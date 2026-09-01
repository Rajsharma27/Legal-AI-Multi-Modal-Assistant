import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.db.session import init_db
from app.utils.logger import setup_logger

logger = setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events.
    """
    logger.info("Initializing Legal AI Assistant Backend Server...")
    # Initialize database tables
    init_db()
    logger.info("Server initialization complete. Listening on %s:%d", settings.HOST, settings.PORT)
    yield
    logger.info("Shutting down Legal AI Assistant Backend Server.")


app = FastAPI(
    title="Legal AI Multi-Modal Assistant API",
    description="Backend API powering Self-Corrective RAG for Indian Legal Intelligence",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router
app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    return {
        "title": "Legal AI Multi-Modal Assistant API",
        "status": "online",
        "docs_url": "/docs",
        "api_prefix": "/api",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
