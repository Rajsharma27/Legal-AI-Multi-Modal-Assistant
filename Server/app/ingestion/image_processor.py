import logging
from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np
from PIL import Image

import pytesseract

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}


# ---------- Preprocessing helpers ----------

def load_image(path: Union[str, Path]) -> np.ndarray:
    """Load an image from disk as an OpenCV BGR array."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported format: {path.suffix}")
    img = cv2.imread(str(path))
    if img is None:
        raise ValueError(f"Could not read image: {path}")
    return img


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert BGR image to grayscale."""
    if len(image.shape) == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def denoise(image: np.ndarray, strength: int = 10) -> np.ndarray:
    """Apply non-local means denoising."""
    if len(image.shape) == 2:
        return cv2.fastNlMeansDenoising(image, None, h=strength)
    return cv2.fastNlMeansDenoisingColored(image, None, h=strength)


def binarize(image: np.ndarray) -> np.ndarray:
    """Binarize a grayscale image using Otsu's method."""
    gray = to_grayscale(image)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def resize_for_ocr(image: np.ndarray, scale: float = 2.0) -> np.ndarray:
    """Upscale small images so Tesseract can read them better."""
    h = image.shape[0]
    if h < 1000:
        return cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    return image


def deskew(image: np.ndarray) -> np.ndarray:
    """Straighten a slightly rotated document scan."""
    gray = to_grayscale(image)
    coords = np.column_stack(np.where(gray > 0))
    if len(coords) == 0:
        return image
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    if abs(angle) < 0.5:
        return image
    h, w = image.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def preprocess(image: np.ndarray) -> np.ndarray:
    """Run the standard preprocessing pipeline: grayscale → resize → denoise → binarize."""
    image = to_grayscale(image)
    image = resize_for_ocr(image)
    image = denoise(image)
    image = binarize(image)
    return image


# ---------- OCR ----------

def extract_text(
    image: np.ndarray,
    lang: str = "eng",
    config: str = "--oem 3 --psm 6",
) -> str:
    """Run Tesseract OCR on an image and return the extracted text."""
    pil_img = Image.fromarray(image)
    text = pytesseract.image_to_string(pil_img, lang=lang, config=config)
    return text.strip()


def extract_text_with_confidence(
    image: np.ndarray,
    lang: str = "eng",
    config: str = "--oem 3 --psm 6",
) -> dict:
    """
    Run OCR and return text along with average word-level confidence.

    Returns:
        {"text": str, "confidence": float, "word_count": int}
    """
    pil_img = Image.fromarray(image)
    text = pytesseract.image_to_string(pil_img, lang=lang, config=config).strip()
    data = pytesseract.image_to_data(pil_img, lang=lang, config=config, output_type=pytesseract.Output.DICT)

    confidences = [int(c) for c, w in zip(data["conf"], data["text"]) if int(c) > 0 and w.strip()]
    avg_conf = float(np.mean(confidences)) if confidences else 0.0

    return {
        "text": text,
        "confidence": round(avg_conf, 2),
        "word_count": len(text.split()),
    }


# ---------- High-level convenience ----------

def process_image(path: Union[str, Path], lang: str = "eng") -> dict:
    """
    Load an image, preprocess it, and run OCR.

    Args:
        path: Path to the image file.
        lang: Tesseract language code(s).

    Returns:
        {"file": str, "text": str, "confidence": float, "word_count": int}
    """
    path = Path(path)
    logger.info("Processing image: %s", path.name)
    raw = load_image(path)
    processed = preprocess(raw)
    result = extract_text_with_confidence(processed, lang=lang)
    result["file"] = str(path)
    return result


def process_directory(directory: Union[str, Path], lang: str = "eng", recursive: bool = True) -> list[dict]:
    """
    Process every supported image in a directory.

    Returns:
        List of result dicts from ``process_image``.
    """
    directory = Path(directory)
    pattern = "**/*" if recursive else "*"
    files = sorted(p for p in directory.glob(pattern) if p.suffix.lower() in SUPPORTED_EXTENSIONS)
    logger.info("Found %d images in %s", len(files), directory)
    return [process_image(f, lang=lang) for f in files]
