# Spec: Phase 1 — Home Wi-Fi & Sonos Network Intelligence Platform

## Problem Statement

Diagnosing and stabilizing the home Wi-Fi environment (`Galerie EAP650`, `Kitchen EAP650`, VLANs 1/10/20/30) and the 14-player Sonos S2 sound system across 11 rooms currently requires a repetitive, manual multi-step workflow:
1. Walking into each `Room` with a phone, running a Wi-Fi scanner (`NetX`), taking multiple screenshots of `BssidReading` values (`dBm`, channel, width), uploading them, and manually transcribing them into Markdown tables.
2. Manually running terminal scripts from the desktop PC (`192.168.55.198`) to poll Sonos players (`:1400/status/proc/ath_rincon/status`, `showstp`, `wireless`, `enetports`, `ZoneGroupTopology`) for `OfdmAniLevel`, `NoiseFloorDbm`, `PhyErrorRate`, `SonosMeshLink` SNR, `StpPathCost`, and `GhostGroup` states.
3. Manually cross-referencing the **Wi-Fi situation**, **Sonos situation**, and **Wired `SwitchPort` VLAN situation** per `Room` without a visual topology graph of how devices are connected, without continuous 24/7 telemetry when the desktop PC is off, and without a UI to dynamically add new `Room` or `NetworkDevice` records.

## Solution

Build an always-on, full-stack **Home Wi-Fi & Sonos Network Intelligence Platform** hosted on the Windows Mini PC (`192.168.55.60`) backed by an isolated Docker PostgreSQL 15 instance (`port 5434`), a Python FastAPI backend + 24/7 telemetry collector, integration with the local TP-Link Omada Software Controller (`:8043`) and Sonos UPnP/Atheros endpoints (`:1400`), and a React + TypeScript + React Flow web/desktop frontend (plus REST/WebSocket APIs ready for the Phase 2 native Android app).

The platform delivers:
- **Per-Room Unified Overview**: Side-by-side grading (`HealthGrade`: `EXCELLENT`, `GOOD`, `MARGINAL`, `CRITICAL`) of the **Wi-Fi coverage** (`2.4 GHz` & `5 GHz` `RssiDbm` per `AccessPointRadio`, co-channel/rogue interference), **Sonos health** (`ConnectionMode`, `OfdmAniLevel`, `PhyErrorRate`, `StpPathCost`, `PingRttMs`, `MasterVolume`), **Wired `SwitchPort` availability**, and connected `NetworkDevice` inventory.
- **Interactive Graphical Network Topology**: Dual visual views—a **Floor & Room Coverage Matrix** (`Keller`, `Erdgeschoss`, `Obergeschoss`, `Dachgeschoss`) and an interactive **Node-Link Topology Graph** rendering `WIRED_LAN`, `WIFI_INFRA`, and `SONOS_MESH` `DeviceConnectionEdge` links (with active `FORWARDING` vs. `BLOCKING` STP tunnels weighted by `FromDb`/`ToDb` SNR).
- **Room-by-Room Survey & Before/After Delta Engine**: Seeded with all verified September/October 2026 room scans and hardware inventories, with 1-click **Room Walkthrough Survey Mode** (capturing live Sonos + Omada client + optional LAN Wireless ADB BSSID scans, or REST payloads from the future Android app) and automatic `SurveyComparisonDelta` calculations.
- **Dynamic Extensibility (Full CRUD)**: Add, edit, reposition, or archive `Floor`, `Room`, `SwitchPort`, and `NetworkDevice` entries in the UI, alongside automatic discovery from Sonos UPnP and Omada.
- **Automated End-to-End `DiagnosticEngine` & `SolutionProposal` Actions**: Automatically detects root causes per room (`GHOST_GROUP_MISMATCH`, `STP_MULTIHOP_DETOUR`, `EMI_NON_WIFI_SPIKE`, `SONOSNET_AIRTIME_SATURATION`, `WIFI_WEAK_COVERAGE`, `CO_CHANNEL_CONTENTION`, `ROGUE_TRANSMITTER_DETECTED`, `BASEMENT_ROOT_TRAP`) and proposes ranked solutions with 1-click execution for safe software actions (`Flush Ghost Groups`, `Run 10s PHY Error Velocity Test`, `Run Room Ping/Jitter Sweep`).

## User Stories

