# ADR-0002: Multi-Source Network Telemetry Adapters Behind Deep Seams

- **Status:** Accepted
- **Date:** 2026-10-11

## Context

Accurately diagnosing room-level connectivity and interference requires correlating three distinct network layers:
1. **Sonos Layer (`VLAN 10`, `192.168.10.0/24:1400`)**: Atheros Rincon RF metrics (`OFDM ANI`, `Noise Floor`, `PHY err/s`), 14×14 peer SNR (`FROM/TO dB`), STP topology (`showstp`), connection mode (`wireless`, `enetports`), volume, and UPnP `ZoneGroupTopology`.
2. **Wi-Fi / Access Point Layer (`VLAN 1`, Omada Controller `:8043`)**: Access point radio status (`Galerie EAP650`, `Kitchen EAP650`), channel utilization, and connected client BSSID/RSSI (`dBm`)/link rates (`Mbps`).
3. **Wired Switch / L3 Reachability Layer (`192.168.55.155` & ICMP)**: Switch port mappings (Ports 1–16, untagged VLAN 10 wall jacks in rooms) and ICMP round-trip latency / packet loss under load.

Cross-VLAN scanning from `192.168.55.x` (`Admin`) to `192.168.10.x` (`WuTangLan-Family`) traverses the Firewalla Purple router, which rate-limits aggressive burst scans (`>20` concurrent workers at `<1.0s` timeout).

## Decision

1. **Three Telemetry Adapters with In-Memory Test Fakes**:
   - `SonosTelemetryAdapter`: Polls all 14 players on port `1400` using cross-VLAN-safe concurrency (`max_workers <= 14`, `timeout >= 2.0s`), computing live `PhyErrorRate` (`err/s`) across consecutive polls and parsing `ath_rincon`, `showstp`, `wireless`, `enetports`, and `ZoneGroupTopology`.
   - `OmadaControllerAdapter`: Connects to the local Omada Software Controller on the Mini PC (`https://192.168.55.60:8043`) to fetch live `AccessPointRadio` metrics and client Wi-Fi associations (`BSSID`, `RssiDbm`, `LinkSpeedMbps`). Degrades gracefully when Omada is unreachable or re-provisioning.
   - `NetworkProbeAdapter`: Executes bounded concurrent ICMP ping/jitter sweeps and resolves `SwitchPort` room mappings.
2. **Seam Discipline**: Each adapter implements a narrow protocol interface injected into the `TelemetryCollector` and `DiagnosticEngine`, allowing 100% deterministic unit and integration testing using recorded fixture payloads without requiring live hardware during CI tests.

## Consequences

- **Positive**: High testability at the module seam; zero cross-VLAN Firewalla rate-limiting false negatives; complete L1/L2/L3 correlation per room.
- **Negative / Trade-offs**: Adapter parsers must handle firmware-specific XML/text formatting from Sonos S2 (`86.8-78270`) and Omada Controller API versions.
