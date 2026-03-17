@echo off
setlocal

set TASK_NAME=HeyClaudeVoiceAssistant
set APP_DIR=%~dp0
set PYTHON_EXE=%APP_DIR%venv\Scripts\pythonw.exe
set SCRIPT=%APP_DIR%main.py

echo Registering Hey Claude to start on Windows login...
echo.

if not exist "%PYTHON_EXE%" (
    echo ERROR: Virtual environment not found at %APP_DIR%venv\
    echo Run install.bat first.
    pause
    exit /b 1
)

:: Remove existing task if present
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if not errorlevel 1 (
    schtasks /delete /tn "%TASK_NAME%" /f >nul
    echo [OK] Removed previous task.
)

:: Create scheduled task: run at logon, highest privileges, no window
schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "\"%PYTHON_EXE%\" \"%SCRIPT%\"" ^
    /sc ONLOGON ^
    /rl HIGHEST ^
    /f >nul

if errorlevel 1 (
    echo ERROR: Failed to create scheduled task.
    echo Try running this script as Administrator (right-click -> Run as administrator).
    pause
    exit /b 1
)

echo [OK] Task "%TASK_NAME%" registered.
echo.
echo Hey Claude will now start automatically when you log in to Windows.
echo.
echo To remove from startup:
echo   schtasks /delete /tn "%TASK_NAME%" /f
echo.

set /p START=Start Hey Claude now? (y/n):
if /i "%START%"=="y" (
    start "" "%PYTHON_EXE%" "%SCRIPT%"
    echo [OK] Hey Claude started. Look for the green circle in the system tray.
)

echo.
pause
