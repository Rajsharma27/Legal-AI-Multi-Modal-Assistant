from __future__ import annotations

import logging
import re
from typing import AsyncIterator, List, Optional
from pydantic import BaseModel
from typing_extensions import TypedDict

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser

from app.config import settings
from app.llm.client import get_llm
from app.rag.prompts import (
    ANSWER_PROMPT,
    DOC_EVAL_PROMPT,
    QUERY_REWRITE_PROMPT,
    SENTENCE_FILTER_PROMPT,
)
from app.rag.retriever import DocType, retrieve_documents
from langgraph.graph import END, START, StateGraph

logger = logging.getLogger(__name__)

# Score thresholds
UPPER_TH = 0.7
LOWER_TH = 0.3


# ---------------------------------------------------------------------------
# Pydantic structured-output schemas
# ---------------------------------------------------------------------------

class DocEvalScore(BaseModel):
    score: float
    reason: str


class KeepOrDrop(BaseModel):
    keep: bool


class WebQuery(BaseModel):
    query: str


# ---------------------------------------------------------------------------
# State Definition
# ---------------------------------------------------------------------------

class RAGState(TypedDict):
    question: str
    doc_type: Optional[str]
    use_hybrid: bool

    # retrieval
    docs: List[Document]
    good_docs: List[Document]
    verdict: str          # "CORRECT" | "INCORRECT" | "AMBIGUOUS"
    reason: str

    # refinement
    strips: List[str]
    kept_strips: List[str]
    refined_context: str

    # web search
    web_query: str
    web_docs: List[Document]

    # output
    answer: str


# ---------------------------------------------------------------------------
# Sentence-level helpers
# ---------------------------------------------------------------------------

def _decompose_to_sentences(text: str) -> List[str]:
    """Split a block of text into individual sentences (min 20 chars)."""
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if len(s.strip()) > 20]


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------

# --- 1. retrieve -----------------------------------------------------------

def retrieve_node(state: RAGState) -> RAGState:
    """Fetch top-k chunks from Chroma (dense or hybrid)."""
    logger.info("[RAG:retrieve] query=%.80s", state["question"])
    docs = retrieve_documents(
        query=state["question"],
        doc_type=state.get("doc_type"),        # type: ignore[arg-type]
        use_hybrid=state.get("use_hybrid", True),
    )
    return {"docs": docs}


# --- 2. eval_each_doc -------------------------------------------------------

def eval_each_doc_node(state: RAGState) -> RAGState:
    """Score every retrieved chunk; classify retrieval as CORRECT/INCORRECT/AMBIGUOUS."""
    q = state["question"]
    docs = state.get("docs", [])

    if not docs:
        logger.info("[RAG:eval] No documents retrieved. Verdict = INCORRECT.")
        return {"good_docs": [], "verdict": "INCORRECT", "reason": "No relevant documents found in knowledge base."}

    scores: List[float] = []
    good: List[Document] = []

    try:
        doc_eval_chain = DOC_EVAL_PROMPT | get_llm().with_structured_output(DocEvalScore)

        for doc in docs:
            out: DocEvalScore = doc_eval_chain.invoke(
                {"question": q, "chunk": doc.page_content}
            )
            logger.debug("[RAG:eval] score=%.2f  reason=%s", out.score, out.reason)
            scores.append(out.score)
            if out.score > LOWER_TH:
                good.append(doc)
    except Exception as e:
        logger.warning("[RAG:eval] Evaluation chain failed (%s). Defaulting to passing all retrieved docs.", e)
        good = docs
        scores = [0.8] * len(docs)

    if any(s > UPPER_TH for s in scores):
        verdict, reason = "CORRECT", f"At least one chunk scored > {UPPER_TH}."
    elif scores and all(s < LOWER_TH for s in scores):
        verdict, reason = "INCORRECT", f"All chunks scored < {LOWER_TH}."
        good = []
    else:
        verdict, reason = "AMBIGUOUS", (
            f"No chunk scored > {UPPER_TH}, but not all were < {LOWER_TH}."
        )

    logger.info("[RAG:eval] verdict=%s  good=%d/%d", verdict, len(good), len(scores))
    return {"good_docs": good, "verdict": verdict, "reason": reason}


