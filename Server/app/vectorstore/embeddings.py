import logging
from langchain_core.embeddings import Embeddings
from app.config import settings

logger = logging.getLogger(__name__)


def get_embeddings() -> Embeddings:
    """
    Return Google Gemini Embeddings client (or fallback to local HuggingFace embeddings).
    """
    api_key = settings.GEMINI_API_KEY
    if api_key:
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            logger.info("Using Google Gemini Embeddings (%s)", settings.EMBEDDING_MODEL)
            return GoogleGenerativeAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                google_api_key=api_key,
            )
        except Exception as e:
            logger.warning("Failed to initialize Google Gemini Embeddings: %s. Falling back to local HuggingFace embeddings.", e)

    # Fallback to local HuggingFace sentence-transformers (BGE model)
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings

        logger.info("Using local HuggingFace BGE Embeddings (BAAI/bge-small-en-v1.5)")
        return HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    except Exception as e:
        logger.error("Failed to load local HuggingFace embeddings: %s", e)
        raise RuntimeError("No suitable embedding engine available.") from e
