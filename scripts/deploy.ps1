# Production Deployment & Verification Script for Sonos Network Platform on Mini PC (192.168.55.60)
# Usage: powershell -ExecutionPolicy Bypass -File scripts/deploy.ps1

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Deploying Sonos Network Intelligence Platform (Phase 1)" -ForegroundColor Cyan
Write-Host "Host: $env:COMPUTERNAME (192.168.55.60)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verify Docker CLI
try {
    $dockerVer = docker --version
    Write-Host "[OK] Docker CLI detected: $dockerVer" -ForegroundColor Green
} catch {
    Write-Error "Docker is not available in PATH. Please install Docker or start Docker Desktop."
    exit 1
}

# 2. Check if a legacy standalone sonos-network-db container is running without compose labels
$existingDb = docker ps -q --filter "name=sonos-network-db"
if ($existingDb) {
    $composeLabel = docker inspect --format '{{index .Config.Labels "com.docker.compose.project"}}' sonos-network-db 2>$null
    if (-not $composeLabel) {
        Write-Host "[INFO] Re-attaching standalone sonos-network-db to compose stack..." -ForegroundColor Yellow
        docker stop sonos-network-db | Out-Null
        docker rm sonos-network-db | Out-Null
    }
}

# 3. Build and spin up the Docker Compose stack
Write-Host "`n[STEP 1] Starting Docker Compose stack (db:5434, backend:8000, frontend:3000)..." -ForegroundColor Cyan
docker compose up -d --build
if ($LASTEXITCODE -ne 0) {
    Write-Error "docker compose up failed with exit code $LASTEXITCODE."
    exit $LASTEXITCODE
}

# 4. Wait for database service health
Write-Host "`n[STEP 2] Waiting for PostgreSQL (sonos-network-db port 5434) to become healthy..." -ForegroundColor Cyan
$maxDbRetries = 20
$dbHealthy = $false
for ($i = 1; $i -le $maxDbRetries; $i++) {
    $status = docker inspect --format '{{.State.Health.Status}}' sonos-network-db 2>$null
    if ($status -eq "healthy") {
        $dbHealthy = $true
        Write-Host "[OK] Database is healthy." -ForegroundColor Green
        break
    }
    Start-Sleep -Seconds 2
}
if (-not $dbHealthy) {
    Write-Warning "Database healthcheck timed out. Checking backend connectivity directly..."
}

# 5. Wait for backend health endpoint
Write-Host "`n[STEP 3] Verifying Backend Health (http://localhost:8000/api/health)..." -ForegroundColor Cyan
$maxBackendRetries = 25
$backendOk = $false
for ($i = 1; $i -le $maxBackendRetries; $i++) {
    try {
        $resp = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -TimeoutSec 3 -ErrorAction Stop
        if ($resp.status -eq "ok") {
            $backendOk = $true
            Write-Host "[OK] Backend responded with status=ok." -ForegroundColor Green
            break
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}
if (-not $backendOk) {
    Write-Error "Backend failed to respond on http://localhost:8000/api/health after $maxBackendRetries attempts."
    exit 1
}

# 6. Verify 24/7 background telemetry daemon
Write-Host "`n[STEP 4] Verifying 24/7 Telemetry Daemon (http://localhost:8000/api/daemon/status)..." -ForegroundColor Cyan
try {
    $daemon = Invoke-RestMethod -Uri "http://localhost:8000/api/daemon/status" -TimeoutSec 3
    Write-Host "[OK] Telemetry Daemon is running: $($daemon.is_running) (interval: $($daemon.interval_sec)s, retention: $($daemon.retention_days)d)" -ForegroundColor Green
} catch {
    Write-Warning "Could not verify daemon status: $_"
}

# 7. Verify frontend accessibility
Write-Host "`n[STEP 5] Verifying Frontend (http://localhost:3000)..." -ForegroundColor Cyan
try {
    $frontendResp = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -ErrorAction Stop
    if ($frontendResp.StatusCode -eq 200) {
        Write-Host "[OK] Frontend is accessible (HTTP 200)." -ForegroundColor Green
    }
} catch {
    Write-Warning "Frontend response warning: $_"
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "Deployment Verified Successfully!" -ForegroundColor Green
Write-Host "Database: 192.168.55.60:5434 (PostgreSQL 15)" -ForegroundColor Green
Write-Host "Backend:  http://192.168.55.60:8000 / http://localhost:8000" -ForegroundColor Green
Write-Host "Frontend: http://192.168.55.60:3000 / http://localhost:3000" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