1. As a homeowner, I want the platform pre-seeded with my 4 `Floor` levels, 11 `Room` definitions (mapping Sonos zone `Eltern` `.131` to physical room `Elternschlafzimmer`, `Wohnzimmer_*` to `Wohnzimmer`, and `Fernsehecke (*)` to `Fernsehecke`), `SwitchPort` VLAN mappings, 2 Omada `WIFI_AP` units, and 14 `SONOS_PLAYER` units (using the 5 Oct 2026 post-remediation state from `docs/sonos/devices.md` as active inventory and preserving 19 Sep / 4 Oct 2026 captures as immutable historical surveys), so that I immediately see my entire house topology without re-entering existing data.
2. As a homeowner, I want to view a `Floor`-by-`Floor` room matrix showing each `Room`'s overall `HealthGrade`, Wi-Fi 5 GHz & 2.4 GHz `RssiDbm`, Sonos `OfdmAniLevel` & `PhyErrorRate`, and connected `NetworkDevice` count, so that I can spot problem rooms at a glance.
3. As a homeowner, I want to click into any `Room` to see a comprehensive 3-pillar breakdown (**Wi-Fi Situation**, **Sonos Situation**, and **Wired/Switch Situation**), so that I understand all connectivity factors in that room on a single screen.
4. As a homeowner, I want to see which `AccessPointRadio` (`Galerie AP` Ch 1/44 vs. `Kitchen AP` Ch 11/40) covers each `Room` and at what `RssiDbm` and link speed (`Mbps`), so that I can identify weak signal zones (`< -75 dBm`) or erratic roaming flaps.
5. As a homeowner, I want the system to classify every heard `BssidReading` in a `Room` as `OWN_MANAGED_AP`, `SONOSNET_MESH`, `ROGUE_OWN_RADIO`, or `NEIGHBOR_WIFI`, so that co-channel contention (such as neighbor networks on Ch 11 or accidental rogue transmitters) is immediately flagged.
6. As a homeowner, I want to see each `SONOS_PLAYER`'s live `ConnectionMode` (`ETHERNET_ROOT`, `ETHERNET_NODE`, `SONOSNET_MODE`, `STATION_MODE`, `HT_SATELLITE`), `OfdmAniLevel` (`0–9` or `N/A`), `NoiseFloorDbm` (or `N/A` when hardware reports `0,0,0,0`), and live `PhyErrorRate` (`err/s`), so that I can distinguish clean rooms from rooms suffering active RF corruption.
7. As a homeowner, I want the platform to detect when a `Room` has high `OfdmAniLevel` (`7–9`) and high `PhyErrorRate` (`> 100 err/s`) while Wi-Fi Channel 6 is clear, and diagnose it as local non-Wi-Fi `EMI_SOURCE` leakage (such as a USB-C dock or power brick), so that I don't waste time changing Wi-Fi channels for a non-Wi-Fi EMI problem.
8. As a homeowner, I want to inspect an interactive **Sonos Mesh & STP Graph** showing `Wohnzimmer_Bookshelf` as the `DesignatedRoot`, solid color-coded `FORWARDING` tunnels (`STP 03`/`04`), dashed `BLOCKING` backup links (`STP 00`), 5 GHz `HT_SATELLITE` bonds (`Beam` to both `LR` and bonded `RR`), and `FromDb`/`ToDb` SNR labels on every link, so that I can visually trace how audio packets flow through the house.
9. As a homeowner, I want the `DiagnosticEngine` to automatically flag any `SONOS_PLAYER` with an `StpPathCost > 450` or multi-hop relay detour, and recommend the exact safe remediation—power-cycling the leaf to renegotiate a direct tunnel, switching to 5 GHz `STATION_MODE`, or patching its `Room` `SwitchPort` on `VLAN 10` **with its SonosNet wireless bridge disabled** (or switch STP priority `4096` configured) so lower-MAC speakers like `Nicolas` (`34:7E:5C:36:DE:90`) or `Noah` (`34:7E:5C:35:B2:C0`) never usurp the `DesignatedRoot` (`9000.542a1b63fe6e`) across the BPDU pass-through `Netgear GS316EP`—so that I can eliminate audio dropouts and `DpcDucking` without triggering an attic/bedroom root-bridge trap.
10. As a homeowner, I want to inspect an interactive **Wi-Fi & Wired Infrastructure Graph** showing `Fritzbox 6660` ➔ `Firewalla Purple` ➔ `Netgear GS316EP` (`SwitchPort` 1–16) ➔ `Galerie AP` & `Kitchen AP` ➔ connected `NetworkDevice` endpoints per `Room`, so that I can see exactly how every device in the house is connected.
11. As a homeowner, I want to toggle between the **Wi-Fi Graph**, **Sonos Mesh Graph**, and **Unified End-to-End Topology Graph**, and filter by `Floor`, `Room`, `VLAN`, or `HealthGrade`, so that I can isolate specific layers when troubleshooting.
12. As a homeowner, I want to dynamically **add, edit, move, or archive a `Room`** (assigning its `Floor`, 2D floorplan position, and available `SwitchPort` wall jacks), so that the platform adapts as I expand coverage to new areas (such as `Terrasse`, `Gäste-WC`, or hallway zones) without losing historical survey data.
13. As a homeowner, I want to dynamically **add, edit, reassign, or archive a `NetworkDevice`** in any `Room` (or adopt newly discovered devices from Sonos UPnP and Omada Controller polls), so that new speakers, APs, or IoT devices are tracked without code changes.
14. As a homeowner walking into a `Room` with my phone or laptop, I want to trigger a **Room Walkthrough Survey** (`WiFiRoomSurvey` + `SonosTelemetrySnapshot`) labeled with a note (e.g., *"Post-AP Relocation"*), so that the backend captures and stores the room's Wi-Fi and Sonos state automatically without NetX screenshots.
15. As a homeowner, I want to compare any two surveys for a `Room` via a **Before/After `SurveyComparisonDelta` view**, showing the exact change in `5 GHz dBm`, `2.4 GHz dBm`, `OfdmAniLevel`, `PhyErrorRate`, `StpPathCost`, and `PingRttMs`, so that I have objective proof whether a change helped or hurt.
16. As a homeowner experiencing `"Couldn't play content"` or group join errors, I want the platform to automatically detect `GhostGroup` mismatches (`GroupID` prefix != `CoordinatorUuid`) or `<VanishedDevices>` across all 12 Sonos zones and provide a **1-Click Flush Ghost Groups** button, so that broken cloud handshakes are fixed in seconds.
17. As a homeowner isolating a local EMI source (like unplugging a USB-C dock or moving a speaker 1m), I want a **Live PHY Error Velocity Monitor** mode in the UI that streams 2–3 second updates of `OfdmAniLevel`, `NoiseFloorDbm`, and `PhyErrorRate` (`err/s`) over WebSockets (`WS /api/ws/live-rf`), so that I can watch the interference rate drop to `0.0 err/s` in real time.
18. As a homeowner, I want the Mini PC (`192.168.55.60`) to run a **24/7 Background Telemetry Collector** every 60 seconds and store time-series history in PostgreSQL, so that I can view historical charts (last 1h, 24h, 7d) of room `OfdmAniLevel`, `PhyErrorRate`, `PingRttMs`, and Wi-Fi `RssiDbm` even when my desktop PC was off.
19. As a homeowner moving my TP-Link Omada Software Controller to the Mini PC (`192.168.55.60:8043`), I want the backend's `OmadaControllerAdapter` to pull live AP radio utilization and client BSSID/RSSI associations when available, and degrade gracefully without failing if Omada is restarting or unreachable.
20. As a developer preparing for the Phase 2 Android app, I want a documented, OpenAPI-typed REST + WebSocket API (`GET /api/overview`, `GET /api/topology`, `GET/POST /api/rooms`, `POST /api/rooms/{id}/surveys`, `POST /api/actions/*`, `WS /api/ws/live-rf`) hosted on `http://192.168.55.60:8000`, so that the future Android app can consume the exact same backend without server rewrites.

