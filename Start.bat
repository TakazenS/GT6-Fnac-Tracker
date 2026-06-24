@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo The project is not installed yet. Run "Installer.bat" first.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" gta6_tracker.py
pause
