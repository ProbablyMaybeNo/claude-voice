import logging
import math
import os
import struct
import tempfile
import time
import wave

import pvrecorder

import config
import speaker

log = logging.getLogger(__name__)


def _rms(frame: list) -> float:
    if not frame:
        return 0.0
    return math.sqrt(sum(s * s for s in frame) / len(frame))


def play_greeting() -> None:
    """Play chime + prompt. Call this once before the first record attempt."""
    if config.CHIME_PATH.exists():
        try:
            speaker.play_file(str(config.CHIME_PATH))
        except Exception as e:
            log.warning("Chime playback failed: %s", e)
    speaker.speak("What do you need?")


def record_until_silence() -> str | None:
    """
    Record from mic until silence, return path to wav or None.
    Call play_greeting() before the first attempt.
    A short settle delay is applied so mic doesn't catch TTS reverb.
    """
    time.sleep(0.15)  # Let room echo from TTS settle

    rec = pvrecorder.PvRecorder(
        frame_length=512,
        device_index=config.MIC_DEVICE_INDEX,
    )

    frames: list[int] = []
    silence_start: float | None = None
    started = time.monotonic()

    try:
        rec.start()
        log.info("Recording...")
        while True:
            frame = rec.read()
            frames.extend(frame)

            rms = _rms(frame)
            if rms < config.SILENCE_THRESHOLD:
                if silence_start is None:
                    silence_start = time.monotonic()
                elif time.monotonic() - silence_start >= config.SILENCE_DURATION:
                    log.info("Silence detected — stopping.")
                    break
            else:
                silence_start = None

            if time.monotonic() - started >= config.MAX_RECORD_SECONDS:
                log.info("Max record length reached.")
                break

    except Exception as e:
        log.error("Recorder error: %s", e)
        return None
    finally:
        rec.stop()
        rec.delete()

    if not frames:
        return None

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp = f.name

    with wave.open(tmp, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(config.INPUT_DEVICE_SAMPLE_RATE)
        wf.writeframes(struct.pack(f"{len(frames)}h", *frames))

    return tmp
