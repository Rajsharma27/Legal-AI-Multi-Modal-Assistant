import logging
import os
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.ingestion.pipeline import ingest_file
from app.models.document import DocumentDB, DocumentResponse
from app.models.query_log import QueryLogDB, QueryRequest, QueryResponse
from app.rag.chain import arun, astream, run
from app.vectorstore.store import add_ingested_document, delete_document_by_path, get_vectorstore_stats

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Query Endpoints
# ---------------------------------------------------------------------------

@router.post("/query", response_model=QueryResponse)
async def query_rag_endpoint(
    req: QueryRequest,
    db: Session = Depends(get_db),
):
    """
    Execute Self-Corrective RAG on a legal question.
    """
    logger.info("Received RAG query: %.80s (doc_type=%s)", req.question, req.doc_type)

    try:
        res = await arun(
            question=req.question,
            doc_type=req.doc_type,  # type: ignore[arg-type]
            use_hybrid=req.use_hybrid,
        )

        # Log query to DB
        log_entry = QueryLogDB(
            question=req.question,
            doc_type_filter=req.doc_type,
            verdict=res.get("verdict"),
            answer=res.get("answer", ""),
            reason=res.get("reason"),
        )
        db.add(log_entry)
        db.commit()

        return QueryResponse(
            question=res.get("question", req.question),
            answer=res.get("answer", ""),
            verdict=res.get("verdict"),
            reason=res.get("reason"),
            sources=res.get("sources", []),
            kept_strips=res.get("kept_strips", []),
        )
    except Exception as e:
        logger.error("Error executing RAG query: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution failed: {str(e)}",
        )


@router.get("/query/stream")
async def stream_query_endpoint(
    question: str,
    doc_type: Optional[str] = None,
):
    """
    Server-Sent Events (SSE) streaming endpoint for real-time LLM token response.
    """
    logger.info("Streaming query: %.80s", question)

    async def event_generator():
        try:
            async for token in astream(question=question, doc_type=doc_type):  # type: ignore[arg-type]
                yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error("Streaming error: %s", e)
            yield f"data: Error: {str(e)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Document Ingestion & Management Endpoints
# ---------------------------------------------------------------------------

@router.post("/ingest", response_model=DocumentResponse)
async def ingest_document_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload and ingest a multi-modal legal document (PDF, Image, Audio, DOCX, TXT).
    Processes file, indexes chunks into ChromaDB, and saves metadata to DB.
    """
    file_name = file.filename or "uploaded_file"
    file_ext = Path(file_name).suffix.lower()

    if not file_ext:
        raise HTTPException(status_code=400, detail="File has no extension")

    save_path = Path(settings.UPLOAD_DIR) / file_name
    logger.info("Saving uploaded file to: %s", save_path)

    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error("Failed to save uploaded file: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save uploaded file on server.")

    try:
        # Run multi-modal ingestion pipeline
        ingested_doc = ingest_file(save_path)

        # Index chunks into ChromaDB
        chunk_count = add_ingested_document(ingested_doc)

        # Save record in SQLite
        doc_entry = DocumentDB(
            file_name=ingested_doc.file_name,
            file_path=ingested_doc.file_path,
            doc_type=ingested_doc.file_type,
            page_count=ingested_doc.page_count,
            file_size_bytes=save_path.stat().st_size,
            chunk_count=chunk_count,
        )

        # Update if file already exists in DB
        existing = db.query(DocumentDB).filter(DocumentDB.file_path == ingested_doc.file_path).first()
        if existing:
            db.delete(existing)
            db.commit()

        db.add(doc_entry)
        db.commit()
        db.refresh(doc_entry)

        return doc_entry
    except Exception as e:
        logger.error("Ingestion failed for %s: %s", file_name, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process and ingest document: {str(e)}",
        )


@router.get("/documents", response_model=List[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    """
    List all ingested documents.
    """
    docs = db.query(DocumentDB).order_by(DocumentDB.created_at.desc()).all()
    return docs


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    """
    Delete an ingested document by ID from DB, ChromaDB, and disk.
    """
    doc = db.query(DocumentDB).filter(DocumentDB.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Remove from Chroma
    delete_document_by_path(doc.file_path)

    # Remove from disk if file exists
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception as e:
            logger.warning("Could not delete file from disk (%s): %s", doc.file_path, e)

    # Remove from DB
    db.delete(doc)
    db.commit()

    return {"message": "Document deleted successfully", "id": doc_id}


# ---------------------------------------------------------------------------
# Health & Status
# ---------------------------------------------------------------------------

@router.get("/health")
def health_check():
    """
    System status and vector store collection statistics.
    """
    stats = get_vectorstore_stats()
    return {
        "status": "healthy",
        "llm_model": settings.LLM_MODEL,
        "embedding_model": settings.EMBEDDING_MODEL,
        "vectorstore": stats,
    }
