# ADR-0005: Native Android Room Scanner & Topology Companion App

- **Status:** Accepted
- **Date:** 2026-10-13

## Context

Phase 1 established the centralized Always-On Mini PC platform (`FastAPI + PostgreSQL` on `192.168.55.60:8001` / `5434`) and responsive web frontend (`192.168.55.60:3000`). While the web interface provides an interactive dual topology graph and 3-pillar diagnostic drawer, physical room walkthrough surveys remain manual:
1. Web browsers (Chrome, Firefox) on Android cannot invoke 802.11 radio scanning APIs, access raw BSSIDs, extract 802.11 channel frequencies/widths, or query RSSI signal strengths.
2. Previously, gathering room Wi-Fi data required manual NetX Network Tools export, copy-pasting markdown tables, or running Python scripts from a workstation.
3. Conducting walkthroughs in signal dead-zones (e.g. basement, thick reinforced concrete walls) causes network disconnects, breaking real-time HTTP submissions.
4. Kenneth frequently accesses the home network remotely via Firewalla WireGuard VPN (`192.168.55.60:8001` / `minipc:8001`), where server health checks and 1-click UPnP actions are valuable, but physical Wi-Fi room scanning is invalid because the phone is physically off-premise.

## Decision

1. **Stack Selection (Native Kotlin + Jetpack Compose)**:
   - Built as a native Android application using Kotlin and Jetpack Compose (Material 3).
   - Direct hardware integration with Android's `WifiManager.startScan()` and `ScanResult` APIs without bridge overhead or cross-platform limitations.
2. **Hybrid Companion Role**:
   - Acts as both a **Field Walkthrough Scanner** (walk room to room, single-tap capture 802.11 BSSID readings, automatically classify APs) and a **Pocket Health Console** (view house health, inspect 3-pillar room diagnostics, execute 1-click UPnP actions).
3. **Single-Shot Fresh Room Probes & Throttle Guard**:
   - Each room survey tap triggers 1 fresh active scan probe via `WifiManager.startScan()`, verifying `EXTRA_RESULTS_UPDATED == true` and checking timestamp freshness so stale cached results from previous rooms are never recorded.
   - Operates strictly within Android 10+ scan throttling limits (4 scans per 2 minutes per foreground app) across multi-room walkthroughs. If throttled, presents a visible countdown timer rather than silently saving stale data.
4. **Offline Store-and-Forward (Android Room SQLite)**:
   - Room surveys captured while disconnected (e.g. basement leaf walk) are persisted locally in an Android Room SQLite database queue.
   - An automatic background synchronization worker checks API connectivity and forwards queued surveys to `POST /api/rooms/{slug}/surveys` upon reconnection.
5. **Firewalla WireGuard VPN & Local LAN Dual-Endpoint**:
   - Supports configurable API endpoint switching between Local LAN (`http://192.168.55.60:8001`) and Firewalla VPN (`http://minipc:8001`).
   - Automatically detects VPN connection status via `ConnectivityManager` network transport flags. When connected remotely over VPN, physical Wi-Fi scanning is safely paused with an informative banner, while all house health metrics, telemetry streams, and 1-click actions remain fully functional.
6. **3-Tab Bottom Navigation**:
   - **📍 Survey Walkthrough**: Floor/room selector, 1-tap capture, live BSSID preview, offline queue indicator.
   - **🏠 House Health**: Floor-by-floor room status badges, 3-pillar breakdown (Wi-Fi, Sonos RF/STP, Wired Switch Ports), dual-view topology toggle.
   - **⚡ Quick Actions & Tools**: 1-click Ghost Group reset (`POST /api/actions/flush-ghost-groups`), live Sonos poll (`POST /api/actions/poll-now`), ICMP ping sweep (`POST /api/actions/ping-sweep`), live EMI velocity oscilloscope.
7. **Dual-View Mobile Topology**:
   - Toggle between **Floor Accordion Cards** (touch-friendly collapsible cards optimized for one-handed vertical phone operation) and **Pinch-to-Zoom Pan Canvas** (vector canvas rendering device nodes and active/blocked STP links).

## Consequences

- **Positive**:
  - Eliminates all manual Wi-Fi data transcription; automated room surveys are ingested into the Mini PC PostgreSQL database in seconds.
  - Offline store-and-forward guarantees zero survey data loss in dead-zones.
  - Kenneth has instant 1-click Sonos diagnostic control and house health monitoring from his Android phone anywhere in the house or remotely over VPN.
- **Trade-offs / Limitations**:
  - Requires Android runtime permissions (`ACCESS_FINE_LOCATION`, `ACCESS_WIFI_STATE`, `CHANGE_WIFI_STATE`, plus `android.permission.NEARBY_WIFI_DEVICES` on Android 13+) mandated by Android OS for Wi-Fi scanning.
  - Physical room Wi-Fi scanning is restricted to local on-premise Wi-Fi connectivity.
