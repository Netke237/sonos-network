# Engineer brief — home Wi-Fi and Sonos

**Purpose.** Hand-over for an engineer asked to stabilise (1) the Wi-Fi/VLAN network and
(2) the Sonos system in this house. Everything below is either **measured** (with the source
file in this repo) or explicitly marked **not verified**.

**Evidence window.** 19 Sep 2026 evening → 21 Sep 2026 evening.

| Source | When | What |
|---|---|---|
| `Netlog_*.jpg` (9 rooms) | **19 Sep**, 19:42–21:14 | Wi-Fi scans (Android, NetSpot/Network Analyzer "Inspector") |
| `Sonos Network.jpg` | **19 Sep**, 21:44 / 22:17 / 22:35 | Sonos `/support/review` Network Matrix, 3 identical captures |
| `Keller/`, `Fernsehecke/`, `küche_2/`, `Büroecke/` | **20 Sep**, 22:01–22:46 | Wi-Fi scans, full resolution |
| `omada/` | **21 Sep**, 08:12 and 19:02 | Omada controller + EAP330 standalone UI (photos of screen) |
| `Kücke_3/` | **21 Sep**, 21:57–21:58 | Wi-Fi re-scan of the kitchen |

All scans were taken with `Wi-Fi throttling ON` (Android scan rate limit). "Offline" in a scan
means *the phone did not hear it in recent scans*, not that the device was down.

---

## 0. Summary

**Both problems share one root cause: the 2.4 GHz band is saturated and uncoordinated.**
SonosNet runs on a single fixed 2.4 GHz channel, so it is the first thing to fail.

- **Wi-Fi:** of four access points, one is powered off, one is unmanaged and unused, and the
  remaining two managed EAP650s have been moved by auto-channel onto the **same channel on both
  bands** (2.4 GHz ch 6, 5 GHz ch 100). Omada shows 2.4 GHz ch 6 **near saturation** and 5 GHz
  ch 100 **idle**. The ISP router (Fritzbox 6660) still broadcasts its own SSID with a
  **40 MHz channel on 2.4 GHz**; clients fall back onto it and **bypass the VLAN design**.
  The Kitchen AP is **not audible in the kitchen** on two separate evenings.
- **Sonos:** SonosNet is **three hops deep** (1 root, 1 secondary, 11 tertiary), the only root
  bridge is in the **basement next to the Fritzbox**, **five players show heavy interference
  mitigation** (OFDM ANI 6–9), strong links sit in **STP blocking**, one allegedly wired player
  (Noemi) is **not acting as wired**, and two players are **not on SonosNet at all**.

---

## 1. Environment

### 1.1 Topology (as described by the owner)

```
[Cable] → Fritzbox 6660 Cable → Firewalla Purple → Netgear switch → TP-Link EAPs
                                                                   (VLANs per SSID)
```

- **Fritzbox role not documented** (router vs. bridge / exposed host). Its Wi-Fi is **on**.
- **Firewalla Purple:** config not captured (VLAN interfaces, mDNS/SSDP reflection, rules).
- **Netgear switch:** Confirmed **NETGEAR GS316EP** (16-Port Gigabit PoE+ Smart Managed Plus switch, IP `192.168.55.155`).
  Web GUI: `http://192.168.55.155/homepage.html`.
  *STP behavior:* Smart Managed Plus model — does not run an active 802.1D/802.1w STP engine (no bridge priority setting).
  Acts as an unmanaged BPDU forwarder/pass-through switch; Sonos handles loop prevention directly between speakers.
  *Requirements:* Switch proprietary Loop Detection must be OFF, Broadcast Filtering must be OFF. Wired Sonos ports (Port 6 Noemi, Wohnzimmer, Keller) must be Untagged VLAN 10 (PVID 10).
- **Omada controller:** *software* controller on a Windows laptop, `https://127.0.0.1:8043`,
  site `NeubibergerStr`. **Not always-on** → both APs show Health **"No Data"**.

### 1.2 Addressing (partial)

| Subnet | Use | Evidence |
|---|---|---|
| `192.168.55.0/24` | AP management | Gallery AP .79, Kitchen AP .37 (Omada) |
| `192.168.10.0/24` | Sonos (inferred = `WuTangLan-Family` VLAN) | Sonos support page at `192.168.10.229` |

