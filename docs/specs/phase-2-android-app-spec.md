# Spec: Phase 2 — Native Android Room Scanner & Topology Companion App

## 1. Problem Statement

Phase 1 established the Always-On Mini PC platform (`FastAPI + PostgreSQL` on `192.168.55.60:8001` / `5434`) and responsive web interface (`192.168.55.60:3000`). However, executing physical room-by-room Wi-Fi walkthroughs and on-the-go Sonos diagnostics presents fundamental mobile limitations:
1. **Web Sandbox Constraints**: Mobile web browsers (Chrome, Firefox) on Android cannot invoke 802.11 radio scanning APIs (`WifiManager.startScan()`), access raw BSSIDs, extract 802.11 channel frequencies/widths, or query signal strengths (`RssiDbm`). Room surveys previously required manual NetX Network Tools export, copy-pasting tables, or running Python scripts.
2. **Signal Dead-Zones & Concrete Attenuation**: Conducting surveys in dead-zones (e.g., basement, thick reinforced concrete walls between floors) causes immediate network disconnection, dropping unbuffered HTTP submissions.
3. **Firewalla WireGuard Remote VPN Ambiguity**: When Kenneth accesses the network remotely via Firewalla WireGuard VPN (`192.168.55.60:8001`), the companion app should provide full visibility into house health, live telemetry, and 1-click UPnP actions, but must explicitly prevent physical Wi-Fi room surveys because the phone is physically off-premise.
4. **Android 10+ Wi-Fi Scan Throttling**: Android limits foreground apps to 4 scans per 2 minutes (`WIFI_SCAN_THROTTLE`). Walkthrough scanning must operate strictly within OS limits, detect throttled broadcasts, and never persist stale cached scan results.

---

## 2. Solution & Scope

