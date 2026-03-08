from __future__ import annotations

import logging
from functools import lru_cache
from typing import List, Literal, Optional

from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever, EnsembleRetriever
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import OpenAIEmbeddings
from app.config import settings

logger = logging.getLogger(__name__)

DocType = Literal["fir", "judgment", "image_ocr", "audio_transcript", "document"]


# ---------------------------------------------------------------------------
# Vectorstore singleton
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _get_vectorstore() -> Chroma:
    """Return a cached Chroma vectorstore connection."""
    embeddings = OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        openai_api_key=settings.OPENAI_API_KEY,
    )
    vectorstore = Chroma(
        collection_name=settings.CHROMA_COLLECTION,
        embedding_function=embeddings,
        persist_directory=settings.CHROMA_PERSIST_DIR,
    )
    logger.info("Connected to Chroma collection '%s'", settings.CHROMA_COLLECTION)
    return vectorstore


# ---------------------------------------------------------------------------
# Public retriever factories
# ---------------------------------------------------------------------------

def get_retriever(k: int = 5) -> VectorStoreRetriever:
    """Dense vector retriever — top-k most similar chunks."""
    return _get_vectorstore().as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )


def get_hybrid_retriever(
    documents: Optional[List[Document]] = None,
    k: int = 5,
    dense_weight: float = 0.6,
) -> EnsembleRetriever:
    """Hybrid dense + BM25 retriever.

    Dense retrieval captures semantic similarity; BM25 captures exact legal
    keywords (IPC sections, statute numbers, case citations).

    Args:
        documents:    Pre-loaded documents for the BM25 index. When None, all
                      docs stored in Chroma are fetched automatically.
        k:            Results to return from each sub-retriever.
        dense_weight: Weight for the dense retriever (BM25 = 1 - dense_weight).
    """
    vs = _get_vectorstore()
    dense_retriever = vs.as_retriever(search_kwargs={"k": k})

    if documents is None:
        results = vs.get(include=["documents", "metadatas"])
        documents = [
            Document(page_content=text, metadata=meta)
            for text, meta in zip(results["documents"], results["metadatas"])
        ]

    bm25_retriever = BM25Retriever.from_documents(documents, k=k)

    return EnsembleRetriever(
        retrievers=[dense_retriever, bm25_retriever],
        weights=[dense_weight, round(1.0 - dense_weight, 2)],
    )


def get_filtered_retriever(doc_type: DocType, k: int = 5) -> VectorStoreRetriever:
    """Dense retriever scoped to a specific document type via Chroma metadata filter."""
    return _get_vectorstore().as_retriever(
        search_type="similarity",
        search_kwargs={"k": k, "filter": {"doc_type": doc_type}},
    )


def retrieve_documents(
    query: str,
    k: int = 5,
    doc_type: Optional[DocType] = None,
    use_hybrid: bool = True,
) -> List[Document]:
    """Retrieve documents for a query.

    Args:
        query:       The user question.
        k:           Number of chunks to retrieve.
        doc_type:    Restrict to this document type (uses filtered dense retriever).
        use_hybrid:  Use hybrid retrieval when doc_type is not set.

    Returns:
        List of LangChain Document objects.
    """
    if doc_type:
        retriever = get_filtered_retriever(doc_type=doc_type, k=k)
    elif use_hybrid:
        retriever = get_hybrid_retriever(k=k)
    else:
        retriever = get_retriever(k=k)

    docs = retriever.invoke(query)
    logger.debug("Retrieved %d chunks for query: %.80s", len(docs), query)
    return docs
