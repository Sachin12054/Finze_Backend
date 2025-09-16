@echo off
REM ===================================================
REM Finze Backend Launcher - Windows Compatible
REM Uses Waitress WSGI server (Windows-friendly alternative to Gunicorn)
REM ===================================================

echo.
echo ==========================================
echo    FINZE BACKEND - PRODUCTION SERVER
echo ==========================================
echo.

REM Store current directory and get script directory
set "ORIGINAL_DIR=%CD%"
set "SCRIPT_DIR=%~dp0"

REM Navigate to Backend directory
echo Setting up environment...
cd /d "%SCRIPT_DIR%"

REM Verify directory and files
if not exist "app.py" (
    echo Error: Backend files not found!
    echo Please ensure this script is in the Backend directory.
    pause
    exit /b 1
)

REM Check and activate virtual environment
if not exist "venv\" (
    echo Virtual environment not found. Creating one...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt

REM Install Waitress (Windows-compatible WSGI server)
echo Installing Waitress WSGI server...
pip install waitress

echo.
echo STARTING FINZE BACKEND WITH WAITRESS...
echo ==========================================
echo.
echo Production Server Configuration:
echo    Server: Waitress WSGI (Windows Compatible)
echo    Threads: 4 threads
echo    Timeout: 120 seconds
echo    Binding: 0.0.0.0:8001
echo.
echo Server Endpoints:
echo    - Main Server: http://localhost:8001
echo    - Health Check: http://localhost:8001/api/health
echo.
echo Available Services:
echo    AI Expense Categorization
echo    Receipt Scanning (Gemini AI)
echo    Firebase Firestore Integration
echo    Batch Processing
echo    User Analytics
echo.
echo API Endpoints:
echo    GET  /api/health
echo    GET  /api/categories
echo    POST /api/categorize
echo    POST /api/categorize-batch
echo    POST /api/upload-receipt
echo    POST /api/save-expense
echo    GET  /api/expenses/^<user_id^>
echo    GET  /api/user-summary/^<user_id^>
echo.
echo Press Ctrl+C to stop the server
echo ==========================================
echo.

REM Start with Waitress (Windows-compatible WSGI server)
waitress-serve --host=0.0.0.0 --port=8001 --threads=4 --connection-limit=100 app:app

REM Server has stopped
echo.
echo Backend server stopped.
echo.
echo Session Summary:
echo ==========================================
echo    Server was running at: http://localhost:8001
echo    Check logs above for any errors or warnings
echo.

REM Return to original directory
cd /d "%ORIGINAL_DIR%"

echo Press any key to exit...
pause >nul