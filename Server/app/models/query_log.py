from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel
from sqlalchemy import String, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class QueryLogDB(Base):
    """SQLAlchemy ORM model for auditing user questions and RAG answers."""
    __tablename__ = "query_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    question: Mapped[str] = mapped_column(Text)
    doc_type_filter: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    verdict: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # CORRECT, INCORRECT, AMBIGUOUS
    answer: Mapped[str] = mapped_column(Text)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# Pydantic Schemas for API requests & responses
class QueryRequest(BaseModel):
    question: str
    doc_type: Optional[str] = None
    use_hybrid: bool = True


class SourceInfo(BaseModel):
    source: str
    doc_type: str


class QueryResponse(BaseModel):
    question: str
    answer: str
    verdict: Optional[str] = None
    reason: Optional[str] = None
    sources: List[SourceInfo] = []
    kept_strips: List[str] = []


class QueryLogItem(BaseModel):
    id: int
    question: str
    doc_type_filter: Optional[str] = None
    verdict: Optional[str] = None
    answer: str
    reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
