@echo off
setlocal
cd /d %~dp0\..

if not exist .venv\Scripts\python.exe (
  echo [ERROR] Python venv missing. Run scripts\deploy_bot.ps1 first.
  exit /b 1
)

if not exist bot\.bot.env (
  echo [ERROR] bot\.bot.env missing.
  exit /b 1
)

for /f "usebackq tokens=1,* delims== eol=#" %%A in ("bot\.bot.env") do (
  if not "%%A"=="" set "%%A=%%B"
)

call .venv\Scripts\activate.bat
python bot\telegram_bot.py
