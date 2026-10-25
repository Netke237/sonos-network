# Sonos & Home Network Repository Guidelines

Documentation and engineering analysis repository for a residential network and 14-player Sonos system. Grounded in Wi-Fi inspector captures, Omada controller diagnostics, and live Sonos UPnP / Atheros driver telemetry.

---

## 1. Project Purpose & Architecture

- **Primary Goal**: Diagnose and stabilize the home Wi-Fi/VLAN environment and the 14-player Sonos sound system.
- **Physical Topology**:
  ```
  Fritzbox 6660 Cable  -->  Firewalla Purple  -->  Netgear GS316EP (192.168.55.155)  -->  TP-Link EAP650 APs (Ports 11,12,14,15)
  (Wi-Fi Disabled)          (VLAN Router)          (BPDU Pass-Through)                    Wohnzimmer_Bookshelf (Port 13, Wired Root)
                                                                                          Room Wall Jacks (Port 5 Nicolas, Port 6 Noemi, Port 7 Noah)
  ```
- **VLAN Segmentation**:
  - `Admin` (`192.168.55.0/24`, VLAN 1 — Management, Switch, Omada, PC at `.198`)
  - `WuTangLan-Family` (`192.168.10.0/24`, VLAN 10 — Trusted devices + all 14 Sonos players)
  - `WuTangLan-Guest` (VLAN 20 — Guest network)
  - `WuTangLan-IOT` (VLAN 30 — Smart home / IoT devices)
- **Wi-Fi Infrastructure (Sanitized Oct 2026)**:
  - **Galerie AP** (`EAP650`, `...:76:7C:40/41`): 2.4 GHz **Ch 1** (20 MHz) & 5 GHz **Ch 44** (80 MHz, non-DFS). Carries primary house coverage at up to 1201 Mbps.
  - **Kitchen AP** (`EAP650`, `...:76:94:C0/C1`): 2.4 GHz **Ch 11** (20 MHz) & 5 GHz **Ch 40** (40 MHz).
  - **Retired / Disabled Interference**: Standalone `EAP330` (`TP-Link_5G_93E92D`) is powered off; `Keller AP` is powered off; `Fritzbox 6660` rogue Wi-Fi is disabled; `Epson ET-4850` Wi-Fi Direct (`-42 dBm` on Ch 11) is disabled.
- **Sonos System (14 Players on VLAN 10, Build `86.8-78270`)**:
  - **Wired STP Root Bridge**: `Wohnzimmer_Bookshelf` (`192.168.10.230`, `9000.542a1b63fe6e`, Cost 0).
  - **Basement Leaf**: `Keller` Play:3 (`192.168.10.217`) is **unplugged from Ethernet** to prevent the basement root-bridge trap (0 dB SNR to upper floors) and operates as a wireless leaf.
  - **Living Room Disambiguation**: The three living room units are uniquely named `Wohnzimmer_Bookshelf` (`.230`), `Wohnzimmer_Esstisch` (`.160`), and `Wohnzimmer_Buchregal` (`.101`) to prevent UI grouping collisions.

---

## 2. Documentation & Skill Map (Context Pointers)

Load the specific target when addressing tasks:

| Topic / Trigger | Target File | Summary |
|---|---|---|
| **Live Sonos Diagnostics, "Couldn't play content", Stuttering, Volume Ducking** | [`.agents/skills/sonos-diagnostics/SKILL.md`](.agents/skills/sonos-diagnostics/SKILL.md) | Runbook for UPnP Ghost Group flushing, Atheros `ath_rincon` SNR/ANI probes, `showstp` path cost audits, and DPC volume ducking |
| **Real-Time RF & ANI Telemetry Monitor** | [`tools/sonos_monitor.py`](tools/sonos_monitor.py) | CLI monitor (`--watch`, `--room`) polling all players for live `OFDM ANI`, `Noise Floor`, and `PHY err/s` rates |
| **Ghost Group Sanitizer Script** | [`scripts/reset_sonos_groups.py`](scripts/reset_sonos_groups.py) | 1-click parallel UPnP `BecomeCoordinatorOfStandaloneGroup` reset across all 12 zones |
| **Sonos IP/MAC/UUID Inventory** | [`docs/sonos/devices.md`](docs/sonos/devices.md)<br>[`docs/sonos/network-matrix.md`](docs/sonos/network-matrix.md) | Complete 14-player IP, MAC, BSSID, RINCON UUID, and STP role map |
| **Room-by-Room RF & Wi-Fi Audit** | [`docs/network-availability-by-room.md`](docs/network-availability-by-room.md) | Consolidated October 2026 Wi-Fi 6 RSSI, SonosNet ANI, and Ethernet availability per room |
| **Per-Room NetX Scan Logs** | [`docs/wifi/<room>.md`](docs/wifi/) | Detailed NetX Inspector captures per room (`nicolas.md`, `wohnzimmer.md`, `kueche.md`, etc.) |
| **Wi-Fi & AP Inventory** | [`docs/wifi/01-access-points.md`](docs/wifi/01-access-points.md) | BSSIDs, SSIDs, channels, radio models, and Omada controller status |
| **Remediation & Engineer Brief** | [`docs/10-assessment-and-recommendations.md`](docs/10-assessment-and-recommendations.md)<br>[`docs/20-engineer-brief.md`](docs/20-engineer-brief.md) | Historical root-cause analysis, channel plans, and hand-over brief |

