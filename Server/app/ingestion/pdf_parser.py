import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

import pdfplumber
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)


@dataclass
class PageContent:
    """Text and metadata for a single PDF page."""
    page_number: int
    text: str
    tables: list[list[list[str]]] = field(default_factory=list)
    is_scanned: bool = False
    char_count: int = 0


@dataclass
class PDFDocument:
    """Parsed output of a PDF file."""
    file_path: str
    file_name: str
    page_count: int
    metadata: dict = field(default_factory=dict)
    pages: list[PageContent] = field(default_factory=list)
    full_text: str = ""


# ---------- Metadata ----------

def extract_metadata(path: Union[str, Path]) -> dict:
    """
    Extract PDF-level metadata (title, author, dates, etc.).
    """
    reader = PdfReader(str(path))
    info = reader.metadata or {}
    return {
        "title": getattr(info, "title", None) or "",
        "author": getattr(info, "author", None) or "",
        "subject": getattr(info, "subject", None) or "",
        "creator": getattr(info, "creator", None) or "",
        "producer": getattr(info, "producer", None) or "",
        "creation_date": str(getattr(info, "creation_date", "") or ""),
        "modification_date": str(getattr(info, "modification_date", "") or ""),
        "page_count": len(reader.pages),
    }


# ---------- Page-level extraction ----------

def extract_page_text(page) -> str:
    """Extract text from a single pdfplumber page."""
    text = page.extract_text() or ""
    return text.strip()


def extract_page_tables(page) -> list[list[list[str]]]:
    """Extract tables from a single pdfplumber page."""
    tables = page.extract_tables() or []
    # Clean None values in cells
    cleaned = []
    for table in tables:
        cleaned_table = [
            [cell.strip() if cell else "" for cell in row]
            for row in table
        ]
        cleaned.append(cleaned_table)
    return cleaned


def is_scanned_page(page) -> bool:
    """
    Heuristic: a page is likely scanned if it has very little
    extractable text but contains images.
    """
    text = page.extract_text() or ""
    has_images = len(page.images) > 0 if hasattr(page, "images") else False
    return len(text.strip()) < 20 and has_images


def ocr_scanned_page(page, lang: str = "eng") -> str:
    """
    OCR a scanned page by converting it to an image first.
    Delegates to image_processor for the actual OCR.
    """
    try:
        from app.ingestion.image_processor import preprocess, extract_text
        import numpy as np
        from PIL import Image as PILImage

        pil_image = page.to_image(resolution=300).original
        img_array = np.array(pil_image.convert("RGB"))
        processed = preprocess(img_array)
        return extract_text(processed, lang=lang)
    except Exception as e:
        logger.warning("OCR failed for page: %s", e)
        return ""


# ---------- Main parser ----------

def parse_pdf(
    path: Union[str, Path],
    extract_tables_flag: bool = True,
    ocr_fallback: bool = True,
    ocr_lang: str = "eng",
) -> PDFDocument:
    """
    Parse a PDF file with page-level text, tables, and OCR fallback.

    Args:
        path: Path to the PDF file.
        extract_tables_flag: Whether to extract tables from each page.
        ocr_fallback: Whether to OCR pages that appear scanned.
        ocr_lang: Tesseract language code for OCR.

    Returns:
        A PDFDocument with per-page content and metadata.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    logger.info("Parsing PDF: %s", path.name)

    metadata = extract_metadata(path)
    pages: list[PageContent] = []

    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages):
            page_num = i + 1
            text = extract_page_text(page)
            scanned = is_scanned_page(page)

            # OCR fallback for scanned pages
            if scanned and ocr_fallback:
                logger.info("Page %d appears scanned, running OCR", page_num)
                text = ocr_scanned_page(page, lang=ocr_lang)

            tables = extract_page_tables(page) if extract_tables_flag else []

            pages.append(PageContent(
                page_number=page_num,
                text=text,
                tables=tables,
                is_scanned=scanned,
                char_count=len(text),
            ))

    full_text = "\n\n".join(p.text for p in pages if p.text)

    return PDFDocument(
        file_path=str(path.resolve()),
        file_name=path.name,
        page_count=len(pages),
        metadata=metadata,
        pages=pages,
        full_text=full_text,
    )


def get_page_text(path: Union[str, Path], page_number: int) -> str:
    """
    Get text from a specific page (1-based).
    """
    doc = parse_pdf(path, extract_tables_flag=False, ocr_fallback=True)
    for page in doc.pages:
        if page.page_number == page_number:
            return page.text
    raise ValueError(f"Page {page_number} not found (PDF has {doc.page_count} pages)")


def get_all_tables(path: Union[str, Path]) -> list[dict]:
    """
    Extract all tables from a PDF with their page numbers.

    Returns:
        [{"page": int, "table_index": int, "data": list[list[str]]}, ...]
    """
    doc = parse_pdf(path, extract_tables_flag=True, ocr_fallback=False)
    results = []
    for page in doc.pages:
        for idx, table in enumerate(page.tables):
            results.append({
                "page": page.page_number,
                "table_index": idx,
                "data": table,
            })
    return results