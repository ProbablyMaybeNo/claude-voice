#!/usr/bin/env python3
"""Hey Claude — Always-on voice assistant. Run this to start."""

import logging
import math
import os
import struct
import subprocess
import sys
import threading
import wave
from pathlib import Path
from typing import Optional

import pygame
import pystray
from PIL import Image, ImageDraw

import claude_client
import config
import recorder
import speaker
import transcriber
import wake_word

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("main")

_wake_event = threading.Event()
_paused = False
_last_response = ""
_tray: Optional[pystray.Icon] = None

STATUS_COLORS = {
    "Listening": "#00cc44",
    "Processing": "#ffcc00",
    "Speaking": "#3399ff",
    "Paused": "#888888",
    "Error": "#ff3333",
}


# ── Tray icon ──────────────────────────────────────────────────────────────────

def _make_icon(color: str) -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)
    draw.ellipse([4, 4, 60, 60], fill=(r, g, b, 255))
    return img


def _set_status(status: str, tooltip: str = "") -> None:
    if _tray is None:
        return
    color = STATUS_COLORS.get(status, "#888888")
    _tray.icon = _make_icon(color)
    label = f"Hey Claude — {status}"
    if tooltip:
        label += f": {tooltip}"
    _tray.title = label


# ── Tray menu callbacks ────────────────────────────────────────────────────────

def _on_pause(icon, item) -> None:
    global _paused
    _paused = True
    wake_word.stop()
    _set_status("Paused")
    log.info("Paused.")


def _on_resume(icon, item) -> None:
    global _paused
    _paused = False
    _set_status("Listening")
    wake_word.start(_wake_event)
    log.info("Resumed.")


def _on_last_response(icon, item) -> None:
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Last Response", _last_response or "(no response yet)")
    root.destroy()


def _on_settings(icon, item) -> None:
    env_path = Path(__file__).parent / ".env"
    subprocess.Popen(["notepad.exe", str(env_path)])


def _on_exit(icon, item) -> None:
    log.info("Shutting down...")
    wake_word.stop()
    speaker.stop()
    if pygame.mixer.get_init():
        pygame.mixer.quit()
    icon.stop()
    os._exit(0)


def _build_menu() -> pystray.Menu:
    return pystray.Menu(
        pystray.MenuItem("Pause", _on_pause),
        pystray.MenuItem("Resume", _on_resume),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("View Last Response", _on_last_response),
        pystray.MenuItem("Settings", _on_settings),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Exit", _on_exit),
    )


# ── Voice pipeline ─────────────────────────────────────────────────────────────

def _pipeline_thread() -> None:
    global _last_response
    while True:
        _wake_event.wait()
        _wake_event.clear()

        if _paused:
            wake_word.resume()
            continue

        _set_status("Processing")
        try:
            speaker.stop()
            recorder.play_greeting()

            # Try recording up to 2 times before giving up
            text = None
            for attempt in range(2):
                wav_path = recorder.record_until_silence()

                if wav_path is None:
                    if attempt == 0:
                        speaker.speak("Go ahead.")
                        continue
                    else:
                        speaker.speak("Nothing heard. Say Hey Claude to try again.")
                        break

                text = transcriber.transcribe(wav_path)
                if text:
                    break
                if attempt == 0:
                    speaker.speak("Say that again.")

            if not text:
                _set_status("Listening")
                wake_word.resume()
                continue

            reply = claude_client.ask(text)
            _last_response = reply

            _set_status("Speaking")
            speaker.speak(reply)

        except Exception as e:
            log.exception("Pipeline error: %s", e)
            try:
                speaker.speak("Something went wrong. Please try again.")
            except Exception:
                pass
            _set_status("Error", str(e)[:60])
        finally:
            _set_status("Listening")
            wake_word.resume()


# ── Chime generation ───────────────────────────────────────────────────────────

def _generate_chime(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 44100
    freq = 880
    duration = 0.15
    num_samples = int(sample_rate * duration)
    fade = int(sample_rate * 0.02)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        s = math.sin(2 * math.pi * freq * t)
        if i < fade:
            s *= i / fade
        elif i > num_samples - fade:
            s *= (num_samples - i) / fade
        samples.append(int(s * 32767))
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"{len(samples)}h", *samples))
    log.info("Generated chime at %s", path)


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    errors = config.validate()
    if errors:
        for e in errors:
            log.error("Config error: %s", e)
        sys.exit(1)

    if not config.CHIME_PATH.exists():
        _generate_chime(config.CHIME_PATH)

    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.mixer.init()

    log.info("Loading speech recognition model...")
    transcriber.load_model()

    try:
        wake_word.start(_wake_event)
    except Exception as e:
        log.error("Could not start wake word listener: %s", e)
        log.warning("Running in degraded mode — wake word detection disabled.")

    t = threading.Thread(target=_pipeline_thread, daemon=True, name="pipeline")
    t.start()

    global _tray
    _tray = pystray.Icon(
        name="hey-claude",
        icon=_make_icon(STATUS_COLORS["Listening"]),
        title="Hey Claude — Listening",
        menu=_build_menu(),
    )
    log.info(
        "Hey Claude is running. "
        "Say 'porcupine' (or your custom wake word) to activate. "
        "Right-click the tray icon to manage."
    )
    _tray.run()


if __name__ == "__main__":
    main()