## Implementation Decisions

### 1. Deep Modules & Seams (`/codebase-design`)

The backend is structured around five deep modules, each presenting a small, deterministic interface at its seam:

1. **`SonosTelemetryModule` (`SonosTelemetryPort` interface)**:
   - **Interface**: `collect_household_snapshot(consumer_id: str) -> HouseholdSonosSnapshot`, `flush_ghost_groups(zone_ips: list[str] | None) -> GhostFlushResult`, `stream_room_rf_velocity(room_id: str, interval_sec: float) -> AsyncIterator[PlayerRfSample]`.
   - **Implementation (`HttpSonosAdapter` & `FakeSonosAdapter`)**:
     - Encapsulates all raw HTTP/XML/SOAP parsing against port `1400` (`/status/proc/ath_rincon/status`, `/status/showstp`, `/status/wireless`, `/status/enetports`, `/xml/device_description.xml`, `/support/review`, `ZoneGroupTopology:1#GetZoneGroupState`, `RenderingControl:1#GetVolume`, `AVTransport:1#BecomeCoordinatorOfStandaloneGroup`), enforcing cross-VLAN Firewalla-safe concurrency (`max_workers <= 14`, `timeout >= 2.0s`).
     - **Bonded Satellite Discovery (`Fernsehecke (RR)`)**: Parses both top-level `<ZoneGroupMember>` elements and nested `<Satellite>` elements inside `ZoneGroupTopology:1#GetZoneGroupState` (and `/support/review` `ZPInfo`/`ath_rincon` blocks) so bonded 5 GHz surround satellites such as `Fernsehecke (RR)` (`RINCON_949F3E00292E01400`, `94:9F:3E:00:29:2E`) have their dynamic IP/status resolved and their 5 GHz Ch 48 `HT_SATELLITE` bond edge to `Fernsehecke (LF,RF)` (`Beam`, `.241`) constructed.
     - **Hardware Telemetry Normalization**: When `/status/proc/ath_rincon/status` or `/support/review` reports `Noise Floor: 0 dBm` (`0, 0, 0, 0` on `Beam`) or `OFDM ANI: undefined`, normalizes `NoiseFloorDbm` and `OfdmAniLevel` to `None` (`N/A`) rather than a numeric `0`.
     - **Isolated `PhyErrorRate` (`err/s`) Delta Cursors**: Maintains isolated `(prev_phy_total, prev_timestamp)` state per `consumer_id` (`"background-60s"` vs. `"on-demand"` vs. each WebSocket stream session ID) so 2–3s WebSocket EMI polling never skews the 60-second PostgreSQL collector window. When a cold/on-demand survey capture has no baseline sample within the last 15 seconds, automatically performs a back-to-back two-sample probe (`1.5s` interval) so `PhyErrorRate` is always non-null. If `current_phy < prev_phy` (speaker rebooted or counter reset), resets the cursor and yields `0.0 err/s`.
