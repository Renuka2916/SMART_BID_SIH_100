@echo off
echo ===================================================
echo Starting SmartBid Verification Frontend
echo ===================================================
cd /d "%~dp0\frontend"
set PATH=%LOCALAPPDATA%\Programs\nodejs;%PATH%
npm run dev
pause
