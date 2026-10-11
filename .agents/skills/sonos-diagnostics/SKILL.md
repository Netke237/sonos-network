---
name: sonos-diagnostics
description: >-
  Diagnose and remediate Sonos playback failures, "Couldn't play content" cloud errors,
  Ghost Group ID mismatches, stuttering/dropouts, volume fluctuations (DPC ducking),
  STP mesh routing detours, and RF interference across the 14-player system.
---

# Sonos Live Diagnostics & Remediation Runbook

Execute this runbook whenever diagnosing playback failures, room grouping errors, audio dropouts, or RF degradation on the 14-player Sonos system (`192.168.10.0/24`, VLAN 10).

---

## 1. Diagnostic Branches (Select by Symptom)

### Branch A: "Couldn't play content" / Track Halts at `0:00` / Cannot Add Rooms to Group
**Root Mechanism — Ghost Group ID Collision:**
In Sonos S2 (`86.8-78270`), unchecking the originating host room while streaming leaves the remaining speakers bound to the departed room's Group ID prefix (`<Originating-UUID>:<Counter>`). Cloud services (Spotify, Apple Music) verify that the active Coordinator UUID matches the Group ID prefix; on mismatch, the cloud token handshake aborts at `0:00` with `"Couldn't play content"` or rejects UPnP group joins (`HTTP 500`).

**Steps:**
1. **Audit & Flush Ghost Groups**:
   Run the repository sanitizer script:
   ```powershell
   python f:\Git\GitHub\Sonos\scripts\reset_sonos_groups.py --all
   ```
   *(Sends `AVTransport:1#BecomeCoordinatorOfStandaloneGroup` to all 12 zones in parallel, forcing each player to generate a clean Group ID anchored to its own hardware UUID).*
2. **Verify Clean Topology**:
   Query `ZoneGroupTopology:1#GetZoneGroupState` on `192.168.10.230:1400`. Confirm every `<ZoneGroup>` has `ID` prefix matching its `Coordinator` attribute and `<VanishedDevices>` is empty.
3. **Completion Criterion**: Every active zone reports `CLEAN` with matching `GroupID` and `Coordinator` UUID.

---

### Branch B: Audio Stuttering, Dropouts, or "Volume Fluctuations" During Grouping
**Root Mechanisms:**
1. **2.4 GHz Airtime Saturation & DPC Ducking**: When 10+ wireless speakers stream uncompressed audio over 2.4 GHz Channel 6 (20 MHz), multi-hop relays saturate airtime (pings rise to 350–600 ms). When a receiver's jitter buffer underruns, Sonos **Dynamic Packet Concealment (DPC)** smoothly attenuates (ducks) and restores volume to mask missing frames—heard as "volume fluctuations".
2. **STP Topology Change Notification (TCN)**: When a central wireless node (e.g., `Noemi`) joins and opens 6–8 forwarding tunnels, the mesh pauses forwarding for 2–4 seconds while ports transition from `LEARNING` to `FORWARDING`.
3. **STP Path Cost Detours**: A wireless leaf (e.g., `Küche` or `Noemi`) may block its direct link to the Root Bridge and route through a multi-hop bedroom or surround satellite (Path Cost > 500), causing >3,000 ms ping spikes.
4. **Master Volume Disparity**: Individual room sliders set to wildly different values (e.g., `Noemi` at 48 vs `Wohnzimmer` at 15).

**Steps:**
1. **Inspect Atheros Radio & SNR Matrix**:
   Run the real-time telemetry monitor (or `--watch 5` for live PHY error rate delta):
   ```powershell
   python f:\Git\GitHub\Sonos\tools\sonos_monitor.py
   ```
   Fetch `http://<player-ip>:1400/status/proc/ath_rincon/status` across all players:
   - Check `OFDM ANI level` (`0–3` Clean, `4–6` Moderate, `7–9` High non-Wi-Fi noise).
   - Check `PHY errors since last reading/reset`.
   - Check `Node <MAC> - FROM <in_snr> : TO <out_snr> : STP <state>` (`03`/`04` = Forwarding, `00` = Blocking).