Build a native Android application in `android/` using **Kotlin** and **Jetpack Compose (Material 3)**. The application serves as a **Hybrid Companion**:
- **Field Walkthrough Scanner**: Walk room to room, single-tap capture 802.11 BSSID readings, automatically classify APs, and persist surveys to the Mini PC backend.
- **Pocket Health Console & Quick Actions**: View floor-by-floor house health grades, inspect 3-pillar room diagnostics, and execute 1-click UPnP and network actions (`Flush Ghost Groups`, `Poll Sonos Now`, `Ping Sweep`).
- **Offline Store-and-Forward with Idempotency**: Local Android Room SQLite queue stores captured surveys during dead-zone walks with original `captured_at` timestamps and `client_survey_id` UUIDs, automatically forwarding them to the Mini PC upon reconnection without clobbering history or creating duplicate records.
- **Dual-Endpoint & Firewalla VPN Safety**: Seamlessly switches between Local LAN (`http://192.168.55.60:8001`) and Firewalla VPN (`http://192.168.55.60:8001` / `http://minipc.lan:8001`), automatically pausing physical Wi-Fi scanning during remote VPN sessions.

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
| - Single-Shot Probe   |       | - Android Room SQLite  |      | - Dual Endpoint   |
| - 802.11 Band/Ch/Width|       | - Store-and-Forward    |      | - VPN Transport   |
| - BSSID Normalizer    |       | - Idempotency UUIDs    |      | - REST + WS Client|
| - Throttling Guard    |       | - Timestamp Preserv.   |      | - 3-Pillar DTOs   |
+-----------------------+       +------------------------+      +-------------------+
```

### Module 1: `WifiScannerModule` (`WifiScannerPort`)
- **Seam Protocol Interface**:
  ```kotlin
  data class RawScanProbeResult(
      val capturedAt: Instant,
      val connectedBssid: String?,
      val connectedSsid: String?,
      val linkSpeedMbps: Int?,
      val frequencyMhz: Int?,
      val readings: List<BssidReadingItem>
  )

  data class BssidReadingItem(
      val bssid: String,
      val ssid: String?,
      val band: String,               // "2.4GHz" | "5GHz"
      val channel: Int,
      val centerChannel: Int,
      val widthMhz: Int,              // 20 | 40 | 80 | 160
      val rssiDbm: Int,
      val classification: String,     // OWN_MANAGED_AP | SONOSNET_MESH | ROGUE_OWN_RADIO | NEIGHBOR_WIFI
      val apDeviceSlug: String?,
      val apName: String?,
      val isConnected: Boolean
  )

  interface WifiScannerPort {
      suspend fun runSingleShotProbe(): Result<RawScanProbeResult>
      suspend fun runPrecisionMultiSampleProbe(sampleCount: Int = 2): Result<RawScanProbeResult>
      fun isHardwareScanningSupported(): Boolean
      fun hasRequiredPermissions(): Boolean
  }
  ```
- **Responsibilities & Mechanisms**:
  - Direct hardware binding to Android `WifiManager.startScan()` and asynchronous `BroadcastReceiver(SCAN_RESULTS_AVAILABLE_ACTION)`.
  - **Single-Shot Probe for Walkthroughs**: Default survey trigger invokes `startScan()` exactly once, suspending asynchronously until the OS broadcast completes (with a 10s coroutine timeout). This preserves the Android 10+ foreground throttle budget (4 scans per 2 minutes), allowing up to 4 rooms to be surveyed per 2-minute walkthrough window.
  - **Optional High-Precision Multi-Sample Probe**: For stationary single-room audits, supports a 2-sample probe. RSSI averaging is performed across the **union** of heard BSSIDs. For each BSSID, average RSSI is computed ONLY across samples where that specific BSSID was detected:
    $$\text{avg\_rssi} = \text{round}\left(\frac{\sum_{s \in \text{detected}} \text{rssi}_s}{|\text{detected}|}\right)$$
    Single detections are preserved as-is and never divided by sample count or substituted with 0 dBm.
  - **OS Scan Throttling Defense**:
    - Inspects `startScan()` return boolean and broadcast `intent.getBooleanExtra(WifiManager.EXTRA_RESULTS_UPDATED, false)`.
    - If `false`, the OS throttled the scan and returned stale cached data. The module aborts immediately with `ScanThrottledException`, displays a clear UI throttle banner, and strictly refuses to return or persist stale cached readings.
  - **Runtime Permissions & Location Services Guard**:
    - Requires runtime permissions: `ACCESS_FINE_LOCATION`, `ACCESS_WIFI_STATE`, `CHANGE_WIFI_STATE`, and Android 13+ (API 33+) `NEARBY_WIFI_DEVICES`.
    - `hasRequiredPermissions()` verifies both granted runtime permissions AND `LocationManager.isLocationEnabled()`. If Location Services are toggled off in system settings, Wi-Fi scanning is blocked with an explicit user prompt to prevent silent empty scans.
  - **802.11 Frequency, Channel & Width Mapping**:
    - $2412 - 2472\text{ MHz} \implies \text{Ch } (f - 2407) / 5$ (`2.4GHz`, 20 MHz).
    - $2484\text{ MHz} \implies \text{Ch } 14$ (`2.4GHz`, 20 MHz).
    - $5180 - 5240\text{ MHz} \implies \text{Ch } (f - 5000) / 5$ (UNII-1, e.g. $5220\text{ MHz} \implies \text{Ch } 44$, $5200\text{ MHz} \implies \text{Ch } 40$).
    - $5260 - 5320\text{ MHz} \implies \text{Ch } (f - 5000) / 5$ (UNII-2A DFS, Channels 52–64).
    - $5500 - 5720\text{ MHz} \implies \text{Ch } (f - 5000) / 5$ (UNII-2C DFS, Channels 100–144).
    - $5745 - 5825\text{ MHz} \implies \text{Ch } (f - 5000) / 5$ (UNII-3 / SRD, Channels 149, 153, 157, 161, 165).
    - **Channel width & center frequency extraction from `ScanResult`**:
      - `CHANNEL_WIDTH_20MHZ`: `width_mhz = 20`, `center_channel = channel`.
      - `CHANNEL_WIDTH_40MHZ`: `width_mhz = 40`, `center_channel = if (centerFreq0 in 1..2999) (centerFreq0 - 2407) / 5 else if (centerFreq0 >= 5000) (centerFreq0 - 5000) / 5 else channel`.
      - `CHANNEL_WIDTH_80MHZ`: `width_mhz = 80`, `center_channel = if (centerFreq0 >= 5000) (centerFreq0 - 5000) / 5 else channel` (e.g. Galerie AP Ch 44 80 MHz centerFreq0 $5210\text{ MHz} \implies \text{Ch } 42$).
      - `CHANNEL_WIDTH_160MHZ`: `width_mhz = 160`, `center_channel = if (centerFreq0 >= 5000) (centerFreq0 - 5000) / 5 else channel`.
  - **BSSID Normalization & Client Classification**:
    - `OWN_MANAGED_AP`: Matches lower 5 octets `:4C:BC:76:7C:40/41` (`Galerie AP`) or `:4C:BC:76:94:C0/C1` (`Kitchen AP`).
    - `SONOSNET_MESH`: Matches registered SonosNet BSSIDs (`BaseMAC + 1`) and 5 GHz HT backhaul.
    - `ROGUE_OWN_RADIO`: Matches known rogue MACs/SSIDs (`EAP330`, `Fritzbox` `WuTangLan`, `Epson` Wi-Fi Direct).
    - `NEIGHBOR_WIFI`: Any external BSSID.

### Module 2: `SurveyQueueModule` (`SurveyQueuePort`)
- **Seam Protocol Interface**:
  ```kotlin
  @Entity(tableName = "pending_surveys")
  data class PendingSurveyEntity(
      @PrimaryKey(autoGenerate = true) val id: Long = 0,
      val clientSurveyId: String,       // UUID for server idempotency deduplication
      val roomSlug: String,
      val capturedAt: String,           // ISO 8601 UTC timestamp of measurement
      val label: String?,
      val triggerMode: String = "MANUAL_SURVEY",
      val connectedBssid: String?,
      val connectedSsid: String?,
      val linkSpeedMbps: Int?,
      val frequencyMhz: Int?,
      val notes: String?,
      val readingsJson: String,          // Serialized List<BssidReadingInput>
      val syncStatus: String = "PENDING",// PENDING | SYNCED | FAILED
      val retryCount: Int = 0
  )

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
  - **Timestamp Preservation & Idempotency**:
    - Each captured survey records a permanent `clientSurveyId` (UUID) and the exact `capturedAt` measurement timestamp.
    - When drained via `POST /api/rooms/{room_slug}/surveys`, sends `client_survey_id` and `captured_at`. The backend uses `client_survey_id` for deduplication, guaranteeing that retries during patchy connectivity never produce duplicate database rows.
    - Draining occurs in strict chronological order of `capturedAt`.
  - **Dead-Zone Survey Handling**:
    - In dead-zones (e.g. `Keller` where zero BSSIDs are heard), `readingsJson` is persisted as `[]`.
    - Submitted to the backend as `readings: []`, which creates a legitimate dead-zone survey (0 readings, `best_5ghz_dbm = null`, `wifi_health_grade = CRITICAL`) without falling back to server-side scan.

