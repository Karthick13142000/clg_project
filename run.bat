@echo off
REM Set up a virtualenv, install dependencies, and start EduGenie.
setlocal
cd /d "%~dp0"

if not exist .venv (
  echo Creating virtualenv in .venv ...
  python -m venv .venv
)

call .venv\Scripts\activate.bat

echo Installing dependencies ...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

if not exist .env (
  copy .env.example .env >nul
  echo Created .env from .env.example - add your GEMINI_API_KEY there.
)

echo Starting EduGenie on http://127.0.0.1:5000
python app.py
endlocal
