# Session handoff — home Wi-Fi/VLAN, EAP diagnostics and Galerie 5 GHz resolution

**Date:** 4 October 2026  
**Status:** Galerie 5 GHz radio restored and verified on Channel 44; EAP330 client and channel conflict audited; Galerie AP powered down for physical relocation; awaiting post-relocation measurement.

---

## 1. Executive Summary & Session Outcomes

1. **Galerie 5 GHz Restored & Verified (Channel 44)**:
   - Initial problem: Galerie 5 GHz (`...:7C:41`) was completely absent across all phone scans down to -92 dBm while configured on DFS Channel 100.
   - Diagnostic action: Switched Galerie 5 GHz to Non-DFS Channel 44 (80 MHz, center 42).
   - Observed result: All 4 SSIDs (`WuTangLan-Family`, `Admin`, `Guest`, `IoT`) immediately appeared at **-53 dBm**. Link rate reached 400 Mbps.
   - Conclusion: Radio hardware, antennas, and Omada mappings are 100% operational. Absence on Channel 100 was caused by European DFS quiet timers (CAC) / radar lockouts. Decision locked: keep Galerie on Channel 44.

2. **Galerie 2.4 GHz Verified on Channel 1**:
   - Confirmed on **Channel 1** at **-54 dBm to -61 dBm** (`76:4C:BC:76:7C:40`). Previous discrepancy where it appeared on Channel 6 in older kitchen scans is fully resolved.

3. **Standalone EAP330 Full Audit & Conflict Identification**:
   - Device: TP-Link EAP330 v1.0/2.0, standalone firmware 1.4.0 (20180925), IP `192.168.55.251` (unmanaged, shows `PENDING` with error in Omada).
   - Physical location: Wohnzimmer (Living Room, browser bookmark `EAP330_livingR`).
   - Active client load: Exactly **8 connected clients** audited via `Monitoring -> Client`:
     1. `68-55-D4-7D-0B-9B` (2.4 GHz Family) — Epson ET-4850 printer
     2. `F8-54-B8-8B-45-36` (2.4 GHz Family)
     3. `FA-32-98-E4-72-A8` (2.4 GHz Family)
     4. `10-97-BD-5D-3C-DC` (2.4 GHz IoT, VLAN 20) — Espressif smart home device
     5. `EC-C9-FF-9C-DC-D8` (2.4 GHz IoT, VLAN 20)
     6. `78-33-C6-D3-03-4E` (5 GHz Family, SNR 42, Rate 135)
     7. `22-93-BB-FE-C0-FD` (5 GHz Family, SNR 22, Rate 121)
     8. `8A-BE-A5-B0-A7-D2` (5 GHz Family, SNR 26, Rate 135)
   - Architectural Conflicts:
     - 2.4 GHz: Operating on **Channel 11**, creating continuous co-channel contention against the Kitchen AP (also on Channel 11).
     - 5 GHz: Operating on **Channel 36 (38)** at 40 MHz, overlapping with Galerie AP (Ch 44 at 80 MHz) and Kitchen AP (Ch 40 at 40 MHz).
     - Sonos Impact: The Wohnzimmer Sonos player registered **OFDM ANI 9 (RED)**, directly corresponding to high local RF congestion from this co-located AP.
     - Retirement Feasibility: In Wohnzimmer scans, Galerie AP already provides **-52 dBm (2.4G) and -55 dBm (5G)**. Turning off EAP330 is the primary candidate to eliminate the house-wide Channel 11 collision.

4. **Nuki Bridge Behavior & VLAN Association**:
   - Device: Nuki Bridge, MAC `30:C6:F7:3D:8B:0C`, IP `192.168.20.156` (VLAN 20 `WuTangLan-IOT`).
   - Radio constraint: 2.4 GHz only (Espressif ESP32 hardware).
   - Connection migration: Previously associated with Galerie AP. When Galerie AP was switched off at ~13:48, Nuki re-associated to **Kitchen AP** (`192.168.55.37`) on Channel 11.
   - Reason it chose Kitchen over EAP330: Both Kitchen AP and EAP330 broadcast on Channel 11. Simple IoT firmware latches onto the first beacon/probe response received and stays sticky.

5. **Galerie AP Relocation State**:
   - Galerie AP powered down at ~13:48 (`DISCONNECTED` in Omada) to be moved away from the soundbar.
   - Clean baseline established before move: 5 GHz Ch 44 at -53 dBm; 2.4 GHz Ch 1 at -61 dBm.
   - "After" scan pending once AP is plugged in at its new position.

---

## 2. Radio Plan Status Table

| Device | 2.4 GHz Status | 5 GHz Status | Role / Operational Notes |
|---|---|---|---|
| **Galerie EAP650** (`...:7C:40` / `...:7C:41`) | **Channel 1**, 20 MHz, -54 to -61 dBm | **Channel 44 (42)**, 80 MHz, -53 dBm | Restored and stable. Pinned off Channel 100 DFS. Currently disconnected for physical relocation. |
| **Kitchen EAP650** (`...:94:C0` / `...:94:C1`) | **Channel 11**, 20 MHz, 17% util in Omada | **Channel 40 (38)**, 40 MHz, 1% util in Omada | Currently hosting Nuki Bridge and mobile clients while Galerie is offline. |
| **EAP330 Standalone** (`84:16:F9...`) | **Channel 11**, 20 MHz | **Channel 36 (38)**, 40 MHz | Hosts 8 clients in Wohnzimmer. Causes Channel 11 collision with Kitchen AP. Recommended for test power-down. |
| **Epson ET-4850** (`6A:55:D4...`) | **Channel 1**, -51 dBm (Wi-Fi Direct) | N/A | Wi-Fi Direct blasts on Ch 1 co-channel with Galerie AP. Connected as client to EAP330 (`68-55-D4...`). |
| **SonosNet** | Fixed 2.4 GHz mesh | N/A | Protected by pinning Galerie AP to Ch 1 and Kitchen AP to Ch 11 (leaving Channel 6 free for SonosNet). |

---

## 3. Immediate Next Steps

1. **Power up Galerie EAP650 in new location**: Verify in Omada that status returns to `CONNECTED`.
2. **Collect Post-Relocation Scan in Galerie**:
   - Run Inspector on phone from the same position near soundbar.
   - Record signal delta for Galerie 2.4 GHz (`...:7C:40`) and 5 GHz (`...:7C:41`).
3. **EAP330 Power-Down Test**:
   - Power off EAP330.
   - Verify that all 8 clients migrate smoothly to Galerie / Kitchen APs.
   - Confirm Channel 11 airtime utilization drop.
