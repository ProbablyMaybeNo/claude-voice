@echo off
setlocal EnableDelayedExpansion

echo ============================================
echo  Hey Claude - Voice Assistant Installer
echo ============================================
echo.

:: Find Python
set PYTHON=
where py >nul 2>&1 && set PYTHON=py -3
if not defined PYTHON (
    where python >nul 2>&1 && set PYTHON=python
)
if not defined PYTHON (
    echo ERROR: Python not found. Install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

:: Check version >= 3.10
for /f "tokens=2 delims= " %%v in ('!PYTHON! --version 2^>^&1') do set PYVER=%%v
for /f "tokens=1,2 delims=." %%a in ("!PYVER!") do (
    set MAJOR=%%a
    set MINOR=%%b
)
if !MAJOR! LSS 3 (
    echo ERROR: Python 3.10+ required. Found !PYVER!
    pause & exit /b 1
)
if !MAJOR! EQU 3 if !MINOR! LSS 10 (
    echo ERROR: Python 3.10+ required. Found !PYVER!
    pause & exit /b 1
)
echo [OK] Python !PYVER! found.

:: Create virtual environment
echo.
echo Creating virtual environment...
if exist venv\ (
    echo   venv already exists, skipping.
) else (
    !PYTHON! -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause & exit /b 1
    )
    echo   [OK] venv created.
)

:: Upgrade pip silently
echo.
echo Upgrading pip...
call venv\Scripts\pip.exe install --upgrade pip --quiet

:: Install dependencies
echo.
echo Installing dependencies (this may take several minutes on first run)...
echo   Installing: pvporcupine pvrecorder faster-whisper anthropic edge-tts pygame pystray Pillow python-dotenv
call venv\Scripts\pip.exe install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Dependency installation failed. Check your internet connection and try again.
    pause & exit /b 1
)
echo [OK] All dependencies installed.

:: Set up .env
echo.
if not exist .env (
    copy .env.example .env >nul
    echo [OK] Created .env from template.
    echo.
    echo Opening .env in Notepad — your keys are already filled in.
    echo Review the settings and close Notepad when done.
    notepad .env
) else (
    echo [OK] .env already exists.
)

echo.
echo ============================================
echo  Installation complete!
echo ============================================
echo.
echo Next steps:
echo   1. Verify your .env has valid API keys
echo   2. Run test scripts to verify each component:
echo        venv\Scripts\python.exe test_config.py
echo        venv\Scripts\python.exe test_speaker.py
echo        venv\Scripts\python.exe test_wake_word.py
echo   3. Run start_on_boot.bat to auto-start with Windows
echo   4. Or launch manually: venv\Scripts\pythonw.exe main.py
echo.
echo NOTE: On first run, Whisper will download the speech model (~150MB).
echo       Say 'porcupine' as the wake word until you train a custom one.
echo.
pause
