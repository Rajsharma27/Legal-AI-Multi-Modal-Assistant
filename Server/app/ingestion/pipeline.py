import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from app.ingestion.document_loader import load_document, SUPPORTED_FORMATS as DOC_FORMATS
from app.ingestion.pdf_parser import parse_pdf
from app.ingestion.image_processor import process_image, SUPPORTED_EXTENSIONS as IMG_FORMATS
from app.ingestion.audio_processor import process_audio, SUPPORTED_FORMATS as AUDIO_FORMATS
from app.ingestion.text_splitter import split_text, TextChunk

logger = logging.getLogger(__name__)


# Map every extension to a processing category
def _build_extension_map() -> dict[str, str]:
    ext_map = {}
    for ext in DOC_FORMATS:
        ext_map[ext] = "document"
    for ext in IMG_FORMATS:
        ext_map[ext] = "image"
    for ext in AUDIO_FORMATS:
        ext_map[ext] = "audio"
    # PDF gets its own category for detailed parsing
    ext_map[".pdf"] = "pdf"
    return ext_map


EXTENSION_MAP = _build_extension_map()


@dataclass
class IngestedDocument:
    """Final output of the ingestion pipeline."""
    file_path: str
    file_name: str
    file_type: str              # 'pdf', 'document', 'image', 'audio'
    text: str                   # full extracted text
    chunks: list[TextChunk] = field(default_factory=list)
    page_count: int = 1
    metadata: dict = field(default_factory=dict)
    ingested_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ---------- Pipeline ----------

def ingest_file(
    path: Union[str, Path],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    split_method: str = "paragraph",
    ocr_lang: str = "eng",
    whisper_model: str = "base",
    audio_lang: str = "en",
) -> IngestedDocument:
    """
    Process a single file through the full ingestion pipeline.

    Args:
        path: Path to the input file.
        chunk_size: Max characters per text chunk.
        chunk_overlap: Overlap between chunks.
        split_method: 'paragraph', 'sentence', or 'character'.
        ocr_lang: Tesseract language for image/scanned PDF OCR.
        whisper_model: Whisper model size for audio transcription.
        audio_lang: Language code for audio transcription.

    Returns:
        An IngestedDocument with extracted text and chunks.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower()
    category = EXTENSION_MAP.get(ext)
    if category is None:
        raise ValueError(f"Unsupported file type: {ext}")

    logger.info("Ingesting [%s] %s", category, path.name)

    text = ""
    page_count = 1
    meta: dict = {"source": str(path), "file_type": category}

    # --- Route to the right processor ---

    if category == "pdf":
        doc = parse_pdf(path, ocr_fallback=True, ocr_lang=ocr_lang)
        text = doc.full_text
        page_count = doc.page_count
        meta.update(doc.metadata)

    elif category == "document":
        doc = load_document(path)
        text = doc.text
        page_count = doc.page_count
        meta["file_size_bytes"] = doc.file_size_bytes

    elif category == "image":
        result = process_image(path, lang=ocr_lang)
        text = result.get("text", "")
        meta["confidence"] = result.get("confidence", 0)

    elif category == "audio":
        result = process_audio(path, model_name=whisper_model, language=audio_lang)
        text = result.get("text", "")
        meta["duration_sec"] = result.get("duration_sec", 0)
        meta["language"] = result.get("language", audio_lang)

    # --- Split into chunks ---

    chunks = split_text(
        text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        method=split_method,
        metadata=meta,
    )

    return IngestedDocument(
        file_path=str(path.resolve()),
        file_name=path.name,
        file_type=category,
        text=text,
        chunks=chunks,
        page_count=page_count,
        metadata=meta,
    )


def ingest_directory(
    directory: Union[str, Path],
    recursive: bool = True,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    split_method: str = "paragraph",
) -> list[IngestedDocument]:
    """
    Ingest all supported files in a directory.

    Args:
        directory: Folder to scan.
        recursive: Search subdirectories.
        chunk_size: Max characters per chunk.
        chunk_overlap: Overlap between chunks.
        split_method: Splitting strategy.

    Returns:
        List of IngestedDocument objects.
    """
    directory = Path(directory)
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    pattern = "**/*" if recursive else "*"
    files = sorted(
        p for p in directory.glob(pattern)
        if p.suffix.lower() in EXTENSION_MAP
    )
    logger.info("Found %d files to ingest in %s", len(files), directory)

    results = []
    for f in files:
        try:
            results.append(ingest_file(
                f, chunk_size=chunk_size, chunk_overlap=chunk_overlap, split_method=split_method
            ))
        except Exception as e:
            logger.error("Failed to ingest %s: %s", f.name, e)

    logger.info("Ingested %d / %d files successfully", len(results), len(files))
    return results