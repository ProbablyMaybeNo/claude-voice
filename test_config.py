"""Run: python test_config.py — verifies .env loads correctly."""
import sys
import config

errors = config.validate()
if errors:
    print("Config errors:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print("Config loaded successfully")
print(f"  CLAUDE_MODEL      = {config.CLAUDE_MODEL}")
print(f"  TTS_VOICE         = {config.TTS_VOICE}")
print(f"  WHISPER_MODEL     = {config.WHISPER_MODEL}")
print(f"  MEMORY_TURNS      = {config.MEMORY_TURNS}")
print(f"  MIC_DEVICE_INDEX  = {config.MIC_DEVICE_INDEX}")
print(f"  SILENCE_THRESHOLD = {config.SILENCE_THRESHOLD}")
print(f"  SILENCE_DURATION  = {config.SILENCE_DURATION}s")
print(f"  MAX_RECORD_SECS   = {config.MAX_RECORD_SECONDS}s")
print(f"  ANTHROPIC_KEY     = {'SET' if config.ANTHROPIC_API_KEY else 'MISSING'}")
print(f"  PICOVOICE_KEY     = {'SET' if config.PICOVOICE_ACCESS_KEY else 'MISSING'}")
print(f"  CHIME_PATH        = {config.CHIME_PATH}")
