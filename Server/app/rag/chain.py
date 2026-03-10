from __future__ import annotations
import logging
import re
from typing import AsyncIterator, List, Optional
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict
from app.config import settings
from app.rag.prompts import (
    ANSWER_PROMPT,
    DOC_EVAL_PROMPT,
    QUERY_REWRITE_PROMPT,
    SENTENCE_FILTER_PROMPT,
)
from app.rag.retriever import DocType, retrieve_documents

logger = logging.getLogger(__name__)

# Score thresholds (same values as the reference notebooks)
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
# State
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
# LLM factory
# ---------------------------------------------------------------------------

def _llm(temperature: float = 0.0) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.LLM_MODEL,
        temperature=temperature,
        openai_api_key=settings.OPENAI_API_KEY,
    )


# ---------------------------------------------------------------------------
# Sentence-level helpers (from notebook 2 / 6)
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

_doc_eval_chain = DOC_EVAL_PROMPT | _llm().with_structured_output(DocEvalScore)


def eval_each_doc_node(state: RAGState) -> RAGState:
    """Score every retrieved chunk; classify retrieval as CORRECT/INCORRECT/AMBIGUOUS.

    Mirrors the exact logic from notebook 3 / 6:
      CORRECT   → at least one chunk scores > UPPER_TH
      INCORRECT → all chunks score  < LOWER_TH
      AMBIGUOUS → anything in between
    """
    q = state["question"]
    scores: List[float] = []
    good: List[Document] = []

    for doc in state["docs"]:
        out: DocEvalScore = _doc_eval_chain.invoke(
            {"question": q, "chunk": doc.page_content}
        )
        logger.debug("[RAG:eval] score=%.2f  reason=%s", out.score, out.reason)
        scores.append(out.score)
        if out.score > LOWER_TH:
            good.append(doc)

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

_rewrite_chain = QUERY_REWRITE_PROMPT | _llm().with_structured_output(WebQuery)


def rewrite_query_node(state: RAGState) -> RAGState:
    """Rewrite the user's legal question into a focused web-search query."""
    out: WebQuery = _rewrite_chain.invoke({"question": state["question"]})
    logger.info("[RAG:rewrite] web_query=%.120s", out.query)
    return {"web_query": out.query}


# --- 4. web_search ----------------------------------------------------------

_tavily = TavilySearchResults(max_results=5, tavily_api_key=settings.TAVILY_API_KEY)


def web_search_node(state: RAGState) -> RAGState:
    """Run Tavily web search using the rewritten query (fallback to original)."""
    q = state.get("web_query") or state["question"]
    logger.info("[RAG:web_search] query=%.80s", q)
    results = _tavily.invoke({"query": q})

    web_docs: List[Document] = []
    for r in results or []:
        title = r.get("title", "")
        url = r.get("url", "")
        content = r.get("content", "") or r.get("snippet", "")
        text = f"TITLE: {title}\nURL: {url}\nCONTENT:\n{content}"
        web_docs.append(
            Document(page_content=text, metadata={"source": url, "doc_type": "web", "title": title})
        )

    logger.info("[RAG:web_search] fetched %d results", len(web_docs))
    return {"web_docs": web_docs}


# --- 5. refine --------------------------------------------------------------

_filter_chain = SENTENCE_FILTER_PROMPT | _llm().with_structured_output(KeepOrDrop)


def refine_node(state: RAGState) -> RAGState:
    """Sentence-level refinement (decompose → LLM filter → recompose).

    Context source depends on verdict (mirrors notebook 6):
      CORRECT   → good_docs only
      INCORRECT → web_docs only
      AMBIGUOUS → good_docs + web_docs  (best of both)
    """
    q = state["question"]
    verdict = state.get("verdict", "CORRECT")

    if verdict == "CORRECT":
        docs_to_use = state.get("good_docs", [])
    elif verdict == "INCORRECT":
        docs_to_use = state.get("web_docs", [])
    else:  # AMBIGUOUS
        docs_to_use = state.get("good_docs", []) + state.get("web_docs", [])

    raw_context = "\n\n".join(d.page_content for d in docs_to_use).strip()
    strips = _decompose_to_sentences(raw_context)

    kept: List[str] = []
    for sentence in strips:
        result: KeepOrDrop = _filter_chain.invoke({"question": q, "sentence": sentence})
        if result.keep:
            kept.append(sentence)

    refined_context = "\n".join(kept).strip()
    logger.info(
        "[RAG:refine] strips=%d  kept=%d  verdict=%s", len(strips), len(kept), verdict
    )
    return {"strips": strips, "kept_strips": kept, "refined_context": refined_context}


# --- 6. generate ------------------------------------------------------------

_answer_chain = ANSWER_PROMPT | _llm(temperature=0.2) | StrOutputParser()


def generate_node(state: RAGState) -> RAGState:
    """Generate the final answer from the refined legal context."""
    logger.info("[RAG:generate] refined_context length=%d", len(state.get("refined_context", "")))
    answer = _answer_chain.invoke(
        {
            "question": state["question"],
            "refined_context": state.get("refined_context", ""),
        }
    )
    return {"answer": answer}


# ---------------------------------------------------------------------------
# Routing  (mirrors notebook 6)
# ---------------------------------------------------------------------------

def _route_after_eval(state: RAGState) -> str:
    """CORRECT → refine directly; INCORRECT / AMBIGUOUS → rewrite → web_search."""
    if state["verdict"] == "CORRECT":
        return "refine"
    return "rewrite_query"


# ---------------------------------------------------------------------------
# Graph builiding
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

    # INCORRECT / AMBIGUOUS path: rewrite → web_search → refine → generate
    g.add_edge("rewrite_query", "web_search")
    g.add_edge("web_search", "refine")

    # Both paths converge at refine → generate → END
    g.add_edge("refine", "generate")
    g.add_edge("generate", END)

    return g.compile()


# Lazy singleton
_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = _build_graph()
    return _graph


# ---------------------------------------------------------------------------
# Output formatter
# ---------------------------------------------------------------------------

def _format_output(state: RAGState) -> dict:
    # Collect unique sources from whichever docs were used
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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run(
    question: str,
    doc_type: Optional[DocType] = None,
    use_hybrid: bool = True,
) -> dict:
    """Run the self-corrective RAG pipeline synchronously.

    Args:
        question:   The user's legal question.
        doc_type:   Restrict retrieval to a specific document type
                    ("fir", "judgment", "image_ocr", "audio_transcript").
        use_hybrid: Use hybrid (dense + BM25) retrieval when doc_type is not set.

    Returns:
        {
            "answer":       str,
            "sources":      list[{"source": str, "doc_type": str}],
            "question":     str,
            "verdict":      "CORRECT" | "INCORRECT" | "AMBIGUOUS",
            "reason":       str,
            "kept_strips":  list[str],
        }
    """
    state = _get_graph().invoke(_initial_state(question, doc_type, use_hybrid))
    return _format_output(state)


async def arun(
    question: str,
    doc_type: Optional[DocType] = None,
    use_hybrid: bool = True,
) -> dict:
    """Async version of :func:`run`."""
    state = await _get_graph().ainvoke(_initial_state(question, doc_type, use_hybrid))
    return _format_output(state)


async def astream(
    question: str,
    doc_type: Optional[DocType] = None,
    use_hybrid: bool = True,
) -> AsyncIterator[str]:
    """Stream answer tokens from the generate node (for Server-Sent Events).

    Yields raw text chunks as they are produced by the LLM.
    """
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
