@echo off
setlocal
title Sonos Network - Frontend
set "ROOT=%~dp0"
cd /d "%ROOT%frontend"

echo ============================================================
echo   Sonos Network Intelligence - Frontend Launcher
echo ============================================================
echo.

rem 1. Check if the frontend is already running inside Docker
set "DOCKER_FRONTEND="
for /f "tokens=*" %%C in ('docker ps -q --filter "name=sonos-network-frontend" --filter "status=running" 2^>nul') do (
    set "DOCKER_FRONTEND=%%C"
)

if defined DOCKER_FRONTEND (
    echo [INFO] Sonos frontend is running in Docker container: %DOCKER_FRONTEND%
    echo [INFO] Opening Web UI in browser: http://localhost:3000
    start http://localhost:3000
    echo.
    echo Streaming Docker frontend logs - Press Ctrl+C to detach:
    docker compose -f "%ROOT%docker-compose.yml" logs -f sonos-network-frontend
    goto end
)

rem 2. Otherwise start local Vite development server
:kill_3000
for /f "tokens=5" %%P in ('netstat -ano 2^>nul ^| findstr ":3000" ^| findstr /L "LISTENING"') do (
    echo Freeing port 3000 [terminating stale PID %%P]...
    taskkill /F /PID %%P /T >nul 2>&1
)
timeout /t 1 /nobreak >nul 2>&1
netstat -ano 2>nul | findstr ":3000" | findstr /L "LISTENING" >nul 2>&1
if not errorlevel 1 goto kill_3000

echo [INFO] Launching Vite Frontend on http://localhost:3000 ...
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:3000"

call npm run dev

:end
pause
