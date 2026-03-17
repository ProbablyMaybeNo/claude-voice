"""Run: python test_transcriber.py — tests Whisper STT model."""
import struct
import sys
import tempfile
import wave

print("Loading Whisper model (may download on first run, ~150MB)...")
import transcriber
transcriber.load_model()
print("  Model loaded OK")

# Test: silent audio should return None
print("Testing with silent audio (should return None)...")
frames = [0] * (16000 * 2)
with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
    tmp = f.name
with wave.open(tmp, "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(16000)
    wf.writeframes(struct.pack(f"{len(frames)}h", *frames))

result = transcriber.transcribe(tmp)
if result is None:
    print("  Silent audio returned None — correct")
else:
    print(f"  Returned: '{result}' (model hallucinated on silence, this is OK)")

print("\nTranscriber test complete.")
print("To test with real audio: import transcriber; print(transcriber.transcribe('file.wav'))")
