@echo off
setlocal

cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.11+ or add it to PATH.
  pause
  exit /b 1
)

if not exist "client\node_modules\vite\bin\vite.js" (
  echo Installing frontend dependencies...
  cd client
  call npm.cmd install
  if errorlevel 1 (
    echo Frontend dependency installation failed.
    pause
    exit /b 1
  )
  cd ..
)

findstr /b /c:"APP_ENV=production" "server\.env" >nul 2>nul
if not errorlevel 1 (
  where docker >nul 2>nul
  if errorlevel 1 (
    echo ERROR: Production mode requires Docker, but docker.exe is not available in this terminal.
    pause
    exit /b 1
  )
  echo Ensuring the persistent MongoDB container is running...
  docker compose --env-file .env.production -f compose.production.yml up -d mongodb
  if errorlevel 1 (
    echo ERROR: MongoDB could not be started. Open Docker Desktop and try again.
    pause
    exit /b 1
  )
)

echo Starting Sri Sakthi Thirumurugan Finance API on http://127.0.0.1:8000
start "STF API" cmd /k "cd /d %~dp0server && python -m uvicorn main:app --host 127.0.0.1 --port 8000"

echo Waiting for the API to become ready...
set "API_READY="
for /l %%I in (1,1,120) do (
  powershell.exe -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8000/api/health' -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } } catch {}; exit 1" >nul 2>nul
  if not errorlevel 1 (
    set "API_READY=1"
    goto :api_ready
  )
  timeout /t 1 /nobreak >nul
)

echo.
echo ERROR: The API did not become ready within 2 minutes. Check the "STF API" window for the exact error.
echo The web app was not started because login would show Bad Gateway.
pause
exit /b 1

:api_ready
echo API is ready.
echo Starting web app on http://127.0.0.1:5173
start "STF Web" cmd /k "cd /d %~dp0client && npm.cmd run dev -- --host 127.0.0.1 --port 5173"

echo.
echo Open http://127.0.0.1:5173
echo Demo login: owner / owner123
pause
