# Spec: Phase 2 — Native Android Room Scanner & Topology Companion App

## 1. Problem Statement

Phase 1 established the Always-On Mini PC platform (`FastAPI + PostgreSQL` on `192.168.55.60:8001` / `5434`) and responsive web interface (`192.168.55.60:3000`). However, executing physical room-by-room Wi-Fi walkthroughs and on-the-go Sonos diagnostics presents fundamental mobile limitations:
1. **Web Sandbox Constraints**: Mobile web browsers (Chrome, Firefox) on Android cannot invoke 802.11 radio scanning APIs (`WifiManager.startScan()`), access raw BSSIDs, extract 802.11 channel frequencies/widths, or query signal strengths (`RssiDbm`). Room surveys previously required manual NetX Network Tools export, copy-pasting tables, or running Python scripts.
2. **Signal Dead-Zones & Concrete Attenuation**: Conducting surveys in dead-zones (e.g., basement, thick reinforced concrete walls between floors) causes immediate network disconnection, dropping unbuffered HTTP submissions.
3. **Firewalla WireGuard Remote VPN Ambiguity**: When Kenneth accesses the network remotely via Firewalla WireGuard VPN (`minipc:8001` / `192.168.55.60:8001`), the companion app should provide full visibility into house health, live telemetry, and 1-click UPnP actions, but must explicitly prevent physical Wi-Fi room surveys because the phone is physically off-premise.
4. **Android 10+ Wi-Fi Scan Throttling**: Android limits foreground apps to 4 scans per 2 minutes (`WIFI_SCAN_THROTTLE`). Continuous background scanning fails or requires developer options to be disabled.

## 2. Solution & Scope

Build a native Android application in `android/` using **Kotlin** and **Jetpack Compose (Material 3)**. The application serves as a **Hybrid Companion**:
- **Field Walkthrough Scanner**: Walk room to room, single-tap capture 802.11 BSSID readings, automatically classify APs, and persist surveys to the Mini PC backend.
- **Pocket Health Console & Quick Actions**: View floor-by-floor house health grades, inspect 3-pillar room diagnostics, and execute 1-click UPnP and network actions (`Flush Ghost Groups`, `Poll Sonos Now`, `Ping Sweep`).
- **Offline Store-and-Forward**: Local Android Room SQLite queue stores captured surveys during dead-zone walks and automatically forwards them to the Mini PC upon reconnection.
- **Dual-Endpoint & Firewalla VPN Safety**: Seamlessly switches between Local LAN (`http://192.168.55.60:8001`) and Firewalla VPN (`http://minipc:8001`), automatically pausing physical Wi-Fi scanning during remote VPN sessions.

---

## 3. Deep Modules & Architecture Boundaries (`/codebase-design`)

The Android application is organized into 4 deep modules, each exposing a minimal, deterministic interface:

```
+-----------------------------------------------------------------------------------+
|                              Jetpack Compose UI                                   |
|   [ Tab 1: Survey Walkthrough ]  [ Tab 2: House Health ]  [ Tab 3: Quick Actions ] |
+-----------------------------------------------------------------------------------+
        |                                   |                              |
        v                                   v                              v
+-----------------------+       +------------------------+      +-------------------+
|  WifiScannerModule    |       |   SurveyQueueModule    |      | NetworkClientMod  |
|  (WifiScannerPort)    |       |   (SurveyQueuePort)    |      | (SonosClientPort) |
|                       |       |                        |      |                   |
| - SingleShotProbe     |       | - Android Room SQLite  |      | - Dual Endpoint   |
| - 802.11 Frequency/Ch |       | - Store-and-Forward    |      | - VPN Transport   |
| - BSSID Normalizer    |       | - Auto-Sync on Reconn  |      | - REST + WS Client|
+-----------------------+       +------------------------+      +-------------------+
```