Other VLAN subnets, gateway, DHCP/DNS: **not verified**.

### 1.3 Access points

| Name (Omada) | Model | MAC | IP | Managed | Firmware | Channels 19–20 Sep | Channels 21 Sep |
|---|---|---|---|---|---|---|---|
| **Gallery AP** | EAP650(EU) v1.0 | `6C:4C:BC:76:7C:40` | 192.168.55.79 | Omada | 1.3.6 *(update available)* | 11 / 44 (80 MHz) | **6 / 100** |
| **Kitchen AP** | EAP650(EU) v1.0 | `6C:4C:BC:76:94:C0` | 192.168.55.37 | Omada | 1.3.6 *(update available)* | 1 / 48 (80 MHz) | **6 / 100** |
| `EAP330-84-16-F9-93-E9-2B` | EAP330 hw 1.0/2.0 (Wi-Fi 5) | `84:16:F9:93:E9:2B` | not captured | **standalone** | **1.4.0 Build 20180925** | 6 → 11 **(40 MHz)** / 44 | — |
| Keller AP | not documented | — | — | — | — | **powered off** | **powered off** |

Channel notation `44 (42)` = primary 44, centre 42 (80 MHz). `11 (9)` on 2.4 GHz = 40 MHz.

**BSSID scheme** (useful for reading the scans):

| Device | 2.4 GHz BSSIDs | 5 GHz BSSIDs |
|---|---|---|
| Gallery AP | `72/76/7A/7E/82:4C:BC:76:7C:40` | same prefixes `…:7C:41` |
| Kitchen AP | `72/76/7A/7E/82:4C:BC:76:94:C0` | same prefixes `…:94:C1` |
| EAP330 | `84:16:F9:93:E9:2C` (hidden) + `86:16:F9:BF:E9:2D/2E/2F` | `84:16:F9:93:E9:2D` = SSID `TP-Link_5G_93E92D` |

First byte on the EAP650s → SSID: `72` Admin · `76` WuTangLan-Family · `7A` WuTangLan-Guest ·
`7E` WuTangLan-IOT · `82` hidden SSID.

### 1.4 SSIDs on air

| SSID | Broadcast by | Bands | Notes |
|---|---|---|---|
| `WuTangLan-Family` | Gallery, Kitchen, EAP330 | 2.4 + 5 (EAP330: 2.4 only) | Sonos VLAN |
| `WuTangLan-Guest` | Gallery, Kitchen, EAP330 | 2.4 + 5 (EAP330: 2.4 only) | |
| `WuTangLan-IOT` | Gallery, Kitchen, EAP330 | 2.4 + 5 (EAP330: 2.4 only) | |
| `Admin` | Gallery, Kitchen | 2.4 + 5 | purpose not documented |
| *hidden* | Gallery, Kitchen, EAP330 | 2.4 + 5 | purpose not documented |
| `TP-Link_5G_93E92D` | EAP330 | 5 | **factory SSID, never removed** |
| **`WuTangLan`** | **Fritzbox 6660** `0C:72:74:00:63:9A/9B` | 2.4 + 5 | **bypasses Firewalla/VLANs** |

→ **5 SSIDs per radio** on the EAP650s; ~30 beacon streams from own kit alone.

### 1.5 Other 2.4 GHz sources in the house

| Device | BSSID | Channel | Loudest reading |
|---|---|---|---|
| **Epson ET-4850 Wi-Fi Direct** `DIRECT-f1-EPSON-ET-4850` | `6A:55:D4:7D:0B:9B` | 11 | **-42 dBm** (Elternbad), -47 (Küche), -48 (Fernsehecke) |
| Printer Wi-Fi Direct `DIRECT-Ub7F-TS5100series` | `6E:F2:D8:E7:FA:7F` | 1 / 11 | -74 … -83 dBm |
| 5 × Tapo bulbs | `0C:EF:15:5E:…` | 6 | -52 dBm (Galerie) … -96 |
| Huawei SUN2000 inverter | `C4:69:F0:A9:B0:17` | 1 | |
| FRITZ!Box 7490 | `38:10:D5:BA:88:B3/B4` | 6 / 40 (42) | ownership **not verified** |
| `WLAN-A7C604` (Fritz repeaters, 3 BSSIDs) | `1C:23:A2:7A:E3:7A/7B`, `38:10:D5:8B:10:56/57` | 1 or 6 / 52 | ownership **not verified** |
| Neighbours: Vodafone-DD14 / Hotspot / Homespot, FRITZ!Box 6660 Cable EV | `DC:A6:33:43:EC:…`, `1C:ED:6F:09:35:22/23` | 1 / 11 / 52–116 | |

