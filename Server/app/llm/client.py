import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings

logger = logging.getLogger(__name__)


def get_llm(temperature: float = 0.0) -> ChatGoogleGenerativeAI:
    """
    Return a Google Gemini Chat LLM client.
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        logger.warning(
            "GEMINI_API_KEY is not set in environment or .env file! Gemini LLM calls may fail."
        )

    return ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL,
        temperature=temperature,
        google_api_key=api_key or "NO_KEY_PROVIDED",
    )