### Module 1: `WifiScannerModule` (`WifiScannerPort`)
- **Seam Protocol Interface**:
  ```kotlin
  interface WifiScannerPort {
      suspend fun runSingleShotProbe(): Result<RawScanProbeResult>
      fun isHardwareScanningSupported(): Boolean
      fun hasRequiredPermissions(): Boolean
  }
  ```
- **Responsibilities & Mechanisms**:
  - Direct hardware binding to Android `WifiManager.startScan()` and `BroadcastReceiver(SCAN_RESULTS_AVAILABLE_ACTION)`.
  - **Single-Shot 2-Sample Probe**: Triggers a back-to-back 2-sample probe spaced 1.5s apart, averaging RSSI values to suppress momentary Rayleigh multipath fading spikes.
  - Abides strictly by Android 10+ 4-scan/2-minute throttling without requiring developer mode tweaks.
  - **802.11 Frequency & Channel Mapping**:
    - $2412 - 2472\text{ MHz} \implies \text{Ch } (f - 2407) / 5$ (`2.4GHz`, 20 MHz).
    - $5180 - 5240\text{ MHz} \implies \text{Ch } (f - 5000) / 5$ (UNII-1, e.g. $5220\text{ MHz} \implies \text{Ch } 44$, $5200\text{ MHz} \implies \text{Ch } 40$).
    - $5260 - 5320\text{ MHz} \implies \text{Ch } (f - 5000) / 5$ (UNII-2A DFS).
    - $5500 - 5720\text{ MHz} \implies \text{Ch } (f - 5000) / 5$ (UNII-2C DFS).
  - **BSSID Normalization & Client Classification**:
    - `OWN_MANAGED_AP`: Matches lower 5 octets `:4C:BC:76:7C:40/41` (`Galerie AP`) or `:4C:BC:76:94:C0/C1` (`Kitchen AP`).
    - `SONOSNET_MESH`: Matches registered SonosNet BSSIDs (`BaseMAC + 1`) and 5 GHz HT backhaul.
    - `ROGUE_OWN_RADIO`: Matches known rogue MACs/SSIDs (`EAP330`, `Fritzbox` `WuTangLan`, `Epson` Wi-Fi Direct).
    - `NEIGHBOR_WIFI`: Any external BSSID.

### Module 2: `SurveyQueueModule` (`SurveyQueuePort`)
- **Seam Protocol Interface**:
  ```kotlin
  interface SurveyQueuePort {
      suspend fun enqueueSurvey(survey: PendingSurveyEntity): Long
      suspend fun getPendingSurveys(): List<PendingSurveyEntity>
      suspend fun markSurveySynced(id: Long)
      suspend fun getPendingCount(): Flow<Int>
      suspend fun purgeSyncedSurveys()
  }
  ```
- **Responsibilities & Mechanisms**:
  - Implemented via **Android Room SQLite** (`sonos_survey_cache.db`).
  - Persists `PendingSurveyEntity` records containing `room_slug`, `timestamp`, `label`, `connected_bssid`, `link_speed_mbps`, and serialized JSON `readings`.
  - Supports offline walkthroughs: when a room survey is captured without network connectivity, it is immediately enqueued locally with state `PENDING`.
  - An auto-sync coordinator observes network reachability: once the Mini PC API is reachable, it drains the queue sequentially via `POST /api/rooms/{slug}/surveys` without losing survey timestamps or ordering.

### Module 3: `NetworkClientModule` (`SonosNetworkClientPort` & `ConnectivityPort`)
- **Seam Protocol Interface**:
  ```kotlin
  interface SonosNetworkClientPort {
      suspend fun getOverview(): Result<HouseOverviewDto>
      suspend fun getTopology(layer: String?): Result<TopologyGraphDto>
      suspend fun getRoomSurveys(roomSlug: String): Result<List<WiFiRoomSurveyDto>>
      suspend fun submitRoomSurvey(roomSlug: String, payload: RoomSurveyInputDto): Result<WiFiRoomSurveyDto>
      suspend fun flushGhostGroups(): Result<GhostFlushResultDto>
      suspend fun pollNow(): Result<Unit>
      suspend fun pingSweep(): Result<PingSweepResultDto>
      fun streamLiveRf(roomSlug: String): Flow<LiveRfSampleDto>
  }

  interface ConnectivityPort {
      fun observeConnectionState(): Flow<ConnectionState>
      fun isRemoteVpnActive(): Boolean
      fun getActiveEndpointUrl(): String
      fun setEndpointMode(mode: EndpointMode)
  }
  ```
