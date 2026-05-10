@echo off
REM Quick start script for AutoML Backend (Windows)

echo.
echo ============================================================
echo     AutoML Pipeline Backend - Quick Start Guide
echo ============================================================
echo.

REM Check if .env exists
if not exist .env (
    echo  WARNING: .env file not found. Creating from template...
    copy .env.example .env
    echo  Created .env
    echo.
    echo  IMPORTANT: Edit .env and add your GROQ_API_KEY
    echo  Get it from: https://console.groq.com
    echo.
)

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  ERROR: Python not found. Please install Python 3.9+
    exit /b 1
)

echo  Python found: %python%
python --version

REM Install dependencies
echo.
echo  Installing dependencies...
python -m pip install -q -r requirements.txt

if %errorlevel% neq 0 (
    echo  ERROR: Failed to install dependencies
    exit /b 1
)

echo  Dependencies installed

echo.
echo ============================================================
echo                    Ready to Start!
echo ============================================================
echo.
echo To start the server, run:
echo.
echo     uvicorn main:app --reload
echo.
echo The server will start at: http://localhost:8000
echo.
echo API Documentation (Swagger UI):
echo     http://localhost:8000/docs
echo.
echo Run test suite (in another terminal):
echo     python test_api.py
echo.
echo Full documentation:
echo     type BACKEND_README.md
echo.