2. **`WiFiAndOmadaModule` (`WiFiTelemetryPort` interface)**:
   - **Interface**: `collect_wifi_infrastructure() -> WiFiInfraSnapshot`, `capture_room_wifi_scan(room_id: str, trigger_mode: ScanTriggerMode, raw_bssid_payload: list[BssidInput] | None) -> WiFiRoomSurvey`.
   - **Implementation (`OmadaAndAdbWiFiAdapter` & `FakeWiFiAdapter`)**:
     - Handles Omada Controller OpenAPI/Web session authentication (`:8043`), fetches `AccessPointRadio` states (`Galerie AP`, `Kitchen AP`) and connected client BSSID/RSSI/PHY rate associations, and optionally pulls LAN Android Wireless ADB (`cmd wifi list-scan-results`) or ingested REST scan payloads.
     - **Exact Hardware `BssidClassification` Rules**:
       - `OWN_MANAGED_AP`: Matches by the **lower 5 octets** of the managed EAP650 radios (`:4C:BC:76:7C:40` 2.4G / `:4C:BC:76:7C:41` 5G for `Galerie AP`, and `:4C:BC:76:94:C0` 2.4G / `:4C:BC:76:94:C1` 5G for `Kitchen AP`), because TP-Link virtual VLAN SSIDs mutate the first octet (`72` Admin, `76` Family, `7A` Guest, `7E` IOT, `82` hidden) relative to the base MAC (`6C:4C:BC:...`).
       - `SONOSNET_MESH`: Matches against the exact registered household SonosNet BSSIDs (`BaseMAC + 1` for each of the 14 players) and 5 GHz Ch 48 Home Theater backhaul BSSIDs (`94:9F:3E:C0:EE:A2`, etc.).
       - `ROGUE_OWN_RADIO`: Matches known retired/rogue in-house transmitters (`84:16:F9:93:E9:2B/2C/2D` and `86:16:F9:BF:E9:2D/2E/2F` for standalone `EAP330` / `TP-Link_5G_93E92D`; `0C:72:74:00:63:9A/9B` or unmanaged SSID `WuTangLan` for `Fritzbox 6660`; `6A:55:D4:7D:0B:9B` or `DIRECT-*-EPSON*` for `Epson ET-4850` Wi-Fi Direct).
       - `NEIGHBOR_WIFI`: Any other external 802.11 BSSID (`WLAN-A7C604`, `Vodafone-DD14`, etc.).
