import logging
from pathlib import Path
from typing import Union

import whisper
from pydub import AudioSegment

logger = logging.getLogger(__name__)

SUPPORTED_FORMATS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".wma", ".aac", ".webm"}


# ---------- Audio helpers ----------

def load_audio(path: Union[str, Path]) -> Path:
    """
    Validate and return the audio file path.
    Converts unsupported formats to WAV if needed.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")
    if path.suffix.lower() not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported audio format: {path.suffix}")
    return path


def convert_to_wav(path: Union[str, Path]) -> Path:
    """Convert any supported audio format to WAV for consistent processing."""
    path = Path(path)
    if path.suffix.lower() == ".wav":
        return path

    logger.info("Converting %s to WAV", path.name)
    audio = AudioSegment.from_file(str(path))
    wav_path = path.with_suffix(".wav")
    audio.export(str(wav_path), format="wav")
    return wav_path


def get_audio_duration(path: Union[str, Path]) -> float:
    """Return the duration of an audio file in seconds."""
    audio = AudioSegment.from_file(str(path))
    return len(audio) / 1000.0


def split_audio(path: Union[str, Path], chunk_minutes: int = 10) -> list[Path]:
    """
    Split a long audio file into smaller chunks.

    Args:
        path: Path to the audio file.
        chunk_minutes: Length of each chunk in minutes.

    Returns:
        List of paths to the chunk files.
    """
    path = Path(path)
    audio = AudioSegment.from_file(str(path))
    chunk_ms = chunk_minutes * 60 * 1000
    chunks = []

    for i in range(0, len(audio), chunk_ms):
        chunk = audio[i:i + chunk_ms]
        chunk_path = path.parent / f"{path.stem}_chunk{i // chunk_ms:03d}.wav"
        chunk.export(str(chunk_path), format="wav")
        chunks.append(chunk_path)

    logger.info("Split %s into %d chunks", path.name, len(chunks))
    return chunks


# ---------- Transcription ----------

def transcribe(
    path: Union[str, Path],
    model_name: str = "base",
    language: str = "en",
) -> dict:
    """
    Transcribe an audio file using Whisper.

    Args:
        path: Path to the audio file.
        model_name: Whisper model size – 'tiny', 'base', 'small', 'medium', 'large'.
        language: Language code (e.g. 'en', 'hi').

    Returns:
        {"text": str, "language": str, "duration_sec": float, "segments": list}
    """
    path = load_audio(path)
    logger.info("Transcribing %s with model '%s'", path.name, model_name)

    model = whisper.load_model(model_name)
    result = model.transcribe(str(path), language=language)

    duration = get_audio_duration(path)

    return {
        "text": result["text"].strip(),
        "language": result.get("language", language),
        "duration_sec": round(duration, 2),
        "segments": [
            {
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"].strip(),
            }
            for seg in result.get("segments", [])
        ],
    }


def transcribe_long_audio(
    path: Union[str, Path],
    model_name: str = "base",
    language: str = "en",
    chunk_minutes: int = 10,
) -> dict:
    """
    Transcribe a long audio file by splitting it into chunks first.

    Args:
        path: Path to the audio file.
        model_name: Whisper model size.
        language: Language code.
        chunk_minutes: Length of each chunk in minutes.

    Returns:
        {"text": str, "language": str, "duration_sec": float, "chunk_count": int}
    """
    path = load_audio(path)
    duration = get_audio_duration(path)

    # If short enough, transcribe directly
    if duration <= chunk_minutes * 60:
        return transcribe(path, model_name=model_name, language=language)

    chunks = split_audio(path, chunk_minutes=chunk_minutes)
    all_text = []

    for chunk_path in chunks:
        result = transcribe(chunk_path, model_name=model_name, language=language)
        all_text.append(result["text"])

    return {
        "text": " ".join(all_text),
        "language": language,
        "duration_sec": round(duration, 2),
        "chunk_count": len(chunks),
    }


# ---------- High-level convenience ----------

def process_audio(path: Union[str, Path], model_name: str = "base", language: str = "en") -> dict:
    """
    Load an audio file and return its transcription.

    Args:
        path: Path to the audio file.
        model_name: Whisper model size.
        language: Language code.

    Returns:
        {"file": str, "text": str, "language": str, "duration_sec": float}
    """
    path = Path(path)
    logger.info("Processing audio: %s", path.name)
    result = transcribe_long_audio(path, model_name=model_name, language=language)
    result["file"] = str(path)
    return result


def process_directory(
    directory: Union[str, Path],
    model_name: str = "base",
    language: str = "en",
    recursive: bool = True,
) -> list[dict]:
    """
    Transcribe all supported audio files in a directory.

    Returns:
        List of result dicts from ``process_audio``.
    """
    directory = Path(directory)
    pattern = "**/*" if recursive else "*"
    files = sorted(p for p in directory.glob(pattern) if p.suffix.lower() in SUPPORTED_FORMATS)
    logger.info("Found %d audio files in %s", len(files), directory)
    return [process_audio(f, model_name=model_name, language=language) for f in files]