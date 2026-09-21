@echo off
echo ===================================================
echo Starting SmartBid Verification Backend
echo ===================================================
cd /d "%~dp0"
backend\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --app-dir backend --reload
pause
