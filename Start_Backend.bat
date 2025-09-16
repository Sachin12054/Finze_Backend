@echo off
REM ===================================================
REM Finze Complete Backend Launcher
REM Starts all backend services with full feature support
REM ===================================================

echo.
echo 🚀 ==========================================
echo    FINZE COMPLETE BACKEND LAUNCHER
echo ==========================================
echo.

REM Store current directory and get script directory
set "ORIGINAL_DIR=%CD%"
set "SCRIPT_DIR=%~dp0"

REM Navigate to Backend directory
echo 📂 Setting up environment...
cd /d "%SCRIPT_DIR%"

REM Verify directory and files
if not exist "app.py" (
    echo ❌ Error: Backend files not found!
    echo Please ensure this script is in the Backend directory.
    pause
    exit /b 1
)

REM Check and activate virtual environment
if not exist "venv\" (
    echo ❌ Virtual environment not found. Creating one...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo 📦 Ensuring all dependencies are installed...
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt

REM Install additional required packages for full functionality
echo 📦 Installing additional packages for full functionality...
pip install Pillow python-dotenv



REM Verify environment configuration
echo.
echo 🔍 CONFIGURATION CHECK:
echo ==========================================

if exist ".env" (
    echo ✅ Environment file found
    
    REM Check for API keys
    findstr /C:"GEMINI_API_KEY=AIzaSyA" .env >nul
    if errorlevel 1 (
        echo ⚠️  GEMINI_API_KEY: Not properly configured
    ) else (
        echo ✅ GEMINI_API_KEY: Configured
    )
    
    findstr /C:"GOOGLE_APPLICATION_CREDENTIALS" .env >nul
    if errorlevel 1 (
        echo ⚠️  FIREBASE_CREDENTIALS: Not configured
    ) else (
        echo ✅ FIREBASE_CREDENTIALS: Configured
    )
    
    findstr /C:"MODEL_PATH" .env >nul
    if errorlevel 1 (
        echo ⚠️  MODEL_PATH: Using default
    ) else (
        echo ✅ MODEL_PATH: Configured
    )
) else (
    echo ⚠️  .env file not found - will use defaults
)

REM Check if AI model exists
if exist "models\expense_distilbert\" (
    echo ✅ AI Model: Found
) else (
    echo ⚠️  AI Model: Not found in models\expense_distilbert\
)

REM Check Python dependencies
echo.
echo 🔍 DEPENDENCY CHECK:
echo ==========================================
python -c "
try:
    import flask; print('✅ Flask: Available')
except: print('❌ Flask: Missing')
    
try:
    import flask_cors; print('✅ Flask-CORS: Available')
except: print('❌ Flask-CORS: Missing')
    
try:
    import torch; print('✅ PyTorch: Available')
except: print('❌ PyTorch: Missing')
    
try:
    import transformers; print('✅ Transformers: Available')
except: print('❌ Transformers: Missing')
    
try:
    import requests; print('✅ Requests: Available')
except: print('❌ Requests: Missing')
    
try:
    import PIL; print('✅ Pillow (PIL): Available')
except: print('❌ Pillow (PIL): Missing')
    
try:
    import firebase_admin; print('✅ Firebase Admin: Available')
except: print('❌ Firebase Admin: Missing')
    
try:
    import google.generativeai; print('✅ Google Generative AI: Available')
except: print('❌ Google Generative AI: Missing')
    
try:
    import dotenv; print('✅ Python-dotenv: Available')
except: print('❌ Python-dotenv: Missing')
"

echo.
echo 🚀 STARTING ENHANCED BACKEND...
echo ==========================================
echo.
echo 📍 Server Endpoints:
echo    - Main Server: http://localhost:8001
echo    - Health Check: http://localhost:8001/api/health
echo.
echo 🎯 Available Services:
echo    ✅ AI Expense Categorization
echo    ✅ Receipt Scanning (Gemini AI)
echo    ✅ Firebase Firestore Integration
echo    ✅ Batch Processing
echo    ✅ User Analytics
echo.
echo 📋 API Endpoints:
echo    GET  /api/health
echo    GET  /api/categories
echo    POST /api/categorize
echo    POST /api/categorize-batch
echo    POST /api/upload-receipt
echo    POST /api/save-expense
echo    GET  /api/expenses/^<user_id^>
echo    GET  /api/user-summary/^<user_id^>
echo.
echo 🔄 Press Ctrl+C to stop the server
echo ==========================================
echo.

REM Start the main server
python app.py

REM Server has stopped
echo.
echo 🛑 Backend server stopped.
echo.
echo 📊 Session Summary:
echo ==========================================
echo    Server was running at: http://localhost:8001
echo    Check logs above for any errors or warnings
echo.

REM Return to original directory
cd /d "%ORIGINAL_DIR%"

echo Press any key to exit...
pause >nul