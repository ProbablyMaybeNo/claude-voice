import os
from pathlib import Path

from dotenv import load_dotenv

_root = Path(__file__).parent
load_dotenv(_root / ".env")

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
PICOVOICE_ACCESS_KEY: str = os.getenv("PICOVOICE_ACCESS_KEY", "")
WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base.en")
CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
TTS_VOICE: str = os.getenv("TTS_VOICE", "en-US-GuyNeural")
MEMORY_TURNS: int = int(os.getenv("MEMORY_TURNS", "5"))
MIC_DEVICE_INDEX: int = int(os.getenv("MIC_DEVICE_INDEX", "-1"))
INPUT_DEVICE_SAMPLE_RATE: int = int(os.getenv("INPUT_DEVICE_SAMPLE_RATE", "16000"))
SILENCE_THRESHOLD: float = float(os.getenv("SILENCE_THRESHOLD", "500"))
SILENCE_DURATION: float = float(os.getenv("SILENCE_DURATION", "1.5"))
MAX_RECORD_SECONDS: int = int(os.getenv("MAX_RECORD_SECONDS", "30"))

ASSETS_DIR: Path = _root / "assets"
CHIME_PATH: Path = ASSETS_DIR / "chime.wav"


def validate() -> list[str]:
    errors = []
    if not ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY is missing from .env")
    if not PICOVOICE_ACCESS_KEY:
        errors.append("PICOVOICE_ACCESS_KEY is missing from .env")
    return errors