3. **`TopologyAndInventoryModule` (`TopologyRepositoryPort` interface)**:
   - **Interface**: CRUD (with soft-archive) for `Floor`, `Room`, `SwitchPort`, `NetworkDevice`, and `WiFiRoomSurvey`; `build_unified_graph(layer_filter: GraphLayerFilter) -> TopologyGraphDto`; `compute_survey_delta(room_id: str, baseline_survey_id: str, target_survey_id: str) -> SurveyComparisonDelta`.
   - **Implementation**:
     - Persists entities in PostgreSQL 15 via SQLAlchemy 2.0 async sessions.
     - **Zone-to-Room & Historical Seed Rules**: Maps the 14 Sonos players into the 11 physical `Room` records (`Wohnzimmer_Bookshelf`, `Wohnzimmer_Esstisch`, `Wohnzimmer_Buchregal` ➔ `Wohnzimmer`; `Fernsehecke (LF,RF)`, `Fernsehecke (LR)`, `Fernsehecke (RR)` ➔ `Fernsehecke`; `Eltern` `.131` ➔ `Elternschlafzimmer`; and 1:1 for `Elternbad`, `Noemi`, `Noah`, `Nicolas`, `Büroecke`, `Küche`, `Keller`). Seeds active `NetworkDevice` connection states from the 5 Oct 2026 post-remediation truth (`docs/sonos/devices.md`: `Wohnzimmer_Bookshelf` wired `ETHERNET_ROOT`, `Keller` wireless leaf) while seeding the 19 Sep 2026 (`docs/sonos/network-matrix.md`, `docs/wifi/*.md`) and 4 Oct / 8 Oct 2026 (`docs/network-availability-by-room.md`, `docs/wifi/nicolas.md`) captures as immutable historical `WiFiRoomSurvey` and `SonosTelemetrySnapshot` records.
     - **Non-Destructive Seeding & Soft-Archive**: Startup seeding uses insert-if-absent (`ON CONFLICT DO NOTHING`) so user CRUD edits are never overwritten on container restart. Deleting a `Room` or `NetworkDevice` via `DELETE /api/rooms/{id}` or `DELETE /api/devices/{id}` performs a soft-archive (`is_archived = true`) rather than cascading hard deletes over historical `WiFiRoomSurvey` and `SonosTelemetrySnapshot` records.
