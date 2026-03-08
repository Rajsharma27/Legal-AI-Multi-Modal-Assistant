import logging
import re
from dataclasses import dataclass
from typing import List, Optional, Union

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 1000       # characters per chunk
DEFAULT_CHUNK_OVERLAP = 200     # overlap between consecutive chunks


@dataclass
class TextChunk:
    """A single chunk of text with position metadata."""
    text: str
    index: int              # chunk number (0-based)
    start_char: int         # start offset in the original text
    end_char: int           # end offset in the original text
    metadata: dict = None   

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


# ---------- Low-level splitters ----------

def split_by_characters(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """
    Split text into fixed-size character chunks with overlap.

    Args:
        text: The input text.
        chunk_size: Max characters per chunk.
        chunk_overlap: Number of overlapping characters between chunks.

    Returns:
        List of text chunks.
    """
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - chunk_overlap
    return chunks


def split_by_sentences(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """
    Split text into chunks at sentence boundaries.

    Sentences are detected by common punctuation (. ! ? followed by space or newline).
    Chunks are built by accumulating sentences until the size limit is reached.
    """
    if not text:
        return []

    # Split on sentence-ending punctuation followed by whitespace
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    chunks = []
    current = ""

    for sentence in sentences:
        # If adding this sentence exceeds the limit, save current chunk
        if current and len(current) + len(sentence) + 1 > chunk_size:
            chunks.append(current.strip())
            # Build overlap from the tail of the current chunk
            overlap_text = current[-chunk_overlap:] if chunk_overlap else ""
            current = overlap_text + " " + sentence
        else:
            current = current + " " + sentence if current else sentence

    if current.strip():
        chunks.append(current.strip())

    return chunks


def split_by_paragraphs(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """
    Split text into chunks at paragraph boundaries (double newlines).

    Short paragraphs are merged together; long paragraphs are further
    split by sentences.
    """
    if not text:
        return []

    paragraphs = re.split(r'\n\s*\n', text.strip())

    chunks = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # If a single paragraph exceeds chunk_size, split it by sentences
        if len(para) > chunk_size:
            if current.strip():
                chunks.append(current.strip())
                current = ""
            sub_chunks = split_by_sentences(para, chunk_size, chunk_overlap)
            chunks.extend(sub_chunks)
            continue

        if current and len(current) + len(para) + 2 > chunk_size:
            chunks.append(current.strip())
            overlap_text = current[-chunk_overlap:] if chunk_overlap else ""
            current = overlap_text + "\n\n" + para
        else:
            current = current + "\n\n" + para if current else para

    if current.strip():
        chunks.append(current.strip())

    return chunks


# ---------- Main entry point ----------

def split_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    method: str = "paragraph",
    metadata: Optional[dict] = None,
) -> list[TextChunk]:
    """
    Split text into chunks and return structured TextChunk objects.

    Args:
        text: The full document text.
        chunk_size: Max characters per chunk.
        chunk_overlap: Overlap between consecutive chunks.
        method: Splitting strategy – 'paragraph', 'sentence', or 'character'.
        metadata: Optional dict attached to every chunk (e.g. file name, doc type).

    Returns:
        List of TextChunk objects.
    """
    if not text:
        return []

    if method == "paragraph":
        raw_chunks = split_by_paragraphs(text, chunk_size, chunk_overlap)
    elif method == "sentence":
        raw_chunks = split_by_sentences(text, chunk_size, chunk_overlap)
    elif method == "character":
        raw_chunks = split_by_characters(text, chunk_size, chunk_overlap)
    else:
        raise ValueError(f"Unknown split method: {method}. Use 'paragraph', 'sentence', or 'character'.")

    # Build TextChunk objects with positional info
    chunks = []
    offset = 0
    for i, chunk_text in enumerate(raw_chunks):
        start = text.find(chunk_text[:50], offset)  # approximate start using first 50 chars
        if start == -1:
            start = offset
        end = start + len(chunk_text)

        chunks.append(TextChunk(
            text=chunk_text,
            index=i,
            start_char=start,
            end_char=end,
            metadata=dict(metadata) if metadata else {},
        ))
        offset = max(offset, start + 1)

    logger.info("Split text (%d chars) into %d chunks (method=%s, size=%d, overlap=%d)",
                len(text), len(chunks), method, chunk_size, chunk_overlap)
    return chunks