### Module 3: `NetworkClientModule` (`SonosNetworkClientPort` & `ConnectivityPort`)
- **Seam Protocol Interface**:
  ```kotlin
  data class LiveRfFrameDto(
      val timestamp: String,
      val consumerId: String,
      val roomSlug: String,
      val samples: List<LiveRfSampleDto>
  )

  interface SonosNetworkClientPort {
      suspend fun getOverview(): Result<HouseOverviewDto>
      suspend fun getTopology(layer: String?): Result<TopologyGraphDto>
      suspend fun getRoomSurveys(roomSlug: String): Result<List<WiFiRoomSurveyDto>>
      suspend fun getRoomDiagnostics(roomSlug: String): Result<RoomDiagnosticSummaryDto>
      suspend fun getSurveyDelta(roomSlug: String, baselineSlug: String? = null, targetSlug: String? = null): Result<SurveyComparisonDeltaDto>
      suspend fun submitRoomSurvey(roomSlug: String, payload: RoomSurveyInputDto): Result<WiFiRoomSurveyDto>
      suspend fun flushGhostGroups(): Result<GhostFlushResultDto>
      suspend fun pollNow(): Result<Unit>
      suspend fun pingSweep(): Result<PingSweepResultDto>
      fun streamLiveRf(roomSlug: String): Flow<LiveRfFrameDto>
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
    - `FIREWALLA_VPN`: `http://192.168.55.60:8001` (or FQDN `http://minipc.lan:8001`) — IP-routed over WireGuard VPN to prevent single-label NetBIOS DNS resolution failure.
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
       - Prominent **"Scan Room Now"** button (shows progress spinner bound to coroutine execution with 10s safety timeout; disabled if Remote VPN is active or permissions/location missing).
       - Live scan preview card (strongest 5 GHz / 2.4 GHz AP, link speed, heard BSSID list grouped by classification).
       - Offline queue pill (e.g., *"2 surveys queued (offline)"*) with manual **"Sync Now"** button.
    2. **🏠 House Health**:
       - Overall House Health Grade banner (`EXCELLENT`, `GOOD`, `MARGINAL`, `CRITICAL`).
       - Dual-View toggle:
         - **Floor Accordion Cards**: Touch-friendly collapsible cards displaying each room's Wi-Fi RSSI, Sonos ANI / PHY err/s, and switch port status. Tapping a room fetches `GET /api/rooms/{slug}/diagnostics` and opens the **Room 3-Pillar Diagnostic Sheet**.
         - **Pinch-to-Zoom Pan Canvas**: Vector-rendered topological graph showing device cards and active/blocked STP links with interactive zoom and pan.
    3. **⚡ Quick Actions & Tools**:
       - **1-Click Ghost Group Reset**: Instant call to `POST /api/actions/flush-ghost-groups` with response dialog.
       - **Poll Sonos Now**: Instant call to `POST /api/actions/poll-now`.
       - **ICMP Ping Sweep**: Instant call to `POST /api/actions/ping-sweep`.
       - **Live RF Velocity Oscilloscope**: Real-time rolling waveform of PHY error rate and ANI desensitization fed by `streamLiveRf` WebSocket wrapper frames.

