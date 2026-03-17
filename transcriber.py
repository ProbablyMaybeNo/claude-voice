import logging
import os
from datetime import datetime
from typing import Optional

from faster_whisper import WhisperModel

import config

log = logging.getLogger(__name__)
_model: Optional[WhisperModel] = None


def load_model() -> None:
    global _model
    if _model is not None:
        return
    log.info("Loading Whisper model '%s' (may download on first run)...", config.WHISPER_MODEL)
    _model = WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8")
    log.info("Whisper ready.")


def transcribe(wav_path: str) -> Optional[str]:
    """Transcribe wav_path, delete the file, return text or None if inaudible."""
    if _model is None:
        load_model()
    try:
        segments, _ = _model.transcribe(wav_path, beam_size=5, language="en")
        text = " ".join(seg.text.strip() for seg in segments).strip()
        if text:
            log.info("[%s] You said: %s", datetime.now().strftime("%H:%M:%S"), text)
            return text
        log.info("No speech detected in audio.")
        return None
    except Exception as e:
        log.error("Transcription error: %s", e)
        return None
    finally:
        try:
            os.unlink(wav_path)
        except OSError:
            pass
