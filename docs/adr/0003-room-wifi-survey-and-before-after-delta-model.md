# ADR-0003: Hybrid Continuous Telemetry & Room Survey Before/After Delta Model

- **Status:** Accepted
- **Date:** 2026-10-11

## Context

Two distinct measurement workflows occur in practice:
1. **Continuous Passive Monitoring**: Catching transient RF events (such as a workstation USB-C dock powering on above `Wohnzimmer_Buchregal` and driving `OFDM ANI` to `9`, or an STP Topology Change Notification causing a temporary multi-hop detour).
2. **Active Room-by-Room Walkthrough Surveys**: Walking into a specific room (`Nicolas`, `Noemi`, `Küche`, `Galerie`, etc.) to measure 2.4 GHz and 5 GHz Wi-Fi BSSID strengths (`dBm`) and verify whether a physical change (moving an AP, turning off a rogue transmitter, plugging in Ethernet, switching a speaker to 5 GHz Station Mode) improved the room.

## Decision

1. **24/7 Background Polling Loop**: The backend runs a scheduled 60-second collection cycle across all registered `SONOS_PLAYER` and `WIFI_AP` devices, persisting `SonosTelemetrySnapshot` and client association records in PostgreSQL (with configurable retention pruning for raw 1-minute samples and permanent hourly aggregates).
2. **Seeded Baseline + Multi-Mode `WiFiRoomSurvey` Ingestion**:
   - On initialization, the database seeds all historical September/October 2026 room scans and hardware inventories from the repository's verified documentation.
   - Users can trigger a new `WiFiRoomSurvey` for any `Room` via:
     - **Live Walkthrough Survey Mode** (Web UI on PC or mobile browser, capturing immediate high-frequency Sonos + Omada client + optional LAN Wireless ADB BSSID scan results).
     - **REST Ingestion Endpoint (`POST /api/rooms/{room_id}/surveys`)** designed as the exact contract for the Phase 2 native Android app (`WifiManager.getScanResults()`).
3. **First-Class `SurveyComparisonDelta`**: Every `Room` view can compare any two `WiFiRoomSurvey` / `SonosTelemetrySnapshot` checkpoints (e.g., *Baseline* vs. *Latest*) and automatically compute the delta in `RssiDbm`, `OfdmAniLevel`, `PhyErrorRate`, `StpPathCost`, and `PingRttMs`.

## Consequences

- **Positive**: Eliminates manual NetX screenshot transcription; preserves historical before/after engineering proof per room; provides an immediate path for the Phase 2 Android scanner app.
- **Negative / Trade-offs**: Time-series tables require indexed timestamp partitioning/pruning so the PostgreSQL volume stays compact over months of 24/7 operation.
