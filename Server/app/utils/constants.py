"""Legal AI Assistant System Constants."""

# Document Types
DOC_TYPE_FIR = "fir"
DOC_TYPE_JUDGMENT = "judgment"
DOC_TYPE_IMAGE_OCR = "image_ocr"
DOC_TYPE_AUDIO_TRANSCRIPT = "audio_transcript"
DOC_TYPE_DOCUMENT = "document"

SUPPORTED_DOC_TYPES = [
    DOC_TYPE_FIR,
    DOC_TYPE_JUDGMENT,
    DOC_TYPE_IMAGE_OCR,
    DOC_TYPE_AUDIO_TRANSCRIPT,
    DOC_TYPE_DOCUMENT,
]

# File Extension Mappings
ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".doc",
    ".txt",
    ".png",
    ".jpg",
    ".jpeg",
    ".tiff",
    ".tif",
    ".mp3",
    ".wav",
    ".m4a",
    ".flac",
    ".ogg",
}

# RAG Thresholds
DEFAULT_RETRIEVAL_K = 5
UPPER_SCORE_THRESHOLD = 0.7
LOWER_SCORE_THRESHOLD = 0.3
