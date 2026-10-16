@echo off
cd /d "%~dp0"
if exist "server\.venv\Scripts\python.exe" (
  "server\.venv\Scripts\python.exe" scripts\setup_sms.py
) else (
  python scripts\setup_sms.py
)
pause