4. **`DiagnosticEngineModule` (`DiagnosticEnginePort` interface)**:
   - **Interface**: `evaluate_house(topology: TopologyGraphDto, sonos: HouseholdSonosSnapshot, wifi: WiFiInfraSnapshot) -> HouseDiagnosticReport`.
   - **Implementation**: Pure, side-effect-free domain engine evaluating deterministic, **`ConnectionMode`-scoped** rules per `Room` and house-wide:
     - **Wi-Fi Grading**: `EXCELLENT >= -55 dBm`, `GOOD -56..-67 dBm`, `MARGINAL -68..-75 dBm`, `CRITICAL < -75 dBm` (evaluated against the strongest `OWN_MANAGED_AP` BSSID per band in that `Room`).
     - **Sonos RF Grading (when `OfdmAniLevel` is present)**: `GOOD` (`ANI 0–3` and `< 20 err/s`), `MARGINAL` (`ANI 4–6` or `20–100 err/s`), `CRITICAL` (`ANI 7–9` or `> 100 err/s`). When `OfdmAniLevel is None` (e.g., `Beam` reporting `undefined`), grades RF health by `PhyErrorRate` and `PingRttMs` without false-failing on `None`.
     - **`ConnectionMode`-Scoped Sonos Link & STP Grading**:
       - `ETHERNET_ROOT` (`Wohnzimmer_Bookshelf`, Cost `0`) and `ETHERNET_NODE` (Cost `10`): Graded `EXCELLENT`/`GOOD` when Ethernet port link is `100FD` and `DesignatedRoot == 9000.542a1b63fe6e`; `CRITICAL` if `DesignatedRoot != 9000.542a1b63fe6e`.
       - `SONOSNET_MODE`: Evaluated strictly on the player's **active upstream `FORWARDING` (`STP 03`/`04`) root-port `SonosMeshLink`** (ignoring `STP 00` `BLOCKING` backup links to other floors): `GOOD` (`min(FromDb, ToDb) >= 30 dB` and `StpPathCost <= 300`), `MARGINAL` (`SNR 20–29 dB` or `StpPathCost 301–450`), `CRITICAL` (`SNR < 20 dB` or `StpPathCost > 450` or `DesignatedRoot != 9000.542a1b63fe6e`).
       - `HT_SATELLITE` (`Fernsehecke LR/RR`): Graded on the 5 GHz Ch 48 bond SNR to `Fernsehecke (LF,RF)` (`Beam`), `OfdmAniLevel`, and `PhyErrorRate`.
       - `STATION_MODE` (e.g., `Nicolas` on 5 GHz Wi-Fi Ch 44): Graded on its associated `OWN_MANAGED_AP` Wi-Fi `RssiDbm`, `OfdmAniLevel`, `PhyErrorRate`, and `PingRttMs` (never penalized for `0 dB` SonosNet peer SNR or non-participation in 2.4 GHz STP).
     - **STP Root Usurpation Guard (`BASEMENT_ROOT_TRAP` / Secondary Wired Leaf Warning)**: Because `Netgear GS316EP` operates in passive BPDU pass-through mode and wired Sonos S2 players default to STP bridge priority `0x9000` (`36864`), 802.1D elects the wired player with the lowest MAC address. Any `SolutionProposal` recommending wiring a secondary room (`Nicolas` `34:7E:5C:36:DE:90` on Port 5, `Noah` `34:7E:5C:35:B2:C0` on Port 7, etc.) explicitly instructs **disabling Wi-Fi/SonosNet on that secondary wired player** (or setting switch STP bridge priority to `4096`) so it operates as a pure `ETHERNET_NODE` leaf without usurping `DesignatedRoot` from `Wohnzimmer_Bookshelf` (`9000.542a1b63fe6e`). If `DesignatedRoot != 9000.542a1b63fe6e` (whether `Keller` `9000.5caafd595eea` or a lower-MAC wired bedroom speaker), `BASEMENT_ROOT_TRAP` fires immediately with `CRITICAL` severity.
5. **`FastApiHttpSeam` (External Application Seam)**:
   - Exposes the REST and WebSocket endpoints consumed by both the React desktop/web frontend and the Phase 2 Android app:
     - `GET /api/overview` (House health summary, floor/room matrix, active diagnostics)
     - `GET /api/topology` (Nodes and `DeviceConnectionEdge` links for React Flow, filterable by layer)
     - `GET/POST/PUT/DELETE /api/floors`, `/api/rooms`, `/api/devices`, `/api/switch-ports`
     - `GET/POST /api/rooms/{room_id}/surveys` & `GET /api/rooms/{room_id}/surveys/delta`
     - `GET /api/rooms/{room_id}/history` (Time-series `SonosTelemetrySnapshot` & Wi-Fi history)
     - `POST /api/actions/flush-ghost-groups`, `POST /api/actions/poll-now`, `POST /api/actions/ping-sweep`
     - `WS /api/ws/live-rf` (Real-time 2–3s streaming telemetry for EMI isolation and walkthrough surveys)

### 2. Frontend Architecture (React + TypeScript + Vite + React Flow)

- **Main Navigation Views**:
  1. **House Matrix & Floor Overview**: Visual cards grouped by `Floor` (`Dachgeschoss`, `Obergeschoss`, `Erdgeschoss`, `Keller`) showing each `Room`'s `HealthGrade` badge, 5 GHz & 2.4 GHz signal meters, Sonos `ConnectionMode` / `ANI` / `PHY err/s` / `STP Cost`, and active `RoomDiagnostic` alerts.
  2. **Interactive Network Topology Map (React Flow)**:
     - Layer toggles: **All Layers**, **Wi-Fi & VLAN Layer**, **Sonos Mesh & STP Layer**.
     - Custom node cards for `WIFI_AP`, `SONOS_PLAYER`, `SWITCH`, `ROUTER`, and `CLIENT_DEVICE` with live telemetry badges.
     - Custom edges showing `FromDb / ToDb` SNR, channel, link rate, and animated flow on active `FORWARDING` paths vs. dashed grey on `BLOCKING` paths.
  3. **Room Deep-Dive & Survey Comparison Drawer/Page**:
     - Detailed 3-pillar breakdown (**Wi-Fi Spectrum Table**, **Sonos RF & Peer Link Table**, **Wired Switch Port & Connected Devices**).
     - **"Capture Room Survey"** button + **Before/After `SurveyComparisonDelta`** selector.
     - **Ranked `SolutionProposal` Cards** with 1-click action buttons.
  4. **Live RF & EMI Isolation Console**:
     - Real-time streaming chart and table (`WS /api/ws/live-rf`) replacement for `tools/sonos_monitor.py --watch`, allowing sequential EMI isolation tests from any browser.
  5. **Room & Device Manager (CRUD + Discovery)**:
     - Add/edit/archive `Room`, `Floor`, `NetworkDevice`, and `SwitchPort` mappings, plus 1-click adoption of newly discovered network nodes.

