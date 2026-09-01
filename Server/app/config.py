import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings tuned specifically for Google Gemini AI."""

    # --- API Keys ---
    GEMINI_API_KEY: str = ""
    TAVILY_API_KEY: str = ""

    # --- Gemini Model Selection ---
    LLM_MODEL: str = "gemini-2.5-flash"
    EMBEDDING_MODEL: str = "models/text-embedding-004"

    # --- Storage & Database Paths ---
    CHROMA_PERSIST_DIR: str = str(BASE_DIR / "data" / "vectorstore")
    CHROMA_COLLECTION: str = "legal_assistant"
    SQLITE_DB_PATH: str = str(BASE_DIR / "data" / "legal_assistant.db")
    UPLOAD_DIR: str = str(BASE_DIR / "data" / "raw")

    # --- Server Config ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

# Ensure directories exist
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(Path(settings.SQLITE_DB_PATH).parent, exist_ok=True)
