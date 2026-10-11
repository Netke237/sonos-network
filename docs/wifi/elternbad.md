# Wi-Fi — Elternbad

Source image: `Netlog_Elternbad.jpg` (Telegram caption **"Elternbad"**,
`IMG_20260920_092430_279.jpg`). NetX Inspector · 21:14 · phone on
`WuTangLanFamily @ 1201 Mbps` · `Wi-Fi throttling ON` · ~9 screens.

## Top of the list

| SSID | BSSID | Band | Channel | Signal |
|---|---|---|---|---|
| DIRECT-f1-EPSON-ET-4850 | 6A:55:D4:7D:0B:9B | 2.4 GHz | 11 | **-42 dBm** |
| Admin | 72:4C:BC:76:7C:41 | 5 GHz | 44 (42) | **-50 dBm** |
| WuTangLan-Guest | 7A:4C:BC:76:7C:41 | 5 GHz | 44 (42) | -50 dBm |
| WuTangLan-IOT | 7E:4C:BC:76:7C:41 | 5 GHz | 44 (42) | -50 dBm |
| WuTangLan-Family *(connected)* | 76:4C:BC:76:7C:41 | 5 GHz | 44 (42) | **-51 dBm** |
| WuTangLan-Guest | 7A:4C:BC:76:7C:40 | 2.4 GHz | 11 | -56 dBm |
| WuTangLan-IOT | 7E:4C:BC:76:7C:40 | 2.4 GHz | 11 | -56 dBm |
| Vodafone Hotspot | DE:A6:33:43:EC:0E | 2.4 GHz | 11 | -59 dBm |
| Vodafone Homespot | DE:A6:33:43:EC:10 | 2.4 GHz | 11 | -60 dBm |
| Vodafone-DD14 | DC:A6:33:43:EC:0C | 2.4 GHz | 11 | -60 dBm |
| TP-Link_5G_93E92D | 84:16:F9:93:E9:2D | 5 GHz | 36 (42) | -69 dBm |
| WuTangLan-Guest | 86:16:F9:BF:E9:2E | 2.4 GHz | 1 | -71 dBm |
| WuTangLan-IOT | 86:16:F9:BF:E9:2F | 2.4 GHz | 1 | -71 dBm |
| WuTangLan-Family | 86:16:F9:BF:E9:2D | 2.4 GHz | 1 | -72 dBm |
| Admin | 72:4C:BC:76:94:C0 | 2.4 GHz | 1 | -76 dBm |
| WuTangLan-Family | 76:4C:BC:76:94:C0 | 2.4 GHz | 1 | -76 dBm |
| WuTangLan-Guest | 7A:4C:BC:76:94:C0 | 2.4 GHz | 1 | -77 dBm |
| WuTangLan-Guest | 7A:4C:BC:76:94:C1 | 5 GHz | 48 (42) | -83 dBm |
| Admin | 72:4C:BC:76:94:C1 | 5 GHz | 48 (42) | -84 dBm |
| WuTangLan-Family | 76:4C:BC:76:94:C1 | 5 GHz | 48 (42) | -84 dBm |

Everything below that is in the "offline / last seen" section, including the Fritzbox
`WuTangLan` SSIDs, `FRITZ!Box 6660 Cable EV`, `FRITZ!Box 7490`, `SG-Gast` and the Tapo bulbs.

> **Reading note:** in this capture AP-3's SSIDs (`86:16:F9:BF:E9:2x`) are reported on channel 1,
> whereas every other room shows AP-3 on channel 6. One of the two is a mis-read or AP-3 changed
> channel between scans. Treat AP-3's channel as "1 or 6, verify in Omada".

## Assessment

- Good 5 GHz from AP-1 here (**-50/-51 dBm**), the strongest own-network reading in the house.
- 2.4 GHz only -56 dBm.
- **The loudest thing in the bathroom is the Epson printer's Wi-Fi Direct AP at -42 dBm on
  2.4 GHz channel 11** — the same channel as AP-1's 2.4 GHz radio and the Fritzbox. A printer
  parked on channel 11 at -42 dBm is a real contributor to the 2.4 GHz problem.
