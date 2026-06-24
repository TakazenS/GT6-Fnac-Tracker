@echo off
cd /d "%~dp0"
echo ============================================
echo    GTA 6 Tracker - Uninstaller
echo ============================================
echo.
echo This will remove the locally installed components:
echo   - .venv             (Python environment + browser)
echo   - browser_profile   (saved cookies)
echo   - state.json        (already-alerted products)
echo   - __pycache__       (Python cache)
echo   - GTA6-Tracker.zip  (build artifact, if present)
echo.
echo Your settings file (.env) and the scripts are NOT removed by default.
echo.
set /p CONFIRM="Continue? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Cancelled.
    pause
    exit /b 0
)

echo.
echo Removing .venv...
if exist ".venv" rmdir /s /q ".venv"
echo Removing browser_profile...
if exist "browser_profile" rmdir /s /q "browser_profile"
echo Removing __pycache__...
if exist "__pycache__" rmdir /s /q "__pycache__"
echo Removing state.json...
if exist "state.json" del /q "state.json"
echo Removing GTA6-Tracker.zip...
if exist "GTA6-Tracker.zip" del /q "GTA6-Tracker.zip"

echo.
set /p DELENV="Also delete your settings file .env (email/password)? (y/n): "
if /i "%DELENV%"=="y" (
    if exist ".env" del /q ".env"
    echo .env deleted.
) else (
    echo .env kept.
)

echo.
echo ============================================
echo    Uninstall complete.
echo.
echo    Notes:
echo    - The Chromium browser downloaded by Playwright is shared and lives in
echo      %%LOCALAPPDATA%%\ms-playwright . Delete that folder manually if no
echo      other project uses it.
echo    - If you set up a Windows scheduled task, remove it from Task Scheduler.
echo    - To remove everything, you can now delete this whole folder.
echo ============================================
pause
