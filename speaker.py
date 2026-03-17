import asyncio
import logging
import os
import tempfile
import threading

import edge_tts
import pygame

import config

log = logging.getLogger(__name__)
_lock = threading.Lock()


def _ensure_mixer() -> None:
    if not pygame.mixer.get_init():
        pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.mixer.init()


def play_file(path: str) -> None:
    """Play a wav file synchronously."""
    _ensure_mixer()
    with _lock:
        sound = pygame.mixer.Sound(path)
        ch = sound.play()
        while ch and ch.get_busy():
            pygame.time.wait(50)


def speak(text: str) -> None:
    """Convert text to speech via edge-tts and play it synchronously."""
    try:
        asyncio.run(_tts_and_play(text))
    except Exception as e:
        log.error("TTS error: %s", e)


async def _tts_and_play(text: str) -> None:
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp = f.name
    try:
        tts = edge_tts.Communicate(text, config.TTS_VOICE)
        await tts.save(tmp)
        _play_mp3(tmp)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def _play_mp3(path: str) -> None:
    _ensure_mixer()
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.wait(50)


def stop() -> None:
    """Interrupt any currently playing audio."""
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()
        pygame.mixer.stop()
