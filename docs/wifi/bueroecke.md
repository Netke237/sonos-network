# Wi-Fi — Büroecke

Source: `Büroecke/Screenshot_2026-09-20-22-45-46-467` … `…-22-46-13-983`
(NetSpot / Network Analyzer "Inspector", 1220 × 2712, seven full-resolution captures).
Time **22:45–22:46** · phone on `WuTangLanFamily @ 1201 Mbps` · `Wi-Fi throttling ON`.

## Full list — everything live in the scan

| SSID | BSSID | Band | Channel | Signal |
|---|---|---|---|---|
| WuTangLan-IOT | 7E:4C:BC:76:7C:40 | 2.4 GHz | 11 | **-52 dBm** |
| Admin | 72:4C:BC:76:7C:40 | 2.4 GHz | 11 | -54 dBm |
| Admin | 72:4C:BC:76:7C:41 | 5 GHz | 44 (42) | -54 dBm |
| WuTangLan-Family | 76:4C:BC:76:7C:40 | 2.4 GHz | 11 | **-54 dBm** |
| WuTangLan-Family *(connected)* | 76:4C:BC:76:7C:41 | 5 GHz | 44 (42) | **-54 dBm** |
| WuTangLan-Guest | 7A:4C:BC:76:7C:41 | 5 GHz | 44 (42) | -54 dBm |
| WuTangLan-IOT | 7E:4C:BC:76:7C:41 | 5 GHz | 44 (42) | -54 dBm |
| Vodafone Homespot | DE:A6:33:43:EC:10 | 2.4 GHz | 1 | -57 dBm |
| Vodafone Hotspot | DE:A6:33:43:EC:0E | 2.4 GHz | 1 | -61 dBm |
| Vodafone-DD14 | DC:A6:33:43:EC:0C | 2.4 GHz | 1 | -61 dBm |
| TP-Link_5G_93E92D | 84:16:F9:93:E9:2D | 5 GHz | 44 (42) | -63 dBm |
| DIRECT-f1-EPSON-ET-4850 | 6A:55:D4:7D:0B:9B | 2.4 GHz | 11 | -64 dBm |
| WuTangLan-Family | 86:16:F9:BF:E9:2D | 2.4 GHz | **11 (9)** | -72 dBm |
| WuTangLan-Guest | 86:16:F9:BF:E9:2E | 2.4 GHz | **11 (9)** | -72 dBm |
| WuTangLan-IOT | 86:16:F9:BF:E9:2F | 2.4 GHz | **11 (9)** | -72 dBm |
| DIRECT-Ub7F-TS5100series | 6E:F2:D8:E7:FA:7F | 2.4 GHz | 1 | -77 dBm |
| WuTangLan-Guest | 7A:4C:BC:76:7C:40 | 2.4 GHz | 11 | -78 dBm |
| WuTangLan-Family | 76:4C:BC:76:94:C0 | 2.4 GHz | 1 | -83 dBm |
| Admin | 72:4C:BC:76:94:C0 | 2.4 GHz | 1 | -87 dBm |
| WLAN-A7C604 | 38:10:D5:8B:10:56 | 2.4 GHz | 1 | -89 dBm |
| WuTangLan-IOT | 7E:4C:BC:76:94:C1 | 5 GHz | 48 (42) | -91 dBm |
| Admin | 72:4C:BC:76:94:C1 | 5 GHz | 48 (42) | -92 dBm |
| WuTangLan-Family | 76:4C:BC:76:94:C1 | 5 GHz | 48 (42) | -92 dBm |
| WuTangLan-Guest | 7A:4C:BC:76:94:C1 | 5 GHz | 48 (42) | -92 dBm |

### Offline in this scan

