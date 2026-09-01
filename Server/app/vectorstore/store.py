import logging
from typing import List, Optional
from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import settings
from app.ingestion.pipeline import IngestedDocument
from app.vectorstore.embeddings import get_embeddings

logger = logging.getLogger(__name__)


def get_vectorstore() -> Chroma:
    """Return a Chroma vectorstore instance."""
    embeddings = get_embeddings()
    return Chroma(
        collection_name=settings.CHROMA_COLLECTION,
        embedding_function=embeddings,
        persist_directory=settings.CHROMA_PERSIST_DIR,
    )


def add_ingested_document(ingested_doc: IngestedDocument) -> int:
    """
    Convert an IngestedDocument's chunks into LangChain Documents and index into ChromaDB.

    Returns:
        Number of chunks indexed.
    """
    if not ingested_doc.chunks:
        logger.warning("No chunks found in IngestedDocument: %s", ingested_doc.file_name)
        return 0

    langchain_docs: List[Document] = []

    for chunk in ingested_doc.chunks:
        metadata = {
            "source": ingested_doc.file_path,
            "file_name": ingested_doc.file_name,
            "doc_type": ingested_doc.file_type,
            "chunk_index": chunk.index,
            "start_char": chunk.start_char,
            "end_char": chunk.end_char,
            "page_count": ingested_doc.page_count,
        }
        # Merge any extra metadata
        if chunk.metadata:
            metadata.update(chunk.metadata)

        langchain_docs.append(
            Document(page_content=chunk.text, metadata=metadata)
        )

    vs = get_vectorstore()
    ids = vs.add_documents(langchain_docs)
    logger.info("Indexed %d chunks into Chroma for document: %s", len(ids), ingested_doc.file_name)
    return len(ids)


def delete_document_by_path(file_path: str) -> bool:
    """
    Delete all vector chunks belonging to a specific file_path.
    """
    try:
        vs = get_vectorstore()
        results = vs.get(where={"source": file_path})
        if results and results.get("ids"):
            vs.delete(ids=results["ids"])
            logger.info("Deleted %d vector chunks for file: %s", len(results["ids"]), file_path)
            return True
    except Exception as e:
        logger.error("Failed to delete vectors for file %s: %s", file_path, e)
    return False


def get_vectorstore_stats() -> dict:
    """Return basic collection metrics."""
    try:
        vs = get_vectorstore()
        results = vs.get()
        doc_count = len(results["ids"]) if results and "ids" in results else 0
        return {
            "collection_name": settings.CHROMA_COLLECTION,
            "total_chunks": doc_count,
            "persist_dir": settings.CHROMA_PERSIST_DIR,
        }
    except Exception as e:
        logger.error("Error retrieving vectorstore stats: %s", e)
        return {
            "collection_name": settings.CHROMA_COLLECTION,
            "total_chunks": 0,
            "error": str(e),
        }
