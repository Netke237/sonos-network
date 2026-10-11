# ADR-0004: Dual Topology Graph & Deterministic Rule-Based Diagnostic Engine

- **Status:** Accepted
- **Date:** 2026-10-11

## Context

A raw table of IP addresses, MACs, and dBm numbers makes it difficult to see at a glance:
- Which rooms have weak 5 GHz or 2.4 GHz Wi-Fi coverage or co-channel neighbor contention.
- How Sonos players route through the Spanning Tree (`Wohnzimmer_Bookshelf` Root Bridge vs. multi-hop wireless detours vs. 5 GHz Home Theater satellites vs. 5 GHz Wi-Fi Station nodes).
- Why a specific room is experiencing audio dropouts, DPC volume ducking, or `"Couldn't play content"` errors—and what exact fix resolves it.

## Decision

1. **Dual Visual Representations**:
   - **Floor & Room Coverage Matrix**: Rooms grouped by `Floor` (`Dachgeschoss`, `Obergeschoss`, `Erdgeschoss`, `Keller`), displaying side-by-side **Wi-Fi Status** (5 GHz & 2.4 GHz `RssiDbm` per AP, rogue/neighbor conflicts), **Sonos Status** (`ConnectionMode`, `OfdmAniLevel`, `PhyErrorRate`, `StpPathCost`, `PingRttMs`), **Wired Status** (`SwitchPort` VLAN 10 availability), and active `RoomDiagnostic` alerts.
   - **Interactive Network Topology Graph (React Flow)**: Renders `NetworkDevice` nodes and `DeviceConnectionEdge` links with layer toggles for **Wi-Fi Infrastructure Layer**, **Sonos Mesh & STP Layer** (showing active `FORWARDING` vs. dashed `BLOCKING` links weighted by `FROM/TO dB` SNR), and **Unified End-to-End View**.
2. **Deterministic `DiagnosticEngine` & `SolutionProposal` Generator**:
   - Evaluates live and survey data against explicit engineering rules (`GHOST_GROUP_MISMATCH`, `BASEMENT_ROOT_TRAP`, `STP_MULTIHOP_DETOUR`, `EMI_NON_WIFI_SPIKE`, `SONOSNET_AIRTIME_SATURATION`, `WIFI_WEAK_COVERAGE`, `CO_CHANNEL_CONTENTION`, `ROGUE_TRANSMITTER_DETECTED`).
   - Produces ranked `SolutionProposal` items per room, exposing safe 1-click UPnP/diagnostic actions (`Flush Ghost Groups`, `Run 10s PHY Error Velocity Test`, `Run Room Ping/Jitter Sweep`) directly in the UI.

## Consequences

- **Positive**: Turns complex multi-layer RF and STP data into an intuitive visual map and self-service troubleshooting workflow; allows adding new rooms and devices dynamically without hardcoding room names in the diagnostic rules.
- **Negative / Trade-offs**: Frontend graph layout must automatically position newly added rooms and devices cleanly when custom coordinates are not yet set.
