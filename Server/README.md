# Legal AI Multi-Modal Assistant — Server Backend

This is the FastAPI Python backend for the **Legal AI Multi-Modal Assistant**, powered by **Google Gemini** and **Self-Corrective RAG (Self-RAG)** via **LangGraph**.

---

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FastAPI REST API                                 │
│  /api/ingest        /api/query        /api/query/stream     /api/documents  │
└──────┬──────────────────┬───────────────────┬─────────────────────┬─────────┘
       │                  │                   │                     │
┌──────▼──────┐    ┌──────▼─────────────┐   ┌─▼─────────────┐   ┌───▼─────────┐
│ Ingestion   │    │  Self-RAG Engine   │   │ Vector Store  │   │ Database    │
│ Pipeline    │    │   (LangGraph)      │   │  (ChromaDB)   │   │ (SQLite +   │
│ • PDF Parser│    │ • Retrieve         │   │ • Dense Embed │   │ SQLAlchemy) │
│ • Image OCR │    │ • Evaluate Docs    │   │ • Sparse BM25 │   │ • Documents │
│ • Whisper   │    │ • Web Search Fallback │ • Metadata     │   │ • Query Logs│
│ • Splitter  │    │ • Refine & Generate│   │   Filtering   │   │             │
└─────────────┘    └────────────────────┘   └───────────────┘   └─────────────┘
```

### Key Modules:
- `app/ingestion/`: Multi-modal document ingestion pipeline for PDFs (pdfplumber/PyPDF2), scanned images (Tesseract OCR & OpenCV), audio statements (OpenAI Whisper), and Word files (docx).
- `app/rag/`: LangGraph implementation of Self-Corrective RAG (Self-RAG) with retrieval scoring (`CORRECT`, `INCORRECT`, `AMBIGUOUS`), live web search fallback (Tavily), sentence refinement, and final generation.
- `app/llm/`: Gemini LLM client (`ChatGoogleGenerativeAI`).
- `app/vectorstore/`: ChromaDB embeddings management (`models/text-embedding-004` or local HuggingFace BGE) and hybrid search (Dense + BM25).
- `app/models/` & `app/db/`: SQLAlchemy ORM models (`DocumentDB`, `QueryLogDB`) and SQLite database management.
- `app/api/`: REST API endpoints and Server-Sent Events (SSE) streaming.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+
- Tesseract OCR (Optional for scanned image OCR)
- FFmpeg (Optional for audio transcription)

### 2. Environment Setup
Copy `.env.example` to `.env` and fill in your Gemini API key:
```bash
cp .env.example .env
```
Inside `.env`:
```env
GEMINI_API_KEY="your_actual_gemini_api_key"
TAVILY_API_KEY="your_tavily_api_key_optional"
```

### 3. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run the API Server
```bash
uvicorn app.main:app --reload --port 8000
```
- Swagger API Docs: `http://localhost:8000/docs`
- Healthcheck: `http://localhost:8000/api/health`

---

## 📡 API Endpoints Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/query` | Synchronous Self-RAG query execution |
| `GET` | `/api/query/stream` | Server-Sent Events (SSE) real-time streaming answer |
| `POST` | `/api/ingest` | Multipart upload & ingestion of PDF, image, audio, docx, txt |
| `GET` | `/api/documents` | List all ingested documents |
| `DELETE` | `/api/documents/{id}` | Delete document from DB, vector index, and disk |
| `GET` | `/api/health` | Server status and vectorstore metrics |