---

## 4. User Stories & Acceptance Criteria

1. **US-1: Single-Tap Room Walkthrough Scan**:
   - As Kenneth walking into `Nicolas` (attic), I select `Dachgeschoss` > `Nicolas` and tap "Scan Room". The app executes an asynchronous single-shot scan awaiting OS broadcast, classifies BSSIDs (`Galerie AP` on Ch 44 at 80 MHz, neighbor networks), and submits `captured_at` and `client_survey_id` to `POST /api/rooms/nicolas/surveys`.
2. **US-2: Offline Dead-Zone Store-and-Forward**:
   - As Kenneth walking into `Keller` where Wi-Fi drops completely, I tap "Scan Room". The app records the survey into Room SQLite with `readings: []`, displays *"1 survey queued (offline)"*, and automatically posts it to the Mini PC once Wi-Fi reconnects on `Erdgeschoss`, preserving original timestamp and marking health grade `CRITICAL` without triggering server fallback.
3. **US-3: Firewalla VPN Safe Mode**:
   - As Kenneth traveling outside the home connected via Firewalla WireGuard VPN (`192.168.55.60:8001`), the app displays a prominent **"Remote VPN Active"** badge. Physical Wi-Fi scanning is safely disabled, while House Health, 3-Pillar Room Diagnostics, and 1-click UPnP actions remain operational.
4. **US-4: 1-Click Ghost Group Flush from Phone**:
   - As Kenneth experiencing Spotify playback stutter or group join failures, I open "Quick Actions", tap "Flush Ghost Groups", and receive confirmation that all 12 zones are reset as standalone coordinators in under 3 seconds.
