"""
Whisper-based wake word detector.

Listens continuously using pvrecorder, transcribes 1.5-second sliding windows
with faster-whisper (tiny.en), and fires the wake event when "Hey Claude" is detected.

Advantages over Porcupine:
  - No custom .ppn file needed
  - Detects the exact phrase "Hey Claude"
  - Works with any variation ("Hey, Claude", "Hay Claude", etc.)

CPU usage: ~5-10% idle (higher than Porcupine but acceptable for most systems).
"""

import logging
import math
import threading
from typing import Optional

import numpy as np
import pvrecorder
from faster_whisper import WhisperModel

import config

log = logging.getLogger(__name__)

_stop_event = threading.Event()
_resume_event = threading.Event()
_model: Optional[WhisperModel] = None
_thread: Optional[threading.Thread] = None

# Phrase matching — covers common Whisper mishearings of "Hey Claude"
_WAKE_PHRASES = {
    "hey claude",
    "hey cloud",
    "hey claud",
    "hay claude",
    "hey clade",
    "a claude",
}

_SAMPLE_RATE = 16000
_FRAME_LENGTH = 512
_WINDOW_SECONDS = 1.5    # Transcription window length
_STRIDE_FRAMES = 8192    # ~0.5s of new audio per window (50% overlap)
_SPEECH_RMS_THRESHOLD = 200  # Skip transcription if audio is silent


def _load_model() -> WhisperModel:
    global _model
    if _model is None:
        log.info("Loading wake word detection model (tiny.en)...")
        _model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
        log.info("Wake word model ready.")
    return _model


def start(on_wake: threading.Event) -> threading.Thread:
    global _thread
    _stop_event.clear()
    _resume_event.set()
    _thread = threading.Thread(
        target=_run, args=(on_wake,), daemon=True, name="wake-whisper"
    )
    _thread.start()
    return _thread


def stop() -> None:
    _stop_event.set()
    _resume_event.set()


def resume() -> None:
    _resume_event.set()


def _rms(frames: list) -> float:
    if not frames:
        return 0.0
    return math.sqrt(sum(s * s for s in frames) / len(frames))


def _frames_to_float(frames: list) -> np.ndarray:
    return np.array(frames, dtype=np.int16).astype(np.float32) / 32768.0


def _run(on_wake: threading.Event) -> None:
    model = _load_model()
    frames_per_window = int(_SAMPLE_RATE * _WINDOW_SECONDS)

    rec = pvrecorder.PvRecorder(
        frame_length=_FRAME_LENGTH,
        device_index=config.MIC_DEVICE_INDEX,
    )

    ring: list[int] = []

    try:
        rec.start()
        log.info("Whisper wake word detection active. Say 'Hey Claude' to activate.")

        while not _stop_event.is_set():
            # Read one frame into the ring buffer
            frame = rec.read()
            ring.extend(frame)

            # Only process once we have a full window
            if len(ring) < frames_per_window:
                continue

            # Trim ring to window size
            window = ring[-frames_per_window:]

            # Skip silent windows (saves CPU significantly)
            if _rms(window) < _SPEECH_RMS_THRESHOLD:
                # Slide forward
                ring = ring[_STRIDE_FRAMES:]
                continue

            # Transcribe the window
            try:
                audio = _frames_to_float(window)
                segments, _ = model.transcribe(
                    audio,
                    beam_size=1,
                    language="en",
                    condition_on_previous_text=False,
                    no_speech_threshold=0.7,
                    log_prob_threshold=-1.0,
                    compression_ratio_threshold=2.4,
                )
                text = " ".join(seg.text.strip().lower() for seg in segments).strip()

                if text:
                    log.debug("Wake window: '%s'", text)

                if any(phrase in text for phrase in _WAKE_PHRASES):
                    log.info("Wake phrase detected: '%s'", text)
                    rec.stop()
                    ring.clear()
                    on_wake.set()
                    _resume_event.clear()
                    _resume_event.wait()
                    if not _stop_event.is_set():
                        rec.start()
                    continue

            except Exception as e:
                log.debug("Transcription window error: %s", e)

            # Slide the ring forward by stride
            ring = ring[_STRIDE_FRAMES:]

    except OSError as e:
        log.error(
            "Microphone not found (device_index=%d): %s",
            config.MIC_DEVICE_INDEX, e,
        )
    except Exception as e:
        log.error("Whisper wake word error: %s", e)
    finally:
        try:
            rec.stop()
            rec.delete()
        except Exception:
            pass
