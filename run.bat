@echo off
rem Windows: double-click to set up (first run) and run the bot, restarting it if it crashes.
cd /d "%~dp0"
if not exist .venv (
  py -3 -m venv .venv || (echo Install Python 3.10+ from python.org first, tick "Add to PATH". & pause & exit /b 1)
  .venv\Scripts\pip install -r requirements.txt
)
if not exist .env (
  copy .env.example .env >nul
  echo Opening .env - paste your bot token after TELEGRAM_BOT_TOKEN=, save, close, then press a key.
  notepad .env
  pause
)
:loop
.venv\Scripts\python bot.py
echo Bot stopped, restarting in 10 seconds (close this window to quit)...
timeout /t 10 >nul
goto loop