5. **US-5: Mobile Dual-View Topology & 3-Pillar Diagnostics**:
   - As Kenneth reviewing network routing on my phone, I can toggle between vertical Floor Accordion Cards and a pinch-to-zoom vector topology graph, and tap any room to view server-computed Wi-Fi, Sonos RF/STP, and wired switch diagnostics.

---

## 5. Domain Invariants & Audit Gates (Gate Criteria)

The Phase 2 implementation must strictly enforce the following invariants:
1. **[G1] Telemetry & RF Data Integrity**:
   - 802.11 channel and frequency calculations must be exact ($2412\text{ MHz} \implies \text{Ch } 1$, $5220\text{ MHz} \implies \text{Ch } 44$, $5745\text{ MHz} \implies \text{Ch } 149$).
   - 802.11 channel widths (20/40/80/160 MHz) and center channels must be preserved from `ScanResult.channelWidth` and `centerFreq0`.
   - Multi-sample RSSI averaging must operate across the detected union without zero-padding or dividing single detections.
   - BSSID classifications must match server rules (EAP650 lower 5 octets, SonosNet BaseMAC+1, rogue radios).
2. **[G2] Invariant Compliance & Scan Throttling**:
   - Must strictly adhere to Android 10+ 4-scan/2-minute throttling via single-shot probes for walkthroughs.
   - Must verify `EXTRA_RESULTS_UPDATED == true` and abort on throttled stale cached scans.
   - Must pause physical Wi-Fi scanning when connected over remote VPN.
   - STP root invariant (`Wohnzimmer_Bookshelf` Cost 0) and basement leaf invariant must never be misstated in UI copy.
3. **[G3] Architectural Boundary Discipline**:
   - The Android app is a companion client: all diagnostic rule evaluation (`DiagnosticEngine`) and historical analytics remain strictly server-side on FastAPI via `RoomDiagnosticSummaryDto`.
4. **[G4] Error Handling, Timestamp Preservation & Zero Data Loss**:
   - Network failure during room scan must never discard user scan data; payloads must safely fall back to Room SQLite.
   - Reconnection sync must be idempotent (via `client_survey_id`) and preserve original `captured_at` measurement timestamps.
   - Dead-zone surveys with zero heard BSSIDs must persist `readings: []` without triggering server-side scan fallback.

---

## 6. Testing Strategy

1. **Unit & Seam Tests (Robolectric / JUnit 5)**:
   - `WifiScannerServiceTest`: Tests 802.11 band, frequency, UNII-3, channel width, center frequency calculation, and asymmetric multi-sample RSSI averaging against recorded `ScanResult` fixtures.
   - `ThrottlingAndPermissionGuardTest`: Tests throttled broadcast detection (`EXTRA_RESULTS_UPDATED = false`), Android 13+ `NEARBY_WIFI_DEVICES`, and Location Services toggle enforcement.
   - `BssidClassifierTest`: Tests BSSID normalization and classification against EAP650 virtual SSIDs, SonosNet BSSIDs, rogue transmitters, and neighbor networks.
   - `SurveyQueueRepositoryTest`: Tests offline SQLite enqueueing, ordering, pending count flow, idempotency keys, and timestamp preservation.
   - `ConnectivityMonitorTest`: Tests network capability detection, VPN transport detection, and dual-endpoint switching.
   - `SonosNetworkClientTest`: Tests REST serialization/deserialization, WebSocket `LiveRfFrameDto` unwrapping, and 3-pillar diagnostic retrieval against mock HTTP server responses.
2. **Compose UI Tests**:
   - `SurveyWalkthroughScreenTest`: Verifies room selection, single-shot scan button state, progress indicators, throttle warning banner, and offline queue banner.
   - `HouseHealthScreenTest`: Verifies dual-view accordion vs. canvas toggle, room health badges, and 3-pillar diagnostic sheet display.
   - `QuickActionsScreenTest`: Verifies 1-click action buttons and response dialogs.