- **Responsibilities & Mechanisms**:
  - Built with **Ktor HTTP Client** (or OkHttp + Retrofit) with kotlinx.serialization.
  - **Dual-Endpoint Switching**:
    - `LOCAL_LAN`: `http://192.168.55.60:8001`
    - `FIREWALLA_VPN`: `http://minipc:8001`
    - `AUTO`: Resolves reachability on connect; falls back to VPN endpoint if local LAN fails.
  - **VPN Transport Safety Guard**:
    - Queries `ConnectivityManager.getNetworkCapabilities(activeNetwork)`.
    - Detects `NetworkCapabilities.TRANSPORT_VPN`.
    - When `isRemoteVpnActive() == true`:
      - Flags connection as `REMOTE_VPN`.
      - **Disables physical room Wi-Fi scanning** in UI with banner: *"Connected via Firewalla Remote VPN — Physical Wi-Fi scanning paused (device is off-premise)."*
      - Keeps all telemetry polling, 3-pillar health views, and 1-click UPnP actions fully enabled.

### Module 4: `ComposeUiModule` (Jetpack Compose UI)
- **Navigation Architecture**:
  - `BottomNavigationBar` with 3 primary tabs:
    1. **📍 Survey Walkthrough**:
       - Floor selector (`Keller`, `Erdgeschoss`, `Obergeschoss`, `Dachgeschoss`) and Room chip selector.
       - Prominent **"Scan Room Now"** button (shows progress spinner during 1.5s 2-sample probe; disabled if Remote VPN is active or permissions missing).
       - Live scan preview card (strongest 5 GHz / 2.4 GHz AP, link speed, heard BSSID list grouped by classification).
       - Offline queue pill (e.g., *"2 surveys queued (offline)"*) with manual **"Sync Now"** button.
    2. **🏠 House Health**:
       - Overall House Health Grade banner (`EXCELLENT`, `GOOD`, `MARGINAL`, `CRITICAL`).
       - Dual-View toggle:
         - **Floor Accordion Cards**: Touch-friendly collapsible cards displaying each room's Wi-Fi RSSI, Sonos ANI / PHY err/s, and switch port status. Tapping a room opens the **Room 3-Pillar Diagnostic Sheet**.
         - **Pinch-to-Zoom Pan Canvas**: Vector-rendered topological graph showing device cards and active/blocked STP links with interactive zoom and pan.
    3. **⚡ Quick Actions & Tools**:
       - **1-Click Ghost Group Reset**: Instant call to `POST /api/actions/flush-ghost-groups` with response dialog.
       - **Poll Sonos Now**: Instant call to `POST /api/actions/poll-now`.
       - **ICMP Ping Sweep**: Instant call to `POST /api/actions/ping-sweep`.
       - **Live RF Velocity Oscilloscope**: Real-time rolling waveform of PHY error rate and ANI desensitization.

---

## 4. User Stories & Acceptance Criteria

1. **US-1: Single-Tap Room Walkthrough Scan**:
   - As Kenneth walking into `Nicolas` (attic), I select `Dachgeschoss` > `Nicolas` and tap "Scan Room". The app runs a 2-sample probe over 1.5 seconds, averages RSSIs, classifies BSSIDs (`Galerie AP` on Ch 44, neighbor networks), and submits to `POST /api/rooms/nicolas/surveys`.
