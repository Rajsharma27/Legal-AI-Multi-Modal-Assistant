from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class DocumentDB(Base):
    """SQLAlchemy ORM model for storing ingested document metadata."""
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    file_name: Mapped[str] = mapped_column(String, index=True)
    file_path: Mapped[str] = mapped_column(String, unique=True, index=True)
    doc_type: Mapped[str] = mapped_column(String, index=True)  # fir, judgment, image_ocr, audio_transcript, document
    page_count: Mapped[int] = mapped_column(Integer, default=1)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# Pydantic Schemas for API requests & responses
class DocumentBase(BaseModel):
    file_name: str
    file_path: str
    doc_type: str
    page_count: int = 1
    file_size_bytes: int = 0
    chunk_count: int = 0


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