---

## 2. Issue 1 — Wi-Fi / VLAN network

### 2.1 Symptoms

- No room reaches "dark green"; best own-AP reading anywhere is **-50 to -52 dBm**.
- Client in the kitchen loses internet on `WuTangLan-Family`, drops Wi-Fi, then re-associates
  to the **Fritzbox** SSID `WuTangLan` (21 Sep 21:57–21:58, phone status bar + scanner banner).

### 2.2 Coverage per room (best own AP; 2.4 GHz / 5 GHz, dBm)

| Room | Best own AP | 2.4 GHz | 5 GHz | Loudest signal in room | Date |
|---|---|---|---|---|---|
| Wohnzimmer | Gallery | -52 | -55 | Gallery AP | 19 Sep |
| Büroecke | Gallery | -52 | -54 | Gallery AP | 20 Sep |
| Galerie | Gallery | -53 | -53 | Tapo bulb -52 | 19 Sep |
| Fernsehecke | Gallery | -55 | -53 | **Fritzbox -40** | 20 Sep |
| Elternbad | Gallery | -56 | -50 | **Epson -42** | 19 Sep |
| Noemi | Gallery | -56 | -59 | Gallery AP | 19 Sep |
| Elternschlafzimmer | Gallery | -57 | -54 | Gallery AP | 19 Sep |
| **Küche** | **Gallery** | -60 / -57 | -55 / -63 | **Epson -47** | 20 / 21 Sep |
| Noah | Gallery | **none live** | -61 | Gallery AP | 19 Sep |
| Keller *(AP off)* | Kitchen | -63 | -68 | **Fritzbox -39** | 20 Sep |
| Nicolas | EAP330 / Gallery | -64 | -70 | EAP330 -55 | 19 Sep |

**The Gallery AP is the strongest own AP in 9 of 11 rooms**, including the kitchen.
Target for comparison: a room containing an AP should read -35 to -45 dBm.

### 2.3 Findings

