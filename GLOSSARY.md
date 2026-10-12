# Domain Glossary — Home Wi-Fi & Sonos Network Intelligence Platform

This glossary is the single source of truth for domain terms across the backend, frontend, future Android app, specs, and tickets. Always use these exact terms in code, database tables, API contracts, and UI labels.

---

## 1. Spatial & Physical Topology

- **`Floor`**: A vertical level of the residence (`Keller`, `Erdgeschoss`, `Obergeschoss`, `Dachgeschoss`). Contains one or more `Room` entities.
- **`Room`**: A physical space in the house (e.g., `Wohnzimmer`, `Fernsehecke`, `Küche`, `Büroecke`, `Galerie`, `Elternschlafzimmer`, `Elternbad`, `Noemi`, `Noah`, `Nicolas`, `Keller`). Every `Room` has an assigned `Floor`, 2D layout coordinates, optional wired `SwitchPort` wall jacks, and an aggregated `HealthGrade`.
  - *Avoid*: "zone" when referring to a physical room (a single `Room` like `Wohnzimmer` can contain three distinct Sonos `ZonePlayer` units: `Wohnzimmer_Bookshelf`, `Wohnzimmer_Esstisch`, `Wohnzimmer_Buchregal`).
- **`SwitchPort`**: A physical RJ45 port (`1–16`) on the managed switch (`Netgear GS316EP` at `192.168.55.155`), carrying a `PVID`, untagged/tagged `VLAN` membership (`VLAN 1 Admin`, `VLAN 10 WuTangLan-Family`, `VLAN 20 WuTangLan-Guest`, `VLAN 30 WuTangLan-IOT`), `BPDU` handling policy, and optional patch mapping to a `Room` wall jack.
- **`NetworkDevice`**: Any hardware node tracked in a `Room`, categorized by `DeviceRole`:
  - `SONOS_PLAYER`: One of the 14 Sonos speakers (`SYMFONISK Bookshelf`, `Play:1`, `Play:3`, `Beam`).
  - `WIFI_AP`: A wireless access point (`Galerie EAP650`, `Kitchen EAP650`, or retired `EAP330`).
  - `SWITCH`: Managed L2 switch (`Netgear GS316EP`).
  - `ROUTER`: L3 VLAN gateway (`Firewalla Purple`) or upstream cable modem (`Fritzbox 6660`).
  - `CLIENT_DEVICE`: Fixed or mobile Wi-Fi/LAN endpoint (`PC`, `Mini PC`, `Phone`, `Nuki Bridge`, `Epson ET-4850`).
  - `EMI_SOURCE`: Non-Wi-Fi 2.4 GHz electromagnetic emitter (e.g., `USB-C Dock`, switching power brick) documented as a local noise source.

---

## 2. Wi-Fi Coverage & Spectrum Domain

- **`AccessPointRadio`**: A single physical radio (`2.4 GHz` or `5 GHz`) on a `WIFI_AP`, defined by its base MAC, derived BSSIDs, pinned IEEE channel (`Ch 1`, `Ch 11`, `Ch 40`, `Ch 44`), channel width (`20 MHz`, `40 MHz`, `80 MHz`), transmit power (`dBm`), and Omada airtime utilization percentage.
- **`BssidReading`**: A single over-the-air observation of an `802.11` BSSID inside a `Room`, recording `BSSID`, `SSID`, `Band` (`2.4GHz` | `5GHz`), `Channel`, `CenterChannel`, `WidthMHz`, `RssiDbm` (`-30` to `-100 dBm`), and `BssidClassification`:
  - `OWN_MANAGED_AP`: Active Omada-managed EAP650 BSSID (`Galerie AP` `...:7C:40/41` or `Kitchen AP` `...:94:C0/94:C1`).
  - `SONOSNET_MESH`: Hidden 2.4 GHz Ch 6 SonosNet mesh BSSID or 5 GHz Ch 48 Home Theater backhaul BSSID.
  - `ROGUE_OWN_RADIO`: Unmanaged or unintended in-house transmitter (e.g., standalone `EAP330`, `Fritzbox` Wi-Fi, `Epson` Wi-Fi Direct).
  - `NEIGHBOR_WIFI`: External neighbor network (`WLAN-A7C604`, `Vodafone-DD14`, etc.).
- **`WiFiRoomSurvey`**: A timestamped collection of `BssidReading` records and active client link metrics (`ConnectedBssid`, `LinkSpeedMbps`, `FrequencyMHz`) captured inside a specific `Room` (either seeded from historical NetX captures, polled from Omada client association, or pushed via a live mobile/Android room scan).
- **`SurveyComparisonDelta`**: A structured Before/After diff between two `WiFiRoomSurvey` (and `SonosTelemetrySnapshot`) records for the same `Room`, quantifying signal improvement (`dB`), interference reduction (`ANI` / `PHY err/s`), and channel cleanliness after a physical or configuration change.

---

## 3. Sonos RF, STP Mesh & Playback Domain

- **`ConnectionMode`**: How a `SONOS_PLAYER` connects to the network:
  - `ETHERNET_ROOT` / `ETHERNET_NODE`: Wired `100FD` RJ45 connection to `VLAN 10` (`Wohnzimmer_Bookshelf` at `.230` is the designated `STP Root Bridge`).
  - `SONOSNET_MODE`: Dedicated 2.4 GHz Channel 6 (`2437 MHz`, 20 MHz) 802.11n mesh tunnel.
  - `STATION_MODE`: Direct connection as a standard Wi-Fi client to `WuTangLan-Family` (preferring 5 GHz Ch 44/40 for isolated rooms like `Nicolas`).
  - `HT_SATELLITE`: Dedicated 5 GHz Channel 48 (`5240 MHz`) low-latency bond from `Fernsehecke Beam` to surround speakers (`LR` / `RR`).