# --- 3. rewrite_query -------------------------------------------------------

def rewrite_query_node(state: RAGState) -> RAGState:
    """Rewrite the user's legal question into a focused web-search query."""
    q = state["question"]
    try:
        rewrite_chain = QUERY_REWRITE_PROMPT | get_llm().with_structured_output(WebQuery)
        out: WebQuery = rewrite_chain.invoke({"question": q})
        web_query = out.query
    except Exception as e:
        logger.warning("[RAG:rewrite] Query rewrite failed (%s). Using original question.", e)
        web_query = q

    logger.info("[RAG:rewrite] web_query=%.120s", web_query)
    return {"web_query": web_query}


# --- 4. web_search ----------------------------------------------------------

def web_search_node(state: RAGState) -> RAGState:
    """Run Tavily web search using the rewritten query (fallback to original)."""
    q = state.get("web_query") or state["question"]
    logger.info("[RAG:web_search] query=%.80s", q)
    web_docs: List[Document] = []

    if settings.TAVILY_API_KEY:
        try:
            from langchain_community.tools.tavily_search import TavilySearchResults

            tavily = TavilySearchResults(max_results=5, tavily_api_key=settings.TAVILY_API_KEY)
            results = tavily.invoke({"query": q})

            for r in results or []:
                title = r.get("title", "")
                url = r.get("url", "")
                content = r.get("content", "") or r.get("snippet", "")
                text = f"TITLE: {title}\nURL: {url}\nCONTENT:\n{content}"
                web_docs.append(
                    Document(page_content=text, metadata={"source": url, "doc_type": "web", "title": title})
                )
        except Exception as e:
            logger.warning("[RAG:web_search] Web search failed: %s", e)
    else:
        logger.info("[RAG:web_search] TAVILY_API_KEY not configured. Skipping live web search.")

    logger.info("[RAG:web_search] fetched %d results", len(web_docs))
    return {"web_docs": web_docs}


# --- 5. refine --------------------------------------------------------------

def refine_node(state: RAGState) -> RAGState:
    """Sentence-level refinement (decompose → LLM filter → recompose)."""
    q = state["question"]
    verdict = state.get("verdict", "CORRECT")

    if verdict == "CORRECT":
        docs_to_use = state.get("good_docs", [])
    elif verdict == "INCORRECT":
        docs_to_use = state.get("web_docs", [])
    else:  # AMBIGUOUS
        docs_to_use = state.get("good_docs", []) + state.get("web_docs", [])

    raw_context = "\n\n".join(d.page_content for d in docs_to_use).strip()
    if not raw_context:
        return {"strips": [], "kept_strips": [], "refined_context": ""}

    strips = _decompose_to_sentences(raw_context)
    kept: List[str] = []

    try:
        filter_chain = SENTENCE_FILTER_PROMPT | get_llm().with_structured_output(KeepOrDrop)
        for sentence in strips:
            result: KeepOrDrop = filter_chain.invoke({"question": q, "sentence": sentence})
            if result.keep:
                kept.append(sentence)
    except Exception as e:
        logger.warning("[RAG:refine] Sentence filtering failed (%s). Keeping raw context.", e)
        kept = strips

    refined_context = "\n".join(kept).strip() if kept else raw_context
    logger.info(
        "[RAG:refine] strips=%d  kept=%d  verdict=%s", len(strips), len(kept), verdict
    )
    return {"strips": strips, "kept_strips": kept, "refined_context": refined_context}


# --- 6. generate ------------------------------------------------------------

