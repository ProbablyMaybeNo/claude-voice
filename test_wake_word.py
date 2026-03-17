"""Run: python test_wake_word.py — tests wake word detection."""
import sys
import threading
import time

import pvrecorder

print("Available microphone devices:")
devices = pvrecorder.PvRecorder.get_available_devices()
for i, d in enumerate(devices):
    print(f"  [{i}] {d}")
print()

import config
print(f"Using device index: {config.MIC_DEVICE_INDEX} ({'-1 = system default' if config.MIC_DEVICE_INDEX == -1 else devices[config.MIC_DEVICE_INDEX] if config.MIC_DEVICE_INDEX < len(devices) else 'invalid'})")
print()

wake_event = threading.Event()
print("Starting wake word detection...")
print("Say 'porcupine' (or your custom wake word) to test.")
print("Press Ctrl+C to stop.\n")

import wake_word

try:
    wake_word.start(wake_event)
    count = 0
    while True:
        if wake_event.wait(timeout=0.5):
            count += 1
            print(f"Wake word detected! (#{count})")
            wake_word.resume()
except KeyboardInterrupt:
    print("\nStopping...")
    wake_word.stop()
    print("Done.")
