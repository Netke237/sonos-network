# ADR-0005: Native Android Room Scanner & Topology Companion App

- **Status:** Accepted
- **Date:** 2026-10-13

## Context

Phase 1 established the centralized Always-On Mini PC platform (`FastAPI + PostgreSQL` on `192.168.55.60:8001` / `5434`) and responsive web frontend (`192.168.55.60:3000`). While the web interface provides an interactive dual topology graph and 3-pillar diagnostic drawer, physical room walkthrough surveys remain manual:
1. Web browsers (Chrome, Firefox) on Android cannot invoke 802.11 radio scanning APIs, access raw BSSIDs, extract 802.11 channel frequencies/widths, or query RSSI signal strengths.
2. Previously, gathering room Wi-Fi data required manual NetX Network Tools export, copy-pasting markdown tables, or running Python scripts from a workstation.
3. Conducting walkthroughs in signal dead-zones (e.g. basement, thick reinforced concrete walls) causes network disconnects, breaking real-time HTTP submissions.
4. Kenneth frequently accesses the home network remotely via Firewalla WireGuard VPN (`192.168.55.60:8001`), where server health checks and 1-click UPnP actions are valuable, but physical Wi-Fi room scanning is invalid because the phone is physically off-premise.

## Decision

1. **Stack Selection (Native Kotlin + Jetpack Compose)**:
   - Built as a native Android application in `android/` using Kotlin and Jetpack Compose (Material 3).
   - Direct hardware integration with Android's `WifiManager.startScan()` and `ScanResult` APIs without bridge overhead or cross-platform limitations.
2. **Hybrid Companion Role**:
   - Acts as both a **Field Walkthrough Scanner** (walk room to room, single-tap capture 802.11 BSSID readings, automatically classify APs) and a **Pocket Health Console** (view house health, inspect 3-pillar room diagnostics, execute 1-click UPnP actions).
3. **Single-Shot Probe & Throttling Defense**:
   - Each walkthrough room tap triggers an asynchronous single-shot probe awaiting OS broadcast (with a 10s timeout), allowing up to 4 rooms to be surveyed per 2-minute window within Android 10+ foreground throttling (`WIFI_SCAN_THROTTLE`).
   - Verifies `intent.getBooleanExtra(WifiManager.EXTRA_RESULTS_UPDATED, false)`. If false, aborts and warns the user instead of recording stale cached data. Optional 2-sample probe retained for stationary single-room audits with asymmetric RSSI averaging across detected samples.
   - Accurately captures 802.11 channel widths (20/40/80/160 MHz), center channels, UNII-1/2A/2C/3 channels, and classifies BSSIDs.
4. **Offline Store-and-Forward with Idempotency (Android Room SQLite)**:
   - Room surveys captured while disconnected (e.g. basement leaf walk) are persisted locally in an Android Room SQLite database queue with original `captured_at` timestamps and `client_survey_id` UUIDs.
   - An automatic background synchronization worker checks API connectivity and forwards queued surveys to `POST /api/rooms/{slug}/surveys` upon reconnection. Server deduplicates on `client_survey_id` to guarantee idempotent retries without corrupting history.
   - Dead-zone surveys with zero heard BSSIDs submit `readings: []`, creating a valid dead-zone survey (0 readings, `best_5ghz_dbm = null`, `wifi_health_grade = CRITICAL`) without falling back to server-side scans.
5. **Firewalla WireGuard VPN & Local LAN Dual-Endpoint**:
   - Supports configurable API endpoint switching between Local LAN (`http://192.168.55.60:8001`) and Firewalla VPN (`http://192.168.55.60:8001` / `http://minipc.lan:8001`), using static IP routing to avoid single-label DNS failures over WireGuard.
   - Automatically detects VPN connection status via `ConnectivityManager` network transport flags. When connected remotely over VPN, physical Wi-Fi scanning is safely paused with an informative banner, while all house health metrics, telemetry streams, and 1-click actions remain fully functional.
6. **3-Tab Bottom Navigation**:
   - **📍 Survey Walkthrough**: Floor/room selector, 1-tap capture, live BSSID preview, offline queue indicator.
   - **🏠 House Health**: Floor-by-floor room status badges, 3-pillar breakdown (Wi-Fi, Sonos RF/STP, Wired Switch Ports) fetched from server, dual-view topology toggle.
   - **⚡ Quick Actions & Tools**: 1-click Ghost Group reset (`POST /api/actions/flush-ghost-groups`), live Sonos poll (`POST /api/actions/poll-now`), ICMP ping sweep (`POST /api/actions/ping-sweep`), live EMI velocity oscilloscope via WebSocket `LiveRfFrameDto`.
7. **Dual-View Mobile Topology**:
   - Toggle between **Floor Accordion Cards** (touch-friendly collapsible cards optimized for one-handed vertical phone operation) and **Pinch-to-Zoom Pan Canvas** (vector canvas rendering device nodes and active/blocked STP links).

## Consequences

- **Positive**:
  - Eliminates all manual Wi-Fi data transcription; automated room surveys are ingested into the Mini PC PostgreSQL database in seconds.
  - Offline store-and-forward guarantees zero survey data loss in dead-zones, with pristine timestamp preservation and idempotent retry deduplication.
  - Kenneth has instant 1-click Sonos diagnostic control and house health monitoring from his Android phone anywhere in the house or remotely over VPN.
- **Trade-offs / Limitations**:
  - Requires Android runtime permissions (`ACCESS_FINE_LOCATION`, `ACCESS_WIFI_STATE`, `CHANGE_WIFI_STATE`, and Android 13+ `NEARBY_WIFI_DEVICES`), plus Location Services enabled in system settings.
  - Physical room Wi-Fi scanning is restricted to local on-premise Wi-Fi connectivity.
