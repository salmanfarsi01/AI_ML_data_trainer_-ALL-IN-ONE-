@echo off
REM AutoML Frontend Setup Script for Windows
REM Run this script to install dependencies and start the development server

echo.
echo ===================================
echo    AutoML Frontend Setup
echo ===================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if errorlevel 1 (
    echo [!] Node.js is not installed.
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo [OK] Node.js version:
node --version

echo [OK] npm version:
npm --version
echo.

REM Check if backend is running
echo [*] Checking backend connection...
timeout /t 1 /nobreak >nul
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing; Write-Host '[OK] Backend is running on http://localhost:8000' -ForegroundColor Green } catch { Write-Host '[WARNING] Backend is not running. Start it first:' -ForegroundColor Yellow; Write-Host '   cd ../automl-backend' -ForegroundColor Yellow; Write-Host '   uvicorn main:app --reload' -ForegroundColor Yellow }"
echo.

echo [*] Installing dependencies...
call npm install

echo.
echo [OK] Setup complete!
echo.
echo [*] Starting development server...
echo [*] Frontend will be available at: http://localhost:3000
echo.

call npm run dev
pause