- **`OfdmAniLevel`**: The Atheros Rincon `OFDM Adaptive Noise Immunity` level (`0` to `9`) read from `/status/proc/ath_rincon/status`. Measures how aggressively the radio must desensitize its receiver against non-Wi-Fi noise (`0–3` Clean, `4–6` Moderate, `7–9` Severe).
- **`PhyErrorRate`**: The first derivative (`errors/sec`) of `PHY errors since last reading/reset` across consecutive polls of `/status/proc/ath_rincon/status`. Distinguishes active live RF corruption (`>100 err/s`) from stale historical counters (`0.0 err/s`).
- **`SonosMeshLink`**: A directed wireless link between two `SONOS_PLAYER` nodes, carrying inbound SNR (`FromDb`), outbound SNR (`ToDb`), and STP port state (`FORWARDING` `03`/`04` vs. `BLOCKING` `00`).
- **`StpPathCost`**: The Spanning Tree Protocol cost (`showstp`) from a `SONOS_PLAYER` back to the `DesignatedRoot` (`9000.542a1b63fe6e`). Wired = `0` (Root) or `10`; healthy direct wireless hop = `200–300`; multi-hop detour = `> 450`.
- **`GhostGroup`**: An orphaned Sonos S2 `ZoneGroup` state where the `GroupID` prefix (`RINCON_<OriginatingUUID>:<Counter>`) no longer matches the active `Coordinator` UUID after the originating host room was unchecked mid-stream, causing Spotify/cloud `"Couldn't play content"` errors and `HTTP 500` join failures.
- **`DpcDucking`**: Sonos *Dynamic Packet Concealment*, which smoothly attenuates (ducks) and restores speaker volume when 2.4 GHz airtime saturation or multi-hop STP latency causes jitter-buffer underruns.
- **`SonosTelemetrySnapshot`**: A timestamped record of a player's `ConnectionMode`, `OfdmAniLevel`, `NoiseFloorDbm`, `PhyErrorTotal`, `PhyErrorRate`, `DesignatedRoot`, `StpPathCost`, `GroupId`, `CoordinatorUuid`, `IsGhostGroup`, `MasterVolume`, and `PingRttMs`.

---

## 4. Unified Graph & Diagnostic Engine Domain

- **`DeviceConnectionEdge`**: A normalized directed edge in the house network graph connecting a `SourceDevice` to a `TargetDevice` across one of three layers:
  - `WIRED_LAN` (Router ➔ Switch ➔ APs / Wired Sonos / Mini PC)
  - `WIFI_INFRA` (AP Radio ➔ Wi-Fi Client / `STATION_MODE` Sonos)
  - `SONOS_MESH` (STP Root ➔ `SONOSNET_MODE` Tunnels & `5 GHz HT_SATELLITE` Bonds)
- **`HealthGrade`**: Standardized 4-tier status used across all rooms, links, and radios:
  - `EXCELLENT` (Dark Green)
  - `GOOD` (Green)
  - `MARGINAL` (Yellow)
  - `CRITICAL` (Red)
- **`RoomDiagnostic`**: An automated root-cause finding generated by the `DiagnosticEngine` for a `Room` or `NetworkDevice`, specifying `Layer` (`WIFI` | `SONOS` | `WIRED`), `Severity` (`HealthGrade`), `RuleCode` (e.g., `EMI_NON_WIFI_SPIKE`, `STP_MULTIHOP_DETOUR`, `WIFI_WEAK_COVERAGE`, `CO_CHANNEL_CONTENTION`, `GHOST_GROUP_MISMATCH`), evidence metrics, and a ranked list of `SolutionProposal` items.
- **`SolutionProposal`**: A concrete, ranked remediation step attached to a `RoomDiagnostic`—either an automated `OneClickAction` (`FLUSH_GHOST_GROUPS`, `RUN_PHY_VELOCITY_TEST`, `RUN_PING_JITTER_SWEEP`) or a guided physical action (e.g., *"Patch Nicolas SYMFONISK to Wall Jack Port 5 (VLAN 10)"*, *"Power-cycle leaf speaker for 10s to renegotiate direct STP tunnel"*).

---

## 5. Mobile & Android Scanner Domain

- **`OfflineSurveyQueue`**: An Android Room SQLite store-and-forward queue caching captured `WiFiRoomSurvey` payloads during dead-zone room walks (e.g., thick concrete walls or basement), automatically synchronizing with `POST /api/rooms/{slug}/surveys` upon network reconnection.
- **`DualEndpointMode`**: Client networking architecture supporting automatic or manual switching between Local LAN (`http://192.168.55.60:8001`) and Firewalla WireGuard VPN (`http://minipc:8001`), with runtime transport detection that pauses local 802.11 room scanning while keeping live health telemetry and 1-click UPnP actions active when connected remotely.
- **`SingleShotProbe`**: A foreground 2-sample 802.11 burst probe (spaced 1.5s) triggered on user tap, calculating 802.11 band, channel frequency, and channel width while strictly respecting Android 10+ scan throttling (4 scans per 2 minutes per foreground app) without requiring developer mode throttling bypasses.
- **`DualViewTopology`**: Touch-optimized mobile representation providing a 1-tap toggle between **Floor Accordion Cards** (collapsible cards tailored for vertical one-handed mobile use) and **Pinch-to-Zoom Pan Canvas** (vector canvas rendering device nodes and active/blocked STP links).

