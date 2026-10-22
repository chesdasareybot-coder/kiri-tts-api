@echo off
title Kiri TTS Khmer Voice Desktop App
cd /d "%~dp0"

echo =======================================================
echo        Starting Kiri TTS Khmer Voice Desktop
echo =======================================================
echo.

:: 1. Clean any old zombie electron processes to avoid cache locks
taskkill /F /IM electron.exe >nul 2>&1

:: 2. Check if local Python backend on port 8000 is running
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8000/health' -TimeoutSec 1 -UseBasicParsing; exit 0 } catch { exit 1 }"
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Starting local Python API server in background...
    start /B python -m uvicorn api:app --host 0.0.0.0 --port 8000 >nul 2>&1
    timeout /t 2 /nobreak >nul
) else (
    echo [INFO] Local Python API server is already running on port 8000.
)

:: 3. Launch Electron Desktop App
cd /d "%~dp0electron-app"
echo [INFO] Launching Desktop Window...
echo.
npm start

