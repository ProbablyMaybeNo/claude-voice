import logging
import threading
from pathlib import Path
from typing import Optional

import pvporcupine
import pvrecorder

import config

log = logging.getLogger(__name__)

_stop_event = threading.Event()
_resume_event = threading.Event()
_porcupine: Optional[pvporcupine.Porcupine] = None
_recorder: Optional[pvrecorder.PvRecorder] = None
_thread: Optional[threading.Thread] = None


def start(on_wake: threading.Event) -> threading.Thread:
    """Start wake word detection in a daemon thread."""
    global _thread
    _stop_event.clear()
    _resume_event.set()
    _thread = threading.Thread(target=_run, args=(on_wake,), daemon=True, name="wake-word")
    _thread.start()
    return _thread


def stop() -> None:
    """Permanently stop the detection thread and release the mic."""
    _stop_event.set()
    _resume_event.set()  # Unblock _resume_event.wait() if waiting


def resume() -> None:
    """Signal that recording is done — wake word thread can restart the mic."""
    _resume_event.set()


def list_devices() -> list[str]:
    return pvrecorder.PvRecorder.get_available_devices()


def _run(on_wake: threading.Event) -> None:
    global _porcupine, _recorder

    ppn_files = sorted(Path(__file__).parent.glob("*.ppn"))

    try:
        if ppn_files:
            log.info("Loading custom keyword file: %s", ppn_files[0].name)
            _porcupine = pvporcupine.create(
                access_key=config.PICOVOICE_ACCESS_KEY,
                keyword_paths=[str(ppn_files[0])],
            )
        else:
            log.warning(
                "No .ppn keyword file found. Using built-in keyword 'porcupine' as fallback.\n"
                "  To use 'Hey Claude', train a custom wake word at:\n"
                "  https://console.picovoice.ai\n"
                "  Download the .ppn file and place it in the app directory."
            )
            _porcupine = pvporcupine.create(
                access_key=config.PICOVOICE_ACCESS_KEY,
                keywords=["porcupine"],
            )

        _recorder = pvrecorder.PvRecorder(
            frame_length=_porcupine.frame_length,
            device_index=config.MIC_DEVICE_INDEX,
        )
        _recorder.start()
        log.info("Wake word detection active.")

        while not _stop_event.is_set():
            pcm = _recorder.read()
            result = _porcupine.process(pcm)
            if result >= 0:
                log.info("Wake word detected!")
                # Release mic before recording starts
                _recorder.stop()
                on_wake.set()
                # Wait until pipeline signals recording is done
                _resume_event.clear()
                _resume_event.wait()
                if not _stop_event.is_set():
                    _recorder.start()

    except pvporcupine.PorcupineInvalidArgumentError as e:
        log.error("Porcupine config error: %s", e)
    except OSError as e:
        log.error(
            "Microphone not found (device_index=%d): %s\n"
            "Run test_wake_word.py to list available devices and update MIC_DEVICE_INDEX in .env.",
            config.MIC_DEVICE_INDEX, e,
        )
    except Exception as e:
        log.error("Wake word thread error: %s", e)
    finally:
        _cleanup()


def _cleanup() -> None:
    if _recorder is not None:
        try:
            _recorder.stop()
            _recorder.delete()
        except Exception:
            pass
    if _porcupine is not None:
        try:
            _porcupine.delete()
        except Exception:
            pass