| # | Severity | Finding | Evidence |
|---|---|---|---|
| W1 | 🔴 critical | **Both EAP650s co-channel on both bands** (2.4 ch 6, 5 GHz ch 100) as of 21 Sep. On 20 Sep they were 11/44 and 1/48 → Omada auto-channel merged them within ~21 h. | `omada/IMG_…190249`, `…190320`; `Keller/`, `Fernsehecke/`, `Büroecke/` |
| W2 | 🔴 critical | **2.4 GHz ch 6 utilisation near saturation** on both APs (Kitchen AP bar almost full); **5 GHz ch 100 idle**. | Omada Channel Utilization widgets |
| W3 | 🔴 critical | **Fritzbox 6660 Wi-Fi active**: SSID `WuTangLan`, 2.4 GHz **ch 11 at 40 MHz** (-39 dBm in Keller), 5 GHz on auto (ch 36 @ 160 MHz on 19 Sep, ch 116 @ 80 MHz on 20 Sep). Clients associate to it: 2401 Mbps (Nicolas, 19 Sep), 573 Mbps (Küche, 21 Sep). **Bypasses Firewalla and VLAN segmentation.** Radios were not heard between ~22:05 on 20 Sep and 21 Sep, but were back on by 21:58 on 21 Sep. | `Keller/`, `Fernsehecke/`, `Netlog_Nicolas.jpg`, `Kücke_3/…21-58-30`, `…21-58-39` |
| W4 | 🔴 critical | **Kitchen AP not audible in the kitchen.** 20 Sep: no live BSSID, in "last seen 6–11 min". 21 Sep: absent from scan entirely. Yet Omada `CONNECTED`, own radio reports ch-6 utilisation, and it was heard at **-63 dBm in Keller and Fernsehecke** → transmitting, **but not into the kitchen**. Placement or shielding suspected. | `küche_2/`, `Kücke_3/`, `Keller/`, `Fernsehecke/`, `omada/` |
| W5 | 🟠 high | **Only two APs effectively serve the house.** Keller AP off; EAP330 has **0 clients**. | owner; `omada/IMG_…081257` |
| W6 | 🟠 high | **Gallery AP only -52 dBm in the best room.** Either TX power reduced or the unit is enclosed/badly mounted. **TX power not verified.** | scans |
| W7 | 🟠 high | **EAP330 unmanaged and stale**: firmware Sep 2018, system clock `2018-03-05` (no NTP), not in Omada, factory SSID on 5 GHz, VLAN SSIDs on 2.4 GHz only, ran **40 MHz on 2.4 GHz ch 11** on 20 Sep. | `omada/IMG_…081257`; `Büroecke/` |
| W8 | 🟠 high | **Epson ET-4850 Wi-Fi Direct AP** is among the loudest 2.4 GHz sources in the house, on ch 11. | `Netlog_Elternbad.jpg`, `küche_2/`, `Fernsehecke/` |
| W9 | 🟡 medium | **SSID sprawl**: 5 SSIDs per radio on the EAP650s (incl. `Admin` and a hidden SSID), all on 2.4 GHz too. | all scans |
| W10 | 🟡 medium | **Everything on auto-channel**: Fritzbox, repeaters, neighbours and all three APs change channel between scans. | all scans |
| W11 | 🟡 medium | **Controller not always-on** (laptop) → no continuous stats, Health "No Data", RRM decisions from partial data. | `omada/IMG_…190223`, `…190249` |
| W12 | ⚪ low | EAP650 firmware 1.3.6, update flagged. | `omada/IMG_…190225` |

---

## 3. Issue 2 — Sonos

### 3.1 Symptoms

"Sonos almost does not work any more"; streaming is difficult / drops out.
Owner states **Keller** and **Noemi** players are cabled; all others wireless.

### 3.2 System (from `/support/review`, 19 Sep)

| Player | MAC (SonosNet BSSID) | Role | Noise floor (dBm) | OFDM ANI | Health |
|---|---|---|---|---|---|
| Noah | 34:7E:5C:35:B2:C0 | **none** | -105 / -102 / -95 | 0 | green |
| Büroecke | 34:7E:5C:35:B0:F4 | **none** | -104 / -104 / -95 | 0 | green |
| **Keller** | 5C:AA:FD:59:5E:EB | **Root Bridge** | -106 / -118 / -108 | 4 | yellow |
| Fernsehecke (LF,RF) | 94:9F:3E:C0:EE:A2 | Tertiary | **0 / 0 / 0 / 0** | **undefined** | white |
| Noemi | 54:2A:1B:64:26:81 | **Tertiary** | -100 / -100 / -100 | 1 | green |
| Wohnzimmer | B8:E9:37:E6:09:85 | Tertiary | -110 / -107 / -100 | **6** | orange |
| Nicolas | 34:7E:5C:36:DE:91 | Tertiary | -113 / -111 / -100 | 0 | green |
| Wohnzimmer | 54:2A:1B:63:FE:6F | Tertiary | -111 / -110 / -100 | 4 | yellow |
| Elternbad | 34:7E:5C:31:CE:29 | Tertiary | -110 / -111 / -100 | **6** | orange |
| Wohnzimmer | B8:E9:37:E5:15:2B | Tertiary | -111 / -109 / -100 | **9** | **red** |
| Küche | 34:7E:5C:38:26:E3 | **Secondary** | -112 / -112 / -100 | 0 | green |
| Eltern | 34:7E:5C:38:28:B1 | Tertiary | -110 / -108 / -100 | 4 | yellow |
| Fernsehecke (LR) | 5C:AA:FD:49:0C:CB | Tertiary | -109 / -105 / -100 | **9** | **red** |
| Fernsehecke (RR) | 94:9F:3E:00:29:2F | Tertiary | -108 / -110 / -100 | **8** | **red** |

Serials (RINCON) and the full link matrix: `docs/sonos/devices.md`, `docs/sonos/network-matrix.md`.