def generate_node(state: RAGState) -> RAGState:
    """Generate the final answer from the refined legal context."""
    logger.info("[RAG:generate] refined_context length=%d", len(state.get("refined_context", "")))
    try:
        answer_chain = ANSWER_PROMPT | get_llm(temperature=0.2) | StrOutputParser()
        answer = answer_chain.invoke(
            {
                "question": state["question"],
                "refined_context": state.get("refined_context", ""),
            }
        )
    except Exception as e:
        logger.error("[RAG:generate] Generation failed: %s", e)
        answer = f"I could not process your legal query due to a system error: {str(e)}"

    return {"answer": answer}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def _route_after_eval(state: RAGState) -> str:
    """CORRECT → refine directly; INCORRECT / AMBIGUOUS → rewrite → web_search."""
    if state["verdict"] == "CORRECT":
        return "refine"
    return "rewrite_query"


# ---------------------------------------------------------------------------
# Graph building
# ---------------------------------------------------------------------------

def _build_graph():
    g = StateGraph(RAGState)

    g.add_node("retrieve", retrieve_node)
    g.add_node("eval_each_doc", eval_each_doc_node)
    g.add_node("rewrite_query", rewrite_query_node)
    g.add_node("web_search", web_search_node)
    g.add_node("refine", refine_node)
    g.add_node("generate", generate_node)

    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "eval_each_doc")

    g.add_conditional_edges(
        "eval_each_doc",
        _route_after_eval,
        {"refine": "refine", "rewrite_query": "rewrite_query"},
    )

    g.add_edge("rewrite_query", "web_search")
    g.add_edge("web_search", "refine")
    g.add_edge("refine", "generate")
    g.add_edge("generate", END)

    return g.compile()


_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = _build_graph()
    return _graph


# ---------------------------------------------------------------------------
# Output Formatter & Public API
# ---------------------------------------------------------------------------

def _format_output(state: RAGState) -> dict:
    all_docs = state.get("good_docs", []) + state.get("web_docs", [])
    seen: set[str] = set()
    sources: List[dict] = []
    for doc in all_docs:
        src = doc.metadata.get("source", "unknown")
        if src not in seen:
            seen.add(src)
            sources.append(
                {"source": src, "doc_type": doc.metadata.get("doc_type", "unknown")}
            )
    return {
        "answer": state.get("answer", ""),
        "sources": sources,
        "question": state.get("question", ""),
        "verdict": state.get("verdict", ""),
        "reason": state.get("reason", ""),
        "kept_strips": state.get("kept_strips", []),
    }


def _initial_state(
    question: str,
    doc_type: Optional[DocType],
    use_hybrid: bool,
) -> RAGState:
    return {
        "question": question,
        "doc_type": doc_type,
        "use_hybrid": use_hybrid,
        "docs": [],
        "good_docs": [],
        "verdict": "",
        "reason": "",
        "strips": [],
        "kept_strips": [],
        "refined_context": "",
        "web_query": "",
        "web_docs": [],
        "answer": "",
    }


def run(
    question: str,
    doc_type: Optional[DocType] = None,
    use_hybrid: bool = True,
) -> dict:
    """Run the self-corrective RAG pipeline synchronously."""
    state = _get_graph().invoke(_initial_state(question, doc_type, use_hybrid))
    return _format_output(state)


async def arun(
    question: str,
    doc_type: Optional[DocType] = None,
    use_hybrid: bool = True,
) -> dict:
    """Async version of run."""
    state = await _get_graph().ainvoke(_initial_state(question, doc_type, use_hybrid))
    return _format_output(state)


async def astream(
    question: str,
    doc_type: Optional[DocType] = None,
    use_hybrid: bool = True,
) -> AsyncIterator[str]:
    """Stream answer tokens from the generate node."""
    async for event in _get_graph().astream_events(
        _initial_state(question, doc_type, use_hybrid),
        version="v2",
    ):
        if (
            event["event"] == "on_chat_model_stream"
            and event.get("metadata", {}).get("langgraph_node") == "generate"
        ):
            chunk = event["data"]["chunk"]
            if hasattr(chunk, "content") and chunk.content:
                yield chunk.content