| SSID | BSSID | Band | Channel | Last seen | ≈ wall clock |
|---|---|---|---|---|---|
| WuTangLan-Guest / -IOT (AP-2) | 7A/7E:4C:BC:76:94:C0 | 2.4 GHz | 1 | ~28 min | ~22:18 |
| [Hidden SSID] (AP-3) | 84:16:F9:93:E9:2C | 2.4 GHz | **11 (9)** | ~28 min | ~22:18 |
| Vodafone-DD14 | DC:A6:33:43:EC:0D | 5 GHz | 60 (58) | ~26 min | ~22:20 |
| WLAN-A7C604 | 1C:23:A2:7A:E3:7A | 2.4 GHz | 1 | ~40 min | ~22:06 |
| WLAN-A7C604 | 1C:23:A2:7A:E3:7B | 5 GHz | 52 (50) | ~40–41 min | ~22:05 |
| **WuTangLan** (Fritzbox) | 0C:72:74:00:63:9A | 2.4 GHz | **11 (9)** | **~45 min** | **~22:01** |
| **WuTangLan** (Fritzbox) | 0C:72:74:00:63:9B | 5 GHz | 116 (114) | **~40–41 min** | **~22:05** |

## Assessment

- **Coverage is fine here — one of the better rooms.** AP-1 at **-52 dBm (2.4 GHz)** and
  **-54 dBm (5 GHz)**, essentially the same as the Wohnzimmer. Once again it is AP-1 doing the
  work; AP-2 is at -83 to -92 dBm and AP-3 at -72 dBm.

- **AP-3 has moved to 2.4 GHz `channel 11 (9)` — and it is now 40 MHz wide.** In every earlier
  scan AP-3 was on channel 6 (and once on 1). At 22:45 all three of its SSIDs *and* its hidden
  SSID sit on channel 11 with a 40 MHz width, i.e. occupying channels 7–11.

  That means **three 2.4 GHz radios are now stacked on channel 11** in this house — AP-1
  (20 MHz), AP-3 (40 MHz) and, until ~22:01, the Fritzbox (40 MHz) — plus the Epson printer at
  -64 dBm. Two 40 MHz channels on 2.4 GHz is already a configuration error; putting them on
  top of your main AP is worse.

- **`84:16:F9:93:E9:2C` (the hidden SSID) is on the same channel 11 (9) as
  `86:16:F9:BF:E9:2D/E/F`.** That confirms AP-3 and the `TP-Link_5G_93E92D` device are the
  same physical hardware.

## Observation worth confirming: did the Fritzbox Wi-Fi go off at ~22:01?

Across three independent scans the Fritzbox's two radios have a consistent "last seen" wall
clock and are never seen again afterwards:

| Scan | Fritzbox 2.4 GHz last seen | Fritzbox 5 GHz last seen |
|---|---|---|
| Fernsehecke 22:05 | ~4 min → **~22:01** | live, **-40 dBm** |
| Küche 22:17 | ~16 min → **~22:01** | ~12 min → **~22:05** |
| Büroecke 22:46 | ~45 min → **~22:01** | ~41 min → **~22:05** |

Both radios stop at fixed wall-clock times (2.4 GHz ~22:01, 5 GHz ~22:05) rather than fading
with distance, and the `WLAN-A7C604` devices stop at ~22:05–22:06 too.

Two readings are possible and the screenshots cannot separate them:

1. **The Fritzbox (and the Fritz repeaters) went off air** around 22:01–22:05 — switched off,
   rebooted, or the radios disabled.
2. The phone left the basement after the 22:01 Keller scan and never came back within range of
   that whole device cluster.

The Fernsehecke scan argues for (1): at 22:05 the Fritzbox 5 GHz was still **-40 dBm** there
while its 2.4 GHz had already been gone for four minutes — both radios are in the same box, so
distance does not explain one dropping and not the other.

**Did you turn the Fritzbox Wi-Fi off at around 22:00?** If so, that is exactly the right move
and the later scans already show the benefit.

## Why this matters for Sonos

The **Büroecke player has no SonosNet role and no mesh links at all** — every cell in its row
and column of the Network Matrix is blank or `00 / 00 undefined`. Wi-Fi here is good (-52 dBm),
so this is almost certainly a player that is **joined over WLAN rather than over SonosNet**,
same as Noah. See `docs/sonos/network-matrix.md`.

## Not retrieved

- Whether the Büroecke player is on `WuTangLan-Family` by Wi-Fi or on a cable — not shown on
  the captured support page.
- Why AP-3 changed channel, and whether Omada auto-channel did it.