### 3.3 Findings

| # | Severity | Finding | Evidence |
|---|---|---|---|
| S1 | 🔴 critical | **Mesh depth**: 1 root (Keller), 1 secondary (Küche), **11 tertiary**. | matrix row headers |
| S2 | 🔴 critical | **Root bridge unreachable for much of the house.** Best link into Keller is **44**; Elternbad `00/16`, Eltern `13/17`, Noemi `16/31`. | matrix, Keller column |
| S3 | 🔴 critical | **Interference on the SonosNet channel**: 3 players at OFDM ANI **8–9**, 2 at **6**, root bridge at **4**. Root bridge sits in the Keller next to the Fritzbox's 40 MHz 2.4 GHz radio (-39 dBm). | matrix; `Keller/` |
| S4 | 🟠 high | **Strong links in STP `blocking`** (e.g. Elternbad→Fernsehecke 48/57, Wz E5:15:2B→Fernsehecke 52/58, Wz E5:15:2B→Wz 63:FE:6F 56/50) because the tree is rooted in the basement. | matrix |
| S5 | 🟠 high | **Noemi reported wired but acts as Tertiary** → cable, switch port or VLAN not effective. | matrix |
| S6 | 🟠 high | **Noah and Büroecke not on SonosNet** (no role, all links 00/00 or blank) → joined via WLAN; mixed WLAN/SonosNet system. Büroecke has good Wi-Fi (-52 dBm); Noah had **no live 2.4 GHz** in its scan. | matrix; `Büroecke/`, `Netlog_Noah.jpg` |
| S7 | 🟠 high | **Fernsehecke (LF,RF) reports no radio statistics** (noise floor 0,0,0,0, ANI undefined) — likely stuck radio. Its surrounds (LR/RR) link to it at 57/66 and 60/66 but sit at ANI 9/8. | matrix |
| S8 | 🟡 medium | **The only Secondary Node (Küche) is in the room with the weakest own-AP coverage**; its links onward are 22–41. | matrix; `küche_2/`, `Kücke_3/` |
| S9 | 🟡 medium | De-facto hub is **Wohnzimmer `B8:E9:37:E6:09:85`** (most green links terminate there), itself ANI 6. Best candidate for a wired root. | matrix |
| S10 | ⚪ low | Three players named "Wohnzimmer" → diagnostics ambiguous. | device list |

### 3.4 Link between the two issues

SonosNet uses one fixed 2.4 GHz channel. That band currently carries: two co-channel EAP650s
at near-saturation (ch 6), the Fritzbox at 40 MHz (ch 7–11), the EAP330 (moved to 40 MHz
ch 11), a printer AP at -42 dBm (ch 11), ~30 beacon streams, bulbs, an inverter and
neighbours. **No clean 2.4 GHz channel exists for SonosNet.** Fixing the Wi-Fi channel plan
is a precondition for fixing Sonos.

---

## 4. Recommended remediation

Ordered; each phase is independently testable. Phases 1–2 need no hardware.

### Phase 1 — Remove rogue / unmanaged radios

1. **Fritzbox 6660: disable WLAN on both bands, and Mesh/repeater functions.** Keep it as the
   upstream router/modem only. Verify: SSID `WuTangLan` no longer on air anywhere.
2. **Epson ET-4850: disable Wi-Fi Direct.** Same for the TS5100-series printer.
3. **EAP330: retire** (recommended: 0 clients, 2018 firmware, Wi-Fi 5). Alternative: factory
   reset → update firmware → adopt into Omada → apply the same SSID/channel policy.
4. Identify **FRITZ!Box 7490** and **`WLAN-A7C604`**; if owned, disable their WLAN
   (keep DECT on the 7490 if used).

### Phase 2 — EAP650 radio plan (Omada)

5. **Disable auto-channel / RRM re-optimisation.** Pin:

   | AP | 2.4 GHz | 5 GHz |
   |---|---|---|
   | Gallery AP | ch **1**, **20 MHz** | ch **100**, 80 MHz |
   | Kitchen AP | ch **11**, **20 MHz** | ch **116**, 80 MHz |
   | *(reserved)* | **ch 6 → SonosNet** | — |

