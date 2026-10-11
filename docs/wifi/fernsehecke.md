# Wi-Fi — Fernsehecke

Source: `Fernsehecke/Screenshot_2026-09-20-22-05-18-071` … `…-22-05-47-738`
(NetSpot / Network Analyzer "Inspector", 1220 × 2712, seven full-resolution captures covering
two list refreshes). Time **22:05** · phone on `WuTangLanFamily @ 1201 Mbps` ·
`Wi-Fi throttling ON`.

> The same seven files were also copied into `Küche/`. The Küche has since been re-scanned
> separately (`küche_2/`, 22:16–22:17), so this set is the **Fernsehecke**.
>
> `Fernsehecke/Screenshot_2026-09-20-22-02-17-014_com.miui.gallery.jpg` is a screenshot of the
> phone's gallery app, not a Wi-Fi scan — no data in it.

## Full list (first refresh)

| SSID | BSSID | Band | Channel | Signal |
|---|---|---|---|---|
| **WuTangLan** (Fritzbox 6660) | 0C:72:74:00:63:9B | 5 GHz | **116 (114)** | **-40 dBm** |
| **DIRECT-f1-EPSON-ET-4850** | 6A:55:D4:7D:0B:9B | 2.4 GHz | **11** | **-48 dBm** |
| Admin | 72:4C:BC:76:7C:41 | 5 GHz | 44 (42) | -53 dBm |
| WuTangLan-Family *(connected)* | 76:4C:BC:76:7C:41 | 5 GHz | 44 (42) | **-53 dBm** |
| WuTangLan-Guest | 7A:4C:BC:76:7C:41 | 5 GHz | 44 (42) | -53 dBm |
| WuTangLan-IOT | 7E:4C:BC:76:7C:41 | 5 GHz | 44 (42) | -53 dBm |
| WuTangLan-Family | 76:4C:BC:76:7C:40 | 2.4 GHz | 11 | **-55 dBm** |
| Admin | 72:4C:BC:76:7C:40 | 2.4 GHz | 11 | -56 dBm |
| Vodafone Homespot | DE:A6:33:43:EC:10 | 2.4 GHz | 1 | -57 dBm |
| Vodafone Hotspot | DE:A6:33:43:EC:0E | 2.4 GHz | 1 | -58 dBm |
| Vodafone-DD14 | DC:A6:33:43:EC:0C | 2.4 GHz | 1 | -59 dBm |
| WuTangLan-IOT | 7E:4C:BC:76:94:C0 | 2.4 GHz | 1 | -63 dBm |
| WuTangLan-Family | 76:4C:BC:76:94:C0 | 2.4 GHz | 1 | -64 dBm |
| WuTangLan-Guest | 7A:4C:BC:76:94:C0 | 2.4 GHz | 1 | -65 dBm |
| WuTangLan-Guest | 86:16:F9:BF:E9:2E | 2.4 GHz | 6 | -67 dBm |
| WuTangLan-Family | 86:16:F9:BF:E9:2D | 2.4 GHz | 6 | -68 dBm |
| WLAN-A7C604 | 1C:23:A2:7A:E3:7A | 2.4 GHz | 1 | -69 dBm |
| WuTangLan-IOT | 86:16:F9:BF:E9:2F | 2.4 GHz | 6 | -69 dBm |
| TP-Link_5G_93E92D | 84:16:F9:93:E9:2D | 5 GHz | 44 (42) | -72 dBm |
| WuTangLan-IOT | 7E:4C:BC:76:7C:40 | 2.4 GHz | 11 | -72 dBm |
| DIRECT-Ub7F-TS5100series | 6E:F2:D8:E7:FA:7F | 2.4 GHz | 1 | -74 dBm |
| WuTangLan-Guest | 7A:4C:BC:76:7C:40 | 2.4 GHz | 11 | -74 dBm |
| Admin | 72:4C:BC:76:94:C0 | 2.4 GHz | 1 | -75 dBm |
| WLAN-A7C604 | 1C:23:A2:7A:E3:7B | 5 GHz | 52 (50) | -75 dBm |
| WuTangLan-Family | 76:4C:BC:76:94:C1 | 5 GHz | 48 (42) | -78 dBm |
| Admin | 72:4C:BC:76:94:C1 | 5 GHz | 48 (42) | -79 dBm |
| WLAN-A7C604 | 38:10:D5:8B:10:56 | 2.4 GHz | 1 | -84 dBm |

## Second refresh, seconds later

AP-2's 5 GHz radio (`…76:94:C1`, ch 48/42) collapses from **-78 / -79 dBm to -91 dBm** for all
four SSIDs, and the Fritzbox's 2.4 GHz `WuTangLan` (`0C:72:74:00:63:9A`, **channel 11 (9)**)
drops to *"Offline. Last seen ~4 mins ago"*. Within one position, within seconds, AP-2's
5 GHz link swings 12 dB. That instability is itself a finding.

## Assessment

- Coverage from your own kit is **the second best in the house** — AP-1 at -53 dBm (5 GHz)
  and -55 dBm (2.4 GHz). Still not same-room-AP strength.
- **The two loudest signals here are the two you least want:**
  - the **Fritzbox 6660 on 5 GHz at -40 dBm** (and its 40 MHz-wide 2.4 GHz radio on channel
    11 intermittently), and
  - the **Epson ET-4850's Wi-Fi Direct AP at -48 dBm on 2.4 GHz channel 11** — directly on
    AP-1's 2.4 GHz channel, and directly on the band SonosNet uses.
- All three EAP groups are audible here (AP-1 ch 11 / 44, AP-2 ch 1 / 48, AP-3 ch 6), so this
  is a fairly central position in the house — which also means it hears *everything*.

## Why this matters for Sonos

The three Fernsehecke players are **the three worst in the whole system**:

| Player | BSSID | Role | Noise floor | OFDM ANI | Health |
|---|---|---|---|---|---|
| Fernsehecke (LF,RF) | 94:9F:3E:C0:EE:A2 | Tertiary Node | **0, 0, 0, 0** | **undefined** | white |
| Fernsehecke (LR) | 5C:AA:FD:49:0C:CB | Tertiary Node | -109, -105, -100 | **9** | **red** |
| Fernsehecke (RR) | 94:9F:3E:00:29:2F | Tertiary Node | -108, -110, -100 | **8** | **red** |

- The soundbar / front pair reports **no radio statistics at all** — noise floor `0,0,0,0` and
  ANI `undefined`. It is not reporting, which usually means a stuck or unhealthy radio.
- The two surrounds are pegged at **ANI 8 and 9** — maximum interference mitigation. The
  surround links themselves are fine (57/66 and 60/66, green, forwarding); it is the RF
  environment around them that is hostile, and this scan shows exactly why: a 40 MHz Fritzbox
  radio and a printer AP, both loud, both on 2.4 GHz channel 11.
- All three are **Tertiary Nodes**, three SonosNet hops from the Keller root bridge.

See `docs/sonos/network-matrix.md`.

## Not retrieved

- Why `Fernsehecke (LF,RF)` reports no radio statistics. Its own support page
  (`http://<its-ip>:1400/support/review`) would say more.
