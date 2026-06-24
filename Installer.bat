@echo off
cd /d "%~dp0"
echo ============================================
echo    GTA 6 Tracker - Installation
echo ============================================
echo.
echo [1/3] Creating the Python environment (.venv)...
py -m venv .venv
if errorlevel 1 (
    echo.
    echo [ERROR] Python was not found. Install it from https://www.python.org/downloads/
    echo Remember to tick "Add python.exe to PATH" during installation.
    pause
    exit /b 1
)
echo.
echo [2/3] Installing dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
echo.
echo [3/3] Installing the browser (Chromium)...
".venv\Scripts\python.exe" -m playwright install chromium
echo.
echo ============================================
echo    Installation complete!
echo    Double-click "Start.bat" to begin.
echo ============================================
pause