6. **2.4 GHz SSIDs → only `WuTangLan-Family` and `WuTangLan-IOT`.** Move `Admin` and
   `WuTangLan-Guest` to 5 GHz only; delete the hidden SSID unless it has a documented purpose.
7. **Check/set TX power** (suggest 5 GHz High, 2.4 GHz Medium; adjust after survey).
8. **Update EAP650 firmware.**

### Phase 3 — Physical

9. **Kitchen AP**: Omada → Devices → Kitchen AP → Tools → **Locate**. If not in the kitchen,
   relocate there. If it is, remount in the open (ceiling preferred), away from appliances/metal.
10. **Keller AP**: decide — adopt and power on, or remove from design. (SonosNet root is wired in
    the Keller and does not need it.)
11. Verify mounting of the Gallery AP (not enclosed).
12. **Move the Omada controller to an always-on host** (OC200/OC300, NAS container, Pi).

### Phase 4 — Sonos

13. **Verify Noemi's cable end-to-end**: link LEDs, switch port, **port VLAN = the Sonos VLAN**
    (untagged), no port isolation.
14. **Wire the Wohnzimmer player `B8:E9:37:E6:09:85`** (or another central player) as an
    additional/primary wired entry point, so the tree roots in the living area, not the basement.
15. **Set the SonosNet channel manually to 6** (freed in Phase 2).
16. **Choose one mode system-wide** — recommended SonosNet. Move Noah and Büroecke onto
    SonosNet (or, deliberately, move everything to WLAN — do not mix).
17. **Reboot / factory-reset Fernsehecke (LF,RF)**; re-bond surrounds.
18. Rename the three "Wohnzimmer" players.
19. Re-capture `/support/review` and compare against §5.

### Checks not yet performed (engineer should verify)

- **Netgear switch**: STP/RSTP settings on Sonos ports (Sonos runs STP; a managed switch must
  not block or flap those ports), IGMP snooping behaviour, VLAN tagging per port.
- **Firewalla**: VLAN interfaces, mDNS/SSDP reflection if the Sonos app is used from another
  VLAN, rules between the Sonos VLAN and client VLANs.
- **Fritzbox mode** (router vs. bridge / exposed host) and whether double NAT is present.
- Purpose of the `Admin` SSID and the hidden SSID.

---

## 5. Acceptance criteria

| Metric | Now | Target |
|---|---|---|
| APs on the same channel | Gallery = Kitchen on both bands | **none** |
| Omada 2.4 GHz channel utilisation | near saturation | **< 50 %** |
| SSIDs heard from the Fritzbox | `WuTangLan` on both bands | **none** |
| Own-AP signal in rooms containing an AP | -52 … -63 dBm | **-35 … -45 dBm** |
| Own-AP signal in every other room (5 GHz) | down to -70 dBm | **≥ -67 dBm** |
| Kitchen client stays on `WuTangLan-Family` | drops, falls back to Fritzbox | **stable, no fallback** |
| SonosNet structure | 1 root / 1 secondary / 11 tertiary | **no tertiary nodes** (or ≤ 2) |
| Sonos OFDM ANI | 3 × 8–9, 2 × 6 | **all ≤ 3** |
| Player → parent link strength | many < 40 | **≥ 45** |
| Players off SonosNet | 2 | **0** (or all on WLAN by design) |

---

## 6. Access the engineer will need

Omada controller (laptop, `https://127.0.0.1:8043`) · EAP330 standalone UI · Fritzbox UI ·
Firewalla app/UI · Netgear switch UI · Sonos app and `http://<player-ip>:1400/support/review` ·
physical access to AP mounting points and the switch.

## 7. Open items (not verified)

Physical location of the Kitchen AP and the EAP330 · TX power per radio · Keller AP model
and reason it is off · SonosNet channel · Sonos models/firmware/IPs · Netgear model/config ·
Firewalla config · Fritzbox mode · ownership of FRITZ!Box 7490 and `WLAN-A7C604` ·
purpose of `Admin` and hidden SSIDs · Sonos player "Eltern" location (presumably
Elternschlafzimmer).

Detailed per-room and per-device pages: `docs/wifi/`, `docs/sonos/`, `docs/open-questions.md`.