---

## 3. Working Principles & Domain Invariants

### Evidence-First Rule
- Every technical assertion (signal in dBm, channel width, MAC/IP, BSSID, OFDM ANI, PHY error rate, STP path cost, Group ID) **must be grounded in live telemetry or recorded captures**. Mark unverified claims as **`unverified`**.
- **Multi-Wave Upload Protocol**: When the user announces a multi-batch screenshot upload, **only acknowledge receipt and do not analyze or interpret** until the user explicitly confirms all uploads are complete.
- **L3 Router vs. L2 AP Attribution**: Never infer which Wi-Fi AP a device is connected to from its IP address or Firewalla's `LAN Port` uplink view (DHCP pools are shared across all APs per VLAN). Always verify BSSID/AP association via the **Omada Controller `Clients` view**.

### Domain Invariants
- **2.4 GHz Spectrum Plan**: Always **20 MHz** width. Galerie AP = **Ch 1**, SonosNet = **Ch 6**, Kitchen AP = **Ch 11**.
- **5 GHz Non-DFS Invariant**: Keep Galerie AP 5 GHz pinned to Non-DFS **Channel 44** (80 MHz, UNII-1) and Kitchen AP on **Channel 40** (40 MHz). Do not revert to DFS **Channel 100**, which suffers persistent ETSI radar/CAC lockouts and Android passive-scan suppression in this environment.
- **STP Root Bridge Invariant**: `Wohnzimmer_Bookshelf` (`192.168.10.230`) must remain the wired STP Root Bridge. Do not wire `Keller` (`192.168.10.217`) without disabling its wireless bridge or overriding STP priority.
- **Ghost Group ID Invariant**: In Sonos S2, unchecking an originating host room while streaming leaves remaining rooms bound to the departed host's Group ID prefix (`<Originating-UUID>:<Counter>`), causing Spotify/cloud `"Couldn't play content"` errors and `HTTP 500` join failures. Flush via [`scripts/reset_sonos_groups.py`](scripts/reset_sonos_groups.py) (`BecomeCoordinatorOfStandaloneGroup`) and always initiate new groups from a stopped state on the target coordinator.
- **2.4 GHz Airtime Ceiling & 5 GHz Offload**: Streaming to 10+ wireless nodes on 2.4 GHz Ch 6 saturates airtime, triggering Sonos **Dynamic Packet Concealment (DPC)** volume ducking. Isolated rooms (`Nicolas` in the attic) perform 300x cleaner on **5 GHz Wi-Fi (`WuTangLan-Family` Ch 44)** or **Wired Ethernet (Switch Ports 5, 6, 7 — Untagged VLAN 10)**.

### Conventions & Style
- **Room Naming**: Preserve exact zone designations: `Wohnzimmer_Bookshelf`, `Wohnzimmer_Esstisch`, `Wohnzimmer_Buchregal`, `Galerie`, `Elternschlafzimmer`, `Elternbad`, `Eltern`, `Noemi`, `Noah`, `Nicolas`, `Büroecke`, `Fernsehecke`, `Küche`, `Keller`.
- **Preserve Documentation Integrity**: Retain historical baseline scans alongside dated post-remediation updates.

---

## Agent skills

### Issue tracker

GitHub Issues on `Netke237/sonos-network` (public), via `gh`. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context (`GLOSSARY.md` + `docs/adr/` at the repo root). See `docs/agents/domain.md`.

### Ticket orchestration & Board Worker

Multi-ticket builds and board items are coordinated through `k-ticket-coordinator` and `k-board-worker` against GitHub Issues. See `docs/agents/ticket-orchestration.md`, `docs/agents/board.md`, and `docs/agents/agent-briefs.md`.

<!-- k-session-reconciliation:begin -->
## Session handoff (all agents)

This repo uses a model-agnostic handoff protocol so an interrupted task can be
continued by any agent, user or container.

- **Before doing anything**, if `.k-session/K-SESSION.md` exists on your branch:
  run `python3 .k-session/k_session.py resume`, read `.k-session/K-SESSION.md`,
  summarize goal / done / next steps / blockers to the user and **wait for
  confirmation** before continuing.
- While working: keep `.k-session/K-SESSION.md` current and run
  `python3 .k-session/k_session.py checkpoint -m "<what changed>"` after each
  meaningful step (it commits WIP and pushes).
- Before stopping: update K-SESSION.md, then `python3 .k-session/k_session.py release`.
- Never write secrets, emails, personal names, absolute container paths or
  chat transcripts into `.k-session/`. Use repo-relative paths.
- Follow the *Conventions* section of K-SESSION.md regardless of which model you are.
- When the task is complete: `python3 .k-session/k_session.py finish`.
<!-- k-session-reconciliation:end -->