2. **US-2: Offline Dead-Zone Store-and-Forward**:
   - As Kenneth walking into `Keller` where Wi-Fi drops completely, I tap "Scan Room". The app records the survey into Room SQLite, displays *"1 survey queued (offline)"*, and automatically posts it to the Mini PC once Wi-Fi reconnects on `Erdgeschoss`.
3. **US-3: Firewalla VPN Safe Mode**:
   - As Kenneth traveling outside the home connected via Firewalla WireGuard VPN (`minipc:8001`), the app displays a prominent **"Remote VPN Active"** badge. Physical Wi-Fi scanning is safely disabled, while House Health, Room Diagnostics, and 1-click UPnP actions remain operational.
4. **US-4: 1-Click Ghost Group Flush from Phone**:
   - As Kenneth experiencing Spotify playback stutter or group join failures, I open "Quick Actions", tap "Flush Ghost Groups", and receive confirmation that all 12 zones are reset as standalone coordinators in under 3 seconds.
5. **US-5: Mobile Dual-View Topology**:
   - As Kenneth reviewing network routing on my phone, I can toggle between vertical Floor Accordion Cards for quick one-handed reading and a pinch-to-zoom vector topology graph to inspect STP mesh links and home theater bonds.

---

## 5. Domain Invariants & Audit Gates (Gate Criteria)

The Phase 2 implementation must strictly enforce the following invariants:
1. **[G1] Telemetry & RF Data Integrity**:
   - 802.11 channel and frequency calculations must be exact ($2412\text{ MHz} \implies \text{Ch } 1$, $5220\text{ MHz} \implies \text{Ch } 44$).
   - BSSID classifications must match the server's exact rules (EAP650 lower 5 octets, SonosNet BaseMAC+1, rogue radios).
   - RSSI values must never be inverted or corrupted during SQLite serialization.
2. **[G2] Invariant Compliance & Scan Throttling**:
   - Must strictly adhere to Android 10+ 4-scan/2-minute throttling via single-shot 2-sample probes (never continuous unthrottled background loops).
   - Must pause physical Wi-Fi scanning when connected over remote VPN.
   - STP root invariant (`Wohnzimmer_Bookshelf` Cost 0) and basement leaf invariant must never be misstated in UI copy.
3. **[G3] Architectural Boundary Discipline**:
   - The Android app is a companion client: all diagnostic rule evaluation (`DiagnosticEngine`) and historical analytics remain strictly server-side on FastAPI. The app displays server-computed grades and proposals faithfully without duplicating business logic.
4. **[G4] Error Handling & Zero Data Loss**:
   - Network failure during room scan must never discard user scan data; payloads must safely fall back to the Room SQLite queue.
   - Reconnection sync must be idempotent and preserve survey timestamps.

---

## 6. Testing Strategy

1. **Unit & Seam Tests (Robolectric / JUnit 5)**:
   - `WifiScannerServiceTest`: Tests 802.11 band, frequency, channel calculation, and 2-sample averaging against recorded `ScanResult` fixtures.
   - `BssidClassifierTest`: Tests BSSID normalization and classification against EAP650 virtual SSIDs, SonosNet BSSIDs, rogue transmitters, and neighbor networks.
   - `SurveyQueueRepositoryTest`: Tests offline SQLite enqueueing, ordering, pending count flow, and sync marking.
   - `ConnectivityMonitorTest`: Tests network capability detection, VPN transport detection, and dual-endpoint switching.
   - `SonosNetworkClientTest`: Tests REST serialization/deserialization and error handling against mock HTTP server responses.
2. **Compose UI Tests**:
   - `SurveyWalkthroughScreenTest`: Verifies room selection, scan button state, progress indicators, and offline queue banner.
   - `HouseHealthScreenTest`: Verifies dual-view accordion vs. canvas toggle, room health badges, and diagnostic sheet display.
   - `QuickActionsScreenTest`: Verifies 1-click action buttons and response dialogs.
