import logging
import re
import unicodedata

logger = logging.getLogger(__name__)


# ---------- Whitespace & basic cleanup ----------

def normalize_whitespace(text: str) -> str:
    """Collapse multiple spaces/tabs into one, and multiple blank lines into two."""
    text = text.replace("\t", " ")
    text = re.sub(r" {2,}", " ", text)              
    text = re.sub(r"\n{3,}", "\n\n", text)           
    return text.strip()


def strip_blank_lines(text: str) -> str:
    """Remove lines that are entirely empty or whitespace."""
    lines = [line for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def fix_line_breaks(text: str) -> str:
    """
    Rejoin lines that were broken mid-sentence by PDF/OCR extraction.
    A line ending without sentence-ending punctuation is joined to the next.
    """
    lines = text.splitlines()
    merged = []
    buffer = ""

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if buffer:
                merged.append(buffer)
                buffer = ""
            merged.append("")
            continue

        if buffer and not re.search(r'[.!?:;)\]"\']\s*$', buffer):
            buffer = buffer + " " + stripped
        else:
            if buffer:
                merged.append(buffer)
            buffer = stripped

    if buffer:
        merged.append(buffer)

    return "\n".join(merged)


# ---------- Unicode normalization ----------

def normalize_unicode(text: str) -> str:
    """Normalize Unicode to NFC form and replace common smart characters."""
    text = unicodedata.normalize("NFC", text)

    replacements = {
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u2013": "-",   # en dash
        "\u2014": "-",   # em dash
        "\u2026": "...", # ellipsis
        "\u00a0": " ",   # non-breaking space
        "\ufeff": "",    # BOM
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def remove_non_printable(text: str) -> str:
    """Remove control characters except newline and tab."""
    return "".join(
        ch for ch in text
        if ch in ("\n", "\t") or not unicodedata.category(ch).startswith("C")
    )


# ---------- OCR artifact cleanup ----------

def fix_ocr_artifacts(text: str) -> str:
    """Fix common OCR misreads and artifacts in legal text."""
    # Remove isolated single characters surrounded by spaces (noise)
    text = re.sub(r'(?<= )[^\w\s](?= )', '', text)

    # Fix common OCR letter substitutions
    fixes = {
        r'\bIl\b': 'II',       # roman numeral II misread
        r'\bl\b(?=[A-Z])': 'I', # lowercase L before uppercase → I
        r'\b0f\b': 'of',
        r'\btbe\b': 'the',
        r'\bwbich\b': 'which',
    }
    for pattern, replacement in fixes.items():
        text = re.sub(pattern, replacement, text)

    return text


# ---------- Legal-document-specific cleanup ----------

def remove_page_numbers(text: str) -> str:
    """Remove standalone page numbers (e.g. '- 5 -', 'Page 12', '12')."""
    # Pattern: line with only a page indicator
    text = re.sub(r'^\s*-?\s*\d{1,4}\s*-?\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*[Pp]age\s+\d{1,4}\s*$', '', text, flags=re.MULTILINE)
    return text


def remove_headers_footers(text: str, min_repeats: int = 3) -> str:
    """
    Remove repeated header/footer lines that appear across pages.
    A line appearing >= min_repeats times is likely a header/footer.
    """
    lines = text.splitlines()
    line_counts: dict[str, int] = {}

    for line in lines:
        stripped = line.strip()
        if stripped:
            line_counts[stripped] = line_counts.get(stripped, 0) + 1

    repeated = {line for line, count in line_counts.items() if count >= min_repeats and len(line) < 100}

    if repeated:
        logger.debug("Removing %d repeated header/footer patterns", len(repeated))

    cleaned = [line for line in lines if line.strip() not in repeated]
    return "\n".join(cleaned)


def normalize_section_numbers(text: str) -> str:
    """Standardize section references like 'Section 302' or 'S. 302' to a consistent format."""
    # S. 302, Sec. 302, sec 302 → Section 302
    text = re.sub(r'\b[Ss](?:ec(?:tion)?)?\.?\s*(\d+)', r'Section \1', text)
    return text


# ---------- Main preprocessing function ----------

def preprocess_text(
    text: str,
    fix_lines: bool = True,
    fix_ocr: bool = True,
    remove_pages: bool = True,
    remove_repeated: bool = True,
    normalize_sections: bool = True,
) -> str:
    """
    Run the full text preprocessing pipeline.

    Args:
        text: Raw extracted text.
        fix_lines: Rejoin broken lines.
        fix_ocr: Fix common OCR artifacts.
        remove_pages: Remove page numbers.
        remove_repeated: Remove repeated headers/footers.
        normalize_sections: Standardize section references.

    Returns:
        Cleaned and normalized text.
    """
    if not text:
        return ""

    text = remove_non_printable(text)
    text = normalize_unicode(text)
    text = normalize_whitespace(text)

    if remove_pages:
        text = remove_page_numbers(text)

    if remove_repeated:
        text = remove_headers_footers(text)

    if fix_lines:
        text = fix_line_breaks(text)

    if fix_ocr:
        text = fix_ocr_artifacts(text)

    if normalize_sections:
        text = normalize_section_numbers(text)

    text = normalize_whitespace(text)  # final pass

    logger.debug("Preprocessed text: %d chars", len(text))
    return text