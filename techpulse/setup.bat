@echo off
title TechPulse AI Voice Agent Setup
echo ===================================================
echo            TECHPULSE AI VOICE AGENT SETUP
echo ===================================================
echo.

:: Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to your PATH.
    echo Please install Python 3.10+ and try again.
    pause
    exit /b %errorlevel%
)

:: 1. Create Virtual Environment
echo [1/4] Creating Python virtual environment (venv)...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b %errorlevel%
)
echo [OK] Virtual environment created successfully.
echo.

:: 2. Activate Virtual Environment & Upgrade pip
echo [2/4] Activating virtual environment and upgrading pip...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
echo.

:: 3. Install requirements
echo [3/4] Installing dependencies from backend\requirements.txt...
pip install -r backend\requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install package dependencies.
    pause
    exit /b %errorlevel%
)
echo [OK] Backend dependencies installed successfully.
echo.

:: 4. Create .env if not exists
echo [4/4] Checking environment configurations...
if not exist .env (
    copy .env.example .env >nul
    echo [OK] Created local .env configuration file from .env.example.
    echo      Please open .env and enter your API keys.
) else (
    echo [NOTE] A local .env file already exists. Skipping template copy.
)
echo.

echo ===================================================
echo               SETUP COMPLETED SUCCESSFULLY
echo ===================================================
echo.
echo NEXT INSTRUCTIONS:
echo 1. Open the created '.env' file and configure:
echo    - ELEVENLABS_API_KEY (Your ElevenLabs API key)
echo    - ELEVENLABS_AGENT_ID (Your ElevenLabs conversational agent ID)
echo    - TWILIO_ACCOUNT_SID (Your Twilio Account SID)
echo    - TWILIO_AUTH_TOKEN (Your Twilio Auth Token)
echo    - TWILIO_PHONE_NUMBER (Your Twilio Phone Number in E.164 format)
echo    - TARGET_PHONE_NUMBER (The recipient's phone number in E.164 format)
echo.
echo 2. Start the FastAPI backend:
echo    python -m uvicorn backend.main:app --reload
echo.
echo 3. Open the dashboard in your browser:
echo    Start double clicking 'frontend/index.html'
echo.
echo 4. (Optional) Run the ElevenLabs MCP server:
echo    pip install elevenlabs-mcp
echo.
echo ===================================================
pause
