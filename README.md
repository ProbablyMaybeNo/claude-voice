# Hey Claude — Always-On Voice Assistant

A fully local, always-on voice assistant for Windows 11. Say the wake word, ask anything, hear Claude respond.

---

## Prerequisites

- **Windows 11** (Windows 10 also works)
- **Python 3.10+** — [python.org](https://www.python.org/downloads/)
- **Anthropic API key** — [console.anthropic.com](https://console.anthropic.com)
- **Picovoice access key** (free) — [console.picovoice.ai](https://console.picovoice.ai)
- A working microphone (USB or built-in)
- Internet connection (for Claude API and edge-tts; Whisper runs offline)

---

## Setup

### 1. Install dependencies

Double-click **`install.bat`** or run in a terminal:

```
install.bat
```

This will:
- Check your Python version
- Create a virtual environment in `venv/`
- Install all required packages
- Open `.env` in Notepad for review

### 2. Configure `.env`

Your `.env` is pre-filled with your API keys. Review and adjust settings if needed:

```env
ANTHROPIC_API_KEY=your_key        # Claude API
PICOVOICE_ACCESS_KEY=your_key     # Porcupine wake word
WHISPER_MODEL=base.en             # STT model size
TTS_VOICE=en-US-GuyNeural         # Microsoft neural voice
MEMORY_TURNS=5                    # Conversation turns to remember
MIC_DEVICE_INDEX=-1               # -1 = system default mic
SILENCE_THRESHOLD=500             # Lower = more sensitive
SILENCE_DURATION=1.5              # Seconds of silence to stop recording
```

### 3. Register with Windows startup (optional)

```
start_on_boot.bat
```

This adds a Task Scheduler job that launches Hey Claude automatically at login.

### 4. Run

```
venv\Scripts\pythonw.exe main.py
```

Or use the startup task registered above. Hey Claude runs silently — look for the **green circle** in the system tray (bottom-right).

---

## Usage

1. **Say the wake word**: `"porcupine"` (default) or your custom `"Hey Claude"` wake word
2. **Wait for the chime** and the prompt: *"What do you need?"*
3. **Speak your request**
4. **Wait** while it processes (tray turns yellow)
5. **Hear the response** (tray turns blue while speaking)

The assistant remembers the last **5 turns** of conversation across wake cycles.

---

## Getting a Free Picovoice Key

1. Go to [console.picovoice.ai](https://console.picovoice.ai)
2. Create a free account
3. Copy your **Access Key** from the dashboard
4. Paste it into `.env` as `PICOVOICE_ACCESS_KEY`

The free tier allows unlimited usage on a single device.

---

## Training a Custom "Hey Claude" Wake Word

The default setup uses `"porcupine"` as the wake word. To use `"Hey Claude"`:

1. Go to [console.picovoice.ai](https://console.picovoice.ai)
2. Open **Porcupine** → **Train a custom wake word**
3. Enter your phrase: `Hey Claude`
4. Select platform: **Windows**
5. Download the `.ppn` file
6. Place the `.ppn` file in the `claude-voice/` app directory (same folder as `main.py`)
7. Restart Hey Claude — it will auto-detect the `.ppn` file

---

## Changing the TTS Voice

Update `TTS_VOICE` in `.env`. Available edge-tts voices (popular options):

| Voice | Style |
|---|---|
| `en-US-GuyNeural` | Male, neutral (default) |
| `en-US-JennyNeural` | Female, friendly |
| `en-US-AriaNeural` | Female, natural |
| `en-GB-RyanNeural` | British male |
| `en-AU-NatashaNeural` | Australian female |

List all available voices:
```
venv\Scripts\python.exe -c "import asyncio, edge_tts; asyncio.run(edge_tts.list_voices())" | findstr /i "en-"
```

---

## System Tray

Right-click the tray icon for options:

| Option | Action |
|---|---|
| **Pause** | Stop listening (frees mic, icon turns grey) |
| **Resume** | Start listening again |
| **View Last Response** | Show Claude's last reply in a popup |
| **Settings** | Open `.env` in Notepad |
| **Exit** | Shut down completely |

**Icon colors:**
- Green = Listening for wake word
- Yellow = Processing (recording / transcribing / querying)
- Blue = Speaking response
- Grey = Paused
- Red = Error

---

## Test Scripts

Run these individually to verify each component:

```bash
# Verify .env config
venv\Scripts\python.exe test_config.py

# Test TTS and chime playback
venv\Scripts\python.exe test_speaker.py

# List mics + test recording
venv\Scripts\python.exe test_recorder.py

# Test Whisper STT (downloads model on first run)
venv\Scripts\python.exe test_transcriber.py

# Test Claude API connection
venv\Scripts\python.exe test_claude_client.py

# Test wake word detection
venv\Scripts\python.exe test_wake_word.py
```

---

## Troubleshooting

### Mic not detected / wrong mic
```
venv\Scripts\python.exe test_recorder.py
```
Note the `[index]` of your mic, then set in `.env`:
```
MIC_DEVICE_INDEX=1
```

### Wake word not responding
- Confirm Picovoice key is correct in `.env`
- If no `.ppn` file found, the built-in `"porcupine"` keyword is used — say that word
- Check mic is not muted in Windows sound settings
- Try `test_wake_word.py` to confirm detection is working

### Claude not responding / API error
- Check `ANTHROPIC_API_KEY` in `.env`
- Verify internet connection
- Run `test_claude_client.py` to test the connection

### TTS not playing / no audio
- Ensure default audio output is set in Windows sound settings
- Run `test_speaker.py` to test playback directly

### Whisper model download fails
- Requires internet on first run to download the model (~150MB)
- Model is cached at `%USERPROFILE%\.cache\huggingface\` after first download
- To use a larger model for better accuracy: set `WHISPER_MODEL=small.en` in `.env`

### "Hey Claude" window appears briefly
- Use `pythonw.exe` (not `python.exe`) to run without a console window
- The startup task in `start_on_boot.bat` already uses `pythonw.exe`

---

## Uninstall

Remove from Windows startup:
```
schtasks /delete /tn HeyClaudeVoiceAssistant /f
```

Remove the app:
```
rmdir /s /q "C:\path\to\claude-voice"
```

---

## Architecture

```
main.py          — Entry point, tray icon, pipeline orchestration
wake_word.py     — Porcupine wake word detection (daemon thread)
recorder.py      — Voice recording with silence detection
transcriber.py   — faster-whisper local speech-to-text
claude_client.py — Anthropic API + conversation memory
speaker.py       — edge-tts synthesis + pygame playback
config.py        — .env loading and validation
assets/          — chime.wav (auto-generated on first run)
```

**Typical pipeline per wake cycle:**
```
Wake word detected
  → mic released
  → chime plays + "What do you need?"
  → record until silence
  → transcribe with Whisper
  → send to Claude API
  → speak response with edge-tts
  → mic resumes
```
