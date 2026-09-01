import logging
from typing import List, Optional
from langchain_core.tools import tool

from app.config import settings
from app.rag.retriever import retrieve_documents

logger = logging.getLogger(__name__)


@tool
def search_legal_precedents(query: str, doc_type: Optional[str] = None) -> str:
    """
    Search the internal knowledge base for relevant legal precedents, court judgments, FIRs, or statutory documents.

    Args:
        query: The legal query or issue to search for.
        doc_type: Optional filter ('fir', 'judgment', 'image_ocr', 'audio_transcript', 'document').

    Returns:
        String summary of retrieved legal passages.
    """
    logger.info("[Tool:search_legal_precedents] query: %.80s", query)
    try:
        docs = retrieve_documents(query=query, k=5, doc_type=doc_type)  # type: ignore[arg-type]
        if not docs:
            return "No relevant legal precedents or documents found in internal database."

        formatted = []
        for i, doc in enumerate(docs, 1):
            src = doc.metadata.get("source", "Unknown Source")
            dtype = doc.metadata.get("doc_type", "document")
            formatted.append(f"--- Document {i} [{dtype}] ({src}) ---\n{doc.page_content}")

        return "\n\n".join(formatted)
    except Exception as e:
        logger.error("[Tool:search_legal_precedents] Error: %s", e)
        return f"Error searching legal database: {str(e)}"


@tool
def lookup_ipc_section(section_number: str) -> str:
    """
    Lookup information or IPC/CrPC/BNS section definitions.

    Args:
        section_number: Section number (e.g. '302', '420', '161').

    Returns:
        Explanation or retrieved context for that legal section.
    """
    query = f"Section {section_number} Indian Penal Code IPC CrPC BNS punishment definition elements"
    logger.info("[Tool:lookup_ipc_section] section: %s", section_number)
    try:
        docs = retrieve_documents(query=query, k=3)
        if docs:
            return "\n\n".join([d.page_content for d in docs])
        return f"Section {section_number} information requested. Please verify against statutory text."
    except Exception as e:
        return f"Error looking up section {section_number}: {str(e)}"


@tool
def perform_legal_web_search(query: str) -> str:
    """
    Search the web via Tavily for recent Indian Supreme Court / High Court decisions and legal amendments.

    Args:
        query: Web search query formatted with legal terms.

    Returns:
        Web search results snippet.
    """
    logger.info("[Tool:perform_legal_web_search] query: %.80s", query)
    if not settings.TAVILY_API_KEY:
        return "Web search is disabled because TAVILY_API_KEY is not configured."

    try:
        from langchain_community.tools.tavily_search import TavilySearchResults

        tavily = TavilySearchResults(max_results=3, tavily_api_key=settings.TAVILY_API_KEY)
        results = tavily.invoke({"query": query})

        if not results:
            return "No web results found."

        snippets = []
        for r in results:
            snippets.append(f"Title: {r.get('title')}\nURL: {r.get('url')}\nContent: {r.get('content')}")
        return "\n\n".join(snippets)
    except Exception as e:
        return f"Web search failed: {str(e)}"
