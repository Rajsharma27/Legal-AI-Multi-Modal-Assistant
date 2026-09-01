import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.db.base import Base

logger = logging.getLogger(__name__)

# SQLite connection setup
engine = create_engine(
    f"sqlite:///{settings.SQLITE_DB_PATH}",
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create tables if they don't exist yet."""
    logger.info("Initializing SQLite database at: %s", settings.SQLITE_DB_PATH)
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for obtaining a database session in API routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
