@echo off
REM ==========================================
REM Kuvera Weekly Pulse - OAuth Setup Script
REM For Windows
REM ==========================================

echo.
echo ============================================================
echo   Kuvera Weekly Pulse - OAuth 2.0 Setup
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python is installed
echo.

REM Check if backend directory exists
if not exist "backend" (
    echo [ERROR] backend directory not found
    echo Please run this script from the project root directory
    pause
    exit /b 1
)

echo [OK] Backend directory found
echo.

REM Navigate to backend
cd backend

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing dependencies...
pip install -q -r requirements.txt
echo [OK] Dependencies installed

echo.
echo ============================================================
echo   Starting Backend Server
echo ============================================================
echo.
echo The server will start on http://localhost:8000
echo.
echo Next steps:
echo   1. Wait for the server to start
echo   2. Open a NEW terminal and run: python test_oauth.py
echo   3. Follow the prompts to complete OAuth authorization
echo.
echo Or manually:
echo   - Visit: http://localhost:8000/oauth/authorize
echo   - Grant permission to your Google account
echo   - Complete the OAuth flow
echo.
echo Press Ctrl+C to stop the server
echo ============================================================
echo.

REM Start the server
python mcp_server.py

pause
