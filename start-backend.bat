@echo off
setlocal
title Sonos Network - Backend
set "ROOT=%~dp0"
cd /d "%ROOT%"

echo ============================================================
echo   Sonos Network Intelligence - Backend Launcher
echo ============================================================
echo.

rem 1. Check or initialize .env file
if not exist "%ROOT%.env" (
    echo [INFO] .env not found. Creating from .env.example ...
    copy "%ROOT%.env.example" "%ROOT%.env" >nul 2>&1
)

rem 2. Check Docker daemon availability
docker info >nul 2>&1
if not errorlevel 1 goto docker_ready

echo [INFO] Docker daemon is not responding.
if not exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" goto docker_manual_start

echo [INFO] Launching Docker Desktop ...
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
echo Waiting up to 60 seconds for Docker daemon to become ready ...
for /l %%I in (1,1,30) do (
    docker info >nul 2>&1
    if not errorlevel 1 goto docker_ready
    timeout /t 2 /nobreak >nul 2>&1
)

:docker_manual_start
echo.
echo [WARNING] Docker daemon is not active.
echo Please ensure Docker Desktop is open and running, then press any key to retry.
pause
docker info >nul 2>&1
if errorlevel 1 goto docker_manual_start

:docker_ready
echo [OK] Docker daemon is active.
echo.

rem 3. Start database and backend services with Docker Compose
echo [STEP 1] Starting database and backend services with Docker Compose...
docker compose up -d sonos-network-db sonos-network-backend
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start Docker Compose services.
    echo Please check Docker logs: docker compose logs
    pause
    exit /b 1
)

rem 4. Wait for backend health endpoint to respond
echo [STEP 2] Waiting for Backend API health check: http://localhost:8001/api/health ...
for /l %%I in (1,1,30) do (
    curl -s -f http://localhost:8001/api/health >nul 2>&1
    if not errorlevel 1 goto backend_online
    timeout /t 2 /nobreak >nul 2>&1
)

:backend_online
echo.
echo ============================================================
echo   Sonos Network Intelligence - Backend is ONLINE!
echo ============================================================
echo   Backend API:   http://localhost:8001
echo   Network API:   http://192.168.55.60:8001 / http://192.168.55.198:8001
echo   Swagger Docs:  http://localhost:8001/docs
echo   Health Status: http://localhost:8001/api/health
echo   Database:      localhost:5434 [PostgreSQL 15]
echo ============================================================
echo.
echo Streaming live backend container logs - Press Ctrl+C to detach:
echo Note: The backend container will continue running in the background.
echo.
docker compose logs -f sonos-network-backend
pause