2. **Inspect Spanning Tree Routing (`showstp`)**:
   Fetch `http://<player-ip>:1400/status/showstp`:
   - Verify `designated root` is **`9000.542a1b63fe6e`** (`Wohnzimmer_Bookshelf`, `192.168.10.230`).
   - Check `root port` and `path cost`. Healthy direct hop is `200–300`. Path cost `> 500` indicates a multi-hop detour (e.g., routing via `Noah` or `Fernsehecke LR`).
   - **Fix for STP Detour**: Power-cycle the affected leaf speaker (10s unplug) so it renegotiates a direct tunnel to `Wohnzimmer_Bookshelf`.
3. **Audit Master Volumes**:
   Query `RenderingControl:1#GetVolume` (`Channel: Master`) across all rooms to identify volume slider disparities.
4. **Completion Criterion**: Root Bridge confirmed as `9000.542a1b63fe6e`, offending leaf path cost reduced or documented, and volume levels reported.

---

### Branch C: Evaluating Wi-Fi Station Mode vs SonosNet vs Ethernet
**Rule:**
- **Wired Ethernet (100FD)** is the gold standard (Cost 10, <1 ms RTT, 0 RF airtime).
- **5 GHz Wi-Fi Station Mode** (`WuTangLan-Family` on Galerie AP Ch 44 @ 80 MHz) is vastly superior to 2.4 GHz SonosNet for isolated rooms (such as `Nicolas` in the attic, where 5 GHz delivers ANI 0 and 2.3 ms ping vs SonosNet's ANI 5 and ~5M PHY errors).
- **Never wire `Keller` (`192.168.10.217`)** unless its Wi-Fi radio is disabled or STP priority is overridden; wiring Keller forces the STP Root Bridge into the concrete basement (0 dB SNR to upper floors).

---

### Branch D: Offline Player Discovery, Cross-VLAN Subnet Sweep & Factory Reset
**Steps:**
1. **Check Peer Mesh Tables for Offline Node**:
   Query `/status/proc/ath_rincon/status` on active nodes (e.g., `192.168.10.230`). If the target BSSID shows `Node <MAC> - FROM 00 : TO 00 : STP 00`, the player is registered in the household but currently offline/unreachable over RF.
2. **Sweep `192.168.10.0/24` on TCP Port 1400 (Cross-VLAN Safe Parameters)**:
   When scanning VLAN 10 from the Admin VLAN (`192.168.55.198`) across the Firewalla Purple router, **keep `max_workers <= 20` and socket `timeout >= 1.2s`**. High-concurrency bursts (`50+` workers at `0.5s` timeout) trigger inter-VLAN rate-limiting and false-negative timeouts.
3. **SYMFONISK Hardware Factory Reset & Wired Onboarding**:
   - Unplug power cable, press and hold **Play/Pause**, and reconnect power while holding until the LED flashes **amber/white**, then release (LED turns **flashing green** after 15–30s).
   - Connect RJ45 Ethernet to an untagged **VLAN 10** wall port (with switch **BPDU Guard disabled**) and adopt in the Sonos app on `WuTangLan-Family`.

---

### Branch E: High Interference (`OFDM ANI 7–9`) When Wi-Fi Channel 6 is Empty
**Root Mechanism — Non-Wi-Fi Electromagnetic Leakage (EMI):**
Wi-Fi scanners (NetX Inspector) only decode `802.11` beacons and are blind to non-Wi-Fi 2.4 GHz noise. When a speaker logs high `OFDM ANI` (`7–9`) and rapid `PHY errors` while Channel 6 shows zero Wi-Fi networks, the culprit is local non-Wi-Fi EMI—specifically **USB 3.0 / USB-C docks** (whose 5 Gbps data clock radiates broadband noise across `2.40–2.50 GHz`), switching power bricks, or workstation equipment located directly above (`Galerie` desk 2m above `Wohnzimmer_Buchregal` `.101`).

**Steps:**
1. **Run Real-Time PHY Error Velocity Monitor**:
   Instead of opening `/support/review` in a browser on a wireless speaker (which times out polling 14 nodes over 2.4 GHz or renders blank due to Chromium XSLT blocking), run the local CLI monitor from the PC (`192.168.55.198`):
   ```powershell
   python f:\Git\GitHub\Sonos\tools\sonos_monitor.py --room Wohnzimmer --watch 3
   ```
2. **Sequential Isolation Test**:
   Observe the `Error Rate (err/s)` column while sequentially unplugging candidate EMI sources (USB-C dock, monitor power bricks, power strips) or moving the speaker 1–2m laterally.
3. **Completion Criterion**: `Error Rate` drops from `>100 err/s` toward `0.0 err/s` and `OFDM ANI` decays toward `0–4`.

---

## 2. Live HTTP / UPnP Reference Endpoints (Port 1400)

| Diagnostic Target | Endpoint / SOAP Action | Key Fields |
|---|---|---|
| **Full Support Matrix** | `GET http://192.168.10.230:1400/support/review` | XML containing all 14 players' `ZPInfo`, `ath_rincon`, and `showstp` *(use 30s timeout)* |
| **Local Radio & SNR** | `GET http://<ip>:1400/status/proc/ath_rincon/status` | `Mode`, `IEEE channel`, `Noise Floor`, `PHY errors`, `OFDM ANI level`, `Node` matrix |
| **Local STP Table** | `GET http://<ip>:1400/status/showstp` | `bridge id`, `designated root`, `root port`, `path cost`, `tunnel to <MAC>` |
| **Connection Mode** | `GET http://<ip>:1400/status/wireless` | `WifiModeString` (`SONOSNET_MODE` vs `STATION_MODE`), `ConnectionTypeString` |
| **Device Identity** | `GET http://<ip>:1400/xml/device_description.xml` | `<roomName>`, `<modelName>`, `<serialNum>`, `<UDN>` |
| **Household Groups** | `POST /ZoneGroupTopology/Control`<br>`ZoneGroupTopology:1#GetZoneGroupState` | `<ZoneGroup Coordinator="..." ID="...">`, `<VanishedDevices>` |
| **Flush Ghost Group** | `POST /MediaRenderer/AVTransport/Control`<br>`AVTransport:1#BecomeCoordinatorOfStandaloneGroup` | `<NewGroupID>` anchored to player's own UUID |

---

## 3. Switch Port & VLAN Reference (`Netgear GS316EP` @ `192.168.55.155`)

- **Port 1**: Firewalla Purple Router Trunk (`VLANs 1*, 10, 20, 30`)
- **Port 5**: Nicolas Room RJ45 (`Untagged VLAN 10, PVID 10`)
- **Port 6**: Noemi Room RJ45 (`Untagged VLAN 10, PVID 10`)
- **Port 7**: Noah Room RJ45 (`Untagged VLAN 10, PVID 10`)
- **Port 8**: Spare / Ground Floor (`Untagged VLAN 10, PVID 10`)
- **Port 11, 12, 14, 15**: TP-Link EAP650 Access Point Trunks (`VLANs 1*, 10, 20, 30`)
- **Port 13**: Living Room / `Wohnzimmer_Bookshelf` (`Untagged VLAN 10, PVID 10`)

### Multi-Wired Sonos STP Requirements (`Netgear GS316EP`)
When multiple Sonos players are wired simultaneously (e.g., Port 13 `Wohnzimmer_Bookshelf` + Port 5/6/7 bedrooms):
- **Switch Bridge Priority**: `4096` (places the switch deterministically above Sonos `36864` / `0x9000` root election)
- **STP Mode**: `802.1D` Classic STP (or RSTP configured with **16-bit Short Path Cost** to match Sonos BPDU path costs)
- **BPDU Handling**: **BPDU Flooding / Pass-Through Enabled**; **BPDU Guard Disabled** on all Sonos ports (Ports 5, 6, 7, 8, 13)
