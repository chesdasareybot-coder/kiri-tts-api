@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
title Kiri TTS Khmer Voice REST API Server (Port 8000)
cd /d "%~dp0"
echo ============================================================
echo   Kiri TTS Khmer Voice REST API Server
echo   API Docs: http://localhost:8000/docs
echo   Health Check: http://localhost:8000/health
echo ============================================================
echo.
python -m uvicorn api:app --host 0.0.0.0 --port 8000
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo API server exited with an error.
    pause
)