### 3. Deployment on Always-On Mini PC (`192.168.55.60`)

- `docker-compose.yml` defines:
  - `sonos-network-db`: `postgres:15-alpine` exposed on `192.168.55.60:5434` (`5434:5432`) with persistent volume `sonos_pgdata`.
  - `sonos-network-backend`: FastAPI + Uvicorn + background collector service (`port 8000`) with LAN access to `192.168.10.0/24:1400` and `192.168.55.60:8043`.
  - `sonos-network-frontend`: React/Vite web interface (`port 3000`) accessible from the Desktop PC (`192.168.55.198`) and Android mobile browsers on `WuTangLan-Family` / `Admin`.

## Testing Decisions

- **Primary Test Seam**: Tests exercise the **FastAPI HTTP interface (`AsyncClient`)** and the **Domain Module Interfaces (`SonosTelemetryPort`, `WiFiTelemetryPort`, `DiagnosticEnginePort`, `TopologyRepositoryPort`)** using recorded real-world Sonos XML/proc fixtures (from `Wohnzimmer_Bookshelf`, `Wohnzimmer_Buchregal`, `Fernsehecke Beam/LR/RR`, `Nicolas`, `Noemi`, `Keller`) and Omada JSON fixtures.
- **What Makes a Good Test**:
  - Tests verify observable behavior and domain invariants:
    - Given TP-Link virtual BSSIDs (`72/76/7A/7E/82:4C:BC:76:7C:40/41`), `WiFiAndOmadaModule` classifies them as `OWN_MANAGED_AP` (`Galerie AP`).
    - Given a `STATION_MODE` player (`Nicolas`) with `0 dB` SonosNet peer SNR and `ANI 0`, `DiagnosticEngineModule` grades it `EXCELLENT`/`GOOD` rather than false-failing on STP/mesh SNR.
    - Given a secondary room with a lower-MAC SYMFONISK (`Nicolas` `34:7E:5C:...`), any wired Ethernet `SolutionProposal` includes the mandatory SonosNet Wi-Fi disable / STP root preservation warning.
    - Concurrent calls to `collect_household_snapshot("background-60s")` and `stream_room_rf_velocity` maintain independent `PhyErrorRate` delta cursors.
    - Restarting the application does not overwrite user CRUD modifications or hard-delete historical `WiFiRoomSurvey` records.
- **Frontend Verification**: TypeScript strict typecheck (`tsc --noEmit`) + Vitest component/integration tests verifying the Floor/Room matrix, Topology Graph layer toggles, Room Survey Delta view, and CRUD forms.

## Out of Scope (Phase 1)

- **Native Android APK (`Phase 2`)**: The native Kotlin/Jetpack Compose Android app is tracked as `PHASE-2-ANDROID-APP` on the backlog. In Phase 1, mobile room surveys work immediately via the responsive mobile web UI (`http://192.168.55.60:3000`) and the REST ingestion endpoint (`POST /api/rooms/{id}/surveys`) is built and tested so Phase 2 is a pure client build.
- **Automated Switch Port VLAN Reconfiguration**: The platform tracks `SwitchPort` mappings (`Netgear GS316EP`) and diagnoses VLAN/STP misconfigurations, but does not mutate switch VLAN configs automatically.

## Further Notes

- All domain invariants in `AGENTS.md` (2.4 GHz Ch 1/6/11 plan, 5 GHz Non-DFS Ch 44/40 plan, `Wohnzimmer_Bookshelf` wired STP root, `Keller` wireless leaf, cross-VLAN scan concurrency limits) are enforced as first-class rules in `DiagnosticEngineModule`.
