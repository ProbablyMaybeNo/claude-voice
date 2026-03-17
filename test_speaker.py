"""Run: python test_speaker.py — tests TTS and chime playback."""
import math
import struct
import sys
import wave

import pygame
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.mixer.init()

import config
import speaker


def generate_chime(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate, freq, duration = 44100, 880, 0.15
    num_samples = int(sample_rate * duration)
    fade = int(sample_rate * 0.02)
    samples = []
    for i in range(num_samples):
        s = math.sin(2 * math.pi * freq * i / sample_rate)
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


print("Checking chime...")
if not config.CHIME_PATH.exists():
    generate_chime(config.CHIME_PATH)
    print(f"  Generated: {config.CHIME_PATH}")
else:
    print(f"  Exists: {config.CHIME_PATH}")

print("Playing chime...")
speaker.play_file(str(config.CHIME_PATH))
print("  Chime played OK")

print("Testing TTS...")
speaker.speak("Hey Claude voice assistant is working. Speech synthesis confirmed.")
print("  TTS OK")

print("\nAll speaker tests passed.")
