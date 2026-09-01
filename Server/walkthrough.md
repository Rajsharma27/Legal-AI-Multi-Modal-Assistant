# Walkthrough - Legal AI Multi-Modal Assistant (Python Backend)

We have completed **100% of the Python backend codebase** for the **Legal AI Multi-Modal Assistant** powered by **Google Gemini** and **LangGraph Self-Corrective RAG**.

---

## 🛠️ Complete Summary of Backend Codebase

### 1. Ingestion Engine (`app/ingestion/`)
- [pipeline.py](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/app/ingestion/pipeline.py): Multi-modal ingestion router across PDF, image, audio, docx, and txt.
- [pdf_parser.py](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/app/ingestion/pdf_parser.py): `pdfplumber` / `PyPDF2` parser with table extraction & scanned page OCR fallback.
- [image_processor.py](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/app/ingestion/image_processor.py): OpenCV preprocessing (grayscale, Otsu binarization, deskewing) & Tesseract OCR with confidence metrics.
- [audio_processor.py](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/app/ingestion/audio_processor.py): `pydub` audio converter & OpenAI `whisper` speech-to-text transcriber.
- [preprocessor.py](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/app/ingestion/preprocessor.py) & [text_splitter.py](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/app/ingestion/text_splitter.py): Legal text cleaning, IPC section normalization, and position-aware chunking.

### 2. Self-Corrective RAG Engine (`app/rag/`)
- [chain.py](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/app/rag/chain.py): LangGraph Self-RAG state machine (`retrieve` $\rightarrow$ `eval_each_doc` $\rightarrow$ `rewrite_query` $\rightarrow$ `web_search` $\rightarrow$ `refine` $\rightarrow$ `generate`). Supports real-time Server-Sent Events (`astream`).
- [retriever.py](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/app/rag/retriever.py): Hybrid search (Dense vector + Sparse BM25 keyword matching) and metadata filtering.
- [prompts.py](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/app/rag/prompts.py): System prompts for document evaluation, sentence refinement, and legal answer synthesis.

### 3. Google Gemini Integration (`app/llm/` & `app/vectorstore/`)
- [llm/client.py](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/app/llm/client.py): Returns [`ChatGoogleGenerativeAI`](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/app/llm/client.py#L10) using `gemini-2.5-flash`.
- [vectorstore/embeddings.py](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/app/vectorstore/embeddings.py): Returns [`GoogleGenerativeAIEmbeddings`](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/app/vectorstore/embeddings.py#L14) (`models/text-embedding-004`) with local HuggingFace BGE fallback.
- [vectorstore/store.py](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/app/vectorstore/store.py): ChromaDB vector collection management, chunk indexing, and deletion tools.

### 4. Multi-Agent Legal Research (`app/agents/`)
- [agents/tools.py](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/app/agents/tools.py): Custom tools for searching precedents, looking up IPC/CrPC sections, and running Tavily legal web searches.
- [agents/state.py](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/app/agents/state.py) & [agents/graph.py](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/app/agents/graph.py): Multi-agent legal research state graph with tool execution router.

### 5. Database & API Layer (`app/db/`, `app/models/`, `app/api/`, `app/main.py`)
- [db/session.py](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/app/db/session.py): SQLite database engine & session management.
- [models/document.py](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/app/models/document.py) & [models/query_log.py](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/app/models/query_log.py): ORM tables & Pydantic schemas.
- [api/routes.py](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/app/api/routes.py): REST API endpoints (`/api/query`, `/api/query/stream`, `/api/ingest`, `/api/documents`, `/api/health`).
- [main.py](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/app/main.py): FastAPI application entrypoint with CORS middleware and lifespan setup.

### 6. Containerization & Documentation
- [Dockerfile](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/Dockerfile): Production Dockerfile with Tesseract OCR & FFmpeg.
- [docker-compose.yml](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/docker-compose.yml): Multi-container orchestration config.
- [README.md](file:///f:/Legal-AI-Multi-Modal-Assistant/Server/README.md): Documentation covering architecture, API reference, and setup.

---

## ⚡ How to Run

```powershell
# 1. Activate virtualenv & install dependencies
cd Server
.\venv\Scripts\activate
pip install -r requirements.txt

# 2. Add your Gemini API key in Server\.env
GEMINI_API_KEY="your_gemini_api_key_here"

# 3. Launch server
uvicorn app.main:app --reload --port 8000
```
- Interactive Swagger API Documentation: `http://localhost:8000/docs`
- Healthcheck Endpoint: `http://localhost:8000/api/health`
