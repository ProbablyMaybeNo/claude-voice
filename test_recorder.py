"""Run: python test_recorder.py — lists mic devices and does a test recording."""
import os
import struct
import sys
import tempfile
import time
import wave

import pvrecorder

print("Available microphone devices:")
devices = pvrecorder.PvRecorder.get_available_devices()
for i, name in enumerate(devices):
    print(f"  [{i}] {name}")
print()
print("Tip: Set MIC_DEVICE_INDEX in .env to the index of your preferred mic.")
print("     Use -1 for the system default.\n")

import config

input("Press Enter to record for up to 5 seconds (speak now, then be quiet), or Ctrl+C to skip: ")

rec = pvrecorder.PvRecorder(frame_length=512, device_index=config.MIC_DEVICE_INDEX)
frames = []
rec.start()
print("Recording... (5 seconds)")
start = time.monotonic()
while time.monotonic() - start < 5:
    frames.extend(rec.read())
rec.stop()
rec.delete()

with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
    tmp = f.name

with wave.open(tmp, "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(16000)
    wf.writeframes(struct.pack(f"{len(frames)}h", *frames))

print(f"  Saved: {tmp}  ({len(frames)} samples)")

play = input("Play back the recording? (y/n): ")
if play.lower() == "y":
    import pygame
    pygame.mixer.init()
    pygame.mixer.music.load(tmp)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.05)
    print("  Playback complete")

os.unlink(tmp)
print("\nRecorder test complete.")