- The Sonos player "Elternbad" is **orange, ANI 6**, and its link to the Keller root is
  `00 / 16` — effectively no path to the wire. See `docs/sonos/network-matrix.md`.

## Not retrieved

- Whether the Epson can be set to a different channel or Wi-Fi Direct disabled (device config,
  not visible in the scan).

---

## Post-Remediation Re-Scan — 4 October 2026 (22:19)

Source image: NetX Inspector screen captures (`IMG_20261004_2219*.jpg`). Phone connected to `WuTangLanFamily @ 1201 Mbps` (Wi-Fi 6), `Wi-Fi throttling ON`.

### Top of the List (4 Oct 2026)

| SSID | BSSID | Band | Channel | Signal | Notes |
|---|---|---|---|---|---|
| **Admin** | `72:4C:BC:76:7C:41` | 5 GHz | **44 (42)** | **-55 dBm** | Galerie AP (Wi-Fi 6, 80 MHz) |
| **WuTangLan-Family** *(connected)* | `76:4C:BC:76:7C:41` | 5 GHz | **44 (42)** | **-55 dBm** | **1201 Mbps link rate** |
| **WuTangLan-Guest** | `7A:4C:BC:76:7C:41` | 5 GHz | **44 (42)** | **-55 dBm** | Galerie AP |
| **WuTangLan-IOT** | `7E:4C:BC:76:7C:41` | 5 GHz | **44 (42)** | **-55 dBm** | Galerie AP |
| **WuTangLan-Family** | `76:4C:BC:76:7C:40` | 2.4 GHz | **1** | **-60 dBm** | Galerie AP (Ch 1 pinned) |
| **Admin** | `72:4C:BC:76:7C:40` | 2.4 GHz | **1** | **-61 dBm** | Galerie AP |
| **WuTangLan-Guest** | `7A:4C:BC:76:7C:40` | 2.4 GHz | **1** | **-61 dBm** | Galerie AP |
| **WuTangLan-IOT** | `7E:4C:BC:76:7C:40` | 2.4 GHz | **1** | **-61 dBm** | Galerie AP |
| WLAN-A7C604 | `38:10:D5:8B:10:56` | 2.4 GHz | 11 | -84 dBm | Neighbor repeater |
| WuTangLan-Family | `76:4C:BC:76:94:C0` | 2.4 GHz | 11 | -85 dBm | Kitchen AP |
| WuTangLan-IOT | `7E:4C:BC:76:94:C0` | 2.4 GHz | 11 | -85 dBm | Kitchen AP |
| WuTangLan-Guest | `7A:4C:BC:76:94:C0` | 2.4 GHz | 11 | -86 dBm | Kitchen AP |
| Vodafone-DD14 | `DC:A6:33:43:EC:0C` | 2.4 GHz | 11 | -87 dBm | Neighbor |
| Vodafone Hotspot | `DE:A6:33:43:EC:0E` | 2.4 GHz | 11 | -88 dBm | Neighbor |
| WuTangLan-IOT | `7E:4C:BC:76:94:C1` | 5 GHz | 40 (38) | -91 dBm | Kitchen AP |
| WuTangLan-Family | `76:4C:BC:76:94:C1` | 5 GHz | 40 (38) | -92 dBm | Kitchen AP |

### Key Differences & Improvements (19 Sep vs 4 Oct)
1. **Epson Wi-Fi Direct (-42 dBm on Ch 11) is 100% GONE**: Disabling Wi-Fi Direct on the printer permanently cleaned the bathroom 2.4 GHz spectrum.
2. **EAP330 is 100% GONE**: Completely powered off.
3. **Galerie 5 GHz is rock solid at -55 dBm**: Operating cleanly on non-DFS Channel 44 (80 MHz) delivering a maximum **1201 Mbps Wi-Fi 6** connection.
4. **Galerie 2.4 GHz pinned to Channel 1 at -60 dBm**: Clean channel allocation leaving Channel 6 unhindered for SonosNet.

