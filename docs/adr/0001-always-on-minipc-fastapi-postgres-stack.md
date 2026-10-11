# ADR-0001: Always-On Mini PC Runtime with FastAPI, Isolated Docker PostgreSQL, and React Flow Frontend

- **Status:** Accepted
- **Date:** 2026-10-11

## Context

 diagnosing and monitoring the 14-player Sonos system (`192.168.10.0/24`, VLAN 10) and Omada Wi-Fi infrastructure (`192.168.55.0/24`, VLAN 1) previously relied on ad-hoc CLI scripts (`tools/sonos_monitor.py`, `scripts/reset_sonos_groups.py`) executed manually from a desktop PC (`192.168.55.198`) and manual Markdown transcriptions of mobile NetX screenshots.

When the desktop PC is off or asleep, no telemetry is collected, intermittent RF interference spikes (`OFDM ANI`, `PHY error/s`) go unrecorded, and the Omada Software Controller (`:8043`) is offline. Furthermore, we need:
1. A persistent database to store room-by-room Wi-Fi surveys, historical Sonos telemetry, and dynamic room/device definitions.
2. An interactive graphical UI on the desktop computer and browser.
3. A clean HTTP/WebSocket contract so a native Android app can connect over the LAN in Phase 2.

An always-on Windows Mini PC (`WIN-6MT8E13J4OR` at `192.168.55.60`) is available on the `Admin` VLAN with Docker and SSH access already configured.

## Decision

1. **Always-On Host (`192.168.55.60`)**: The production runtime (PostgreSQL database, FastAPI backend + background telemetry daemon, React web frontend, and TP-Link Omada Software Controller) will run 24/7 on the Mini PC (`192.168.55.60`).
2. **Isolated PostgreSQL Container (`Port 5434`)**: Because `192.168.55.60` already hosts `tradingassistant-db` (`postgres:15-alpine`) on port `5433`, this platform will use a dedicated `sonos-network-db` (`postgres:15-alpine`) container mapped to port `5434` with its own isolated volume (`sonos_pgdata`).
3. **Backend Stack**: Python 3.11+ with **FastAPI**, **SQLAlchemy 2.0 (async) / Alembic**, and **Pydantic v2**, exposing REST and WebSocket endpoints on the LAN (`http://192.168.55.60:8000`).
4. **Frontend Stack**: **React 19 + TypeScript + Vite + React Flow** for interactive Wi-Fi and Sonos network topology graphs and floor-by-floor room diagnostics.
5. **Dual-Machine Git Workflow**: The repository is hosted on GitHub (`Netke237/sonos-network`) and cloned on both the Desktop PC (`f:\Git\GitHub\Sonos`) and the Mini PC (`C:\GitHub\sonos-network`).

## Consequences

- **Positive**: 24/7 telemetry collection and Omada management even when the desktop PC is powered off; zero database contention with `trading-assistant`; immediate LAN accessibility from desktop browsers and mobile phones; OpenAPI schema ready for the Phase 2 Android app.
- **Negative / Trade-offs**: Requires managing a Docker Compose stack on the Mini PC (`sonos-network-db`, backend, frontend).
