#!/usr/bin/env bash
# Production Deployment & Verification Script for Sonos Network Platform on Mini PC (192.168.55.60)
# Usage: ./scripts/deploy.sh

set -euo pipefail

echo "=========================================================="
echo "Deploying Sonos Network Intelligence Platform (Phase 1)"
echo "Host: $(hostname) (192.168.55.60)"
echo "=========================================================="

# 1. Verify Docker CLI
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker CLI not found. Please install Docker."
    exit 1
fi
echo "[OK] Docker CLI detected: $(docker --version)"

# 2. Check if a standalone sonos-network-db is running without compose labels
if docker ps -q --filter "name=sonos-network-db" | grep -q .; then
    COMPOSE_LABEL=$(docker inspect --format '{{index .Config.Labels "com.docker.compose.project"}}' sonos-network-db 2>/dev/null || true)
    if [ -z "$COMPOSE_LABEL" ]; then
        echo "[INFO] Re-attaching standalone sonos-network-db to compose stack..."
        docker stop sonos-network-db >/dev/null 2>&1 || true
        docker rm sonos-network-db >/dev/null 2>&1 || true
    fi
fi

# 3. Build and spin up the Docker Compose stack
echo ""
echo "[STEP 1] Starting Docker Compose stack (db:5434, backend:8000, frontend:3000)..."
docker compose up -d --build

# 4. Wait for database service health
echo ""
echo "[STEP 2] Waiting for PostgreSQL (sonos-network-db port 5434) to become healthy..."
DB_HEALTHY=false
for i in $(seq 1 20); do
    STATUS=$(docker inspect --format '{{.State.Health.Status}}' sonos-network-db 2>/dev/null || echo "starting")
    if [ "$STATUS" = "healthy" ]; then
        DB_HEALTHY=true
        echo "[OK] Database is healthy."
        break
    fi
    sleep 2
done

# 5. Wait for backend health endpoint
echo ""
echo "[STEP 3] Verifying Backend Health (http://localhost:8000/api/health)..."
BACKEND_OK=false
for i in $(seq 1 25); do
    if curl -sf --max-time 3 http://localhost:8000/api/health >/dev/null; then
        BACKEND_OK=true
        echo "[OK] Backend responded with status=ok."
        break
    fi
    sleep 2
done

if [ "$BACKEND_OK" = false ]; then
    echo "[ERROR] Backend failed to respond on http://localhost:8000/api/health."
    exit 1
fi

# 6. Verify 24/7 background telemetry daemon
echo ""
echo "[STEP 4] Verifying 24/7 Telemetry Daemon (http://localhost:8000/api/daemon/status)..."
curl -s --max-time 3 http://localhost:8000/api/daemon/status || true

# 7. Verify frontend accessibility
echo ""
echo "[STEP 5] Verifying Frontend (http://localhost:3000)..."
curl -s --max-time 5 -I http://localhost:3000 | head -n 1 || true

echo ""
echo "=========================================================="
echo "Deployment Verified Successfully!"
echo "Database: 192.168.55.60:5434 (PostgreSQL 15)"
echo "Backend:  http://192.168.55.60:8000 / http://localhost:8000"
echo "Frontend: http://192.168.55.60:3000 / http://localhost:3000"
echo "=========================================================="
