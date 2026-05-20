@echo off
echo ==============================================
echo Kuvera Pulse - Local Setup and Run Script
echo ==============================================

echo Checking for backend Python virtual environment...
cd backend
IF NOT EXIST "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt
cd ..

echo Starting Backend Server on port 8000...
start cmd /k "cd backend && call venv\Scripts\activate.bat && python mcp_server.py"

echo Starting Frontend Server on port 3000...
start cmd /k "cd frontend && python -m http.server 3000"

echo ==============================================
echo Backend running on http://localhost:8000
echo Frontend running on http://localhost:3000
echo ==============================================

echo Waiting for servers to start...
timeout /t 5 /nobreak > nul

echo Opening browser...
start http://localhost:3000/?backend=http://localhost:8000
