# Wi-Fi — Wohnzimmer

Source image: `Netlog_Wohnzimmer.jpg` (Telegram caption **"Wohnzimmer"**,
`IMG_20260920_092234_903.jpg`). NetX Inspector · 21:00–21:01 · phone on
`WuTangLanFamily @ 1201 Mbps` · `Wi-Fi throttling ON` · ~8 screens.

## Top of the list

| SSID | BSSID | Band | Channel | Signal |
|---|---|---|---|---|
| Admin | 72:4C:BC:76:7C:40 | 2.4 GHz | 11 | **-52 dBm** |
| WuTangLan-Family | 76:4C:BC:76:7C:40 | 2.4 GHz | 11 | **-52 dBm** |
| WuTangLan-Guest | 7A:4C:BC:76:7C:40 | 2.4 GHz | 11 | -52 dBm |
| WuTangLan-IOT | 7E:4C:BC:76:7C:40 | 2.4 GHz | 11 | -52 dBm |
| WuTangLan-Family *(connected)* | 76:4C:BC:76:7C:41 | 5 GHz | 44 (42) | **-55 dBm** |
| WuTangLan-Guest | 7A:4C:BC:76:7C:41 | 5 GHz | 44 (42) | -55 dBm |
| WuTangLan-IOT | 7E:4C:BC:76:7C:41 | 5 GHz | 44 (42) | -55 dBm |
| **TP-Link_5G_93E92D** | 84:16:F9:93:E9:2D | 5 GHz | **44 (42)** | -56 dBm |
| DIRECT-f1-EPSON-ET-4850 | 6A:55:D4:7D:0B:9B | 2.4 GHz | 11 | -59 dBm |
| Vodafone Homespot | DE:A6:33:43:EC:10 | 2.4 GHz | 11 | -67 dBm |
| Admin | 72:4C:BC:76:94:C1 | 5 GHz | 48 (42) | -75 dBm |
| WuTangLan-IOT | 7E:4C:BC:76:94:C1 | 5 GHz | 48 (42) | -75 dBm |
| Vodafone-DD14 | DC:A6:33:43:EC:0D | 5 GHz | 108 (106) | -77 dBm |
| **WuTangLan** (Fritzbox 6660) | 0C:72:74:00:63:9B | 5 GHz | **36 (50)** | -86 dBm |
| Tapo_Bulb_C67B | 0C:EF:15:5E:C6:7B | 2.4 GHz | 6 | -96 dBm |

Hidden SSIDs seen here: `82:4C:BC:76:7C:41` (5 GHz ch 44/42), `82:4C:BC:76:94:C1`
(5 GHz ch 48/42), `84:16:F9:93:E9:2C` (2.4 GHz ch 6).

## Assessment

- Best coverage in the house: **-52 dBm on 2.4 GHz, -55 dBm on 5 GHz**, both from AP-1.
  Still not "same-room AP" strength.
- **`TP-Link_5G_93E92D` is on exactly the same channel as your own AP-1 (44, centre 42) at
  almost identical strength (-56 vs -55).** Two of your radios are fighting each other for the
  same 80 MHz here. This alone will halve 5 GHz throughput in the living room.
- Three Sonos players called "Wohnzimmer" live here, and in the Sonos matrix one of them
  (B8:E9:37:E5:15:2B) is **red with OFDM ANI 9** — the worst interference score in the system.
  That is consistent with what this scan shows.

## Not retrieved

- Whether the EAP you believe is in the Wohnzimmer is AP-1 or the `TP-Link_…93E92D` device.
- The 2.4 GHz reading for AP-3 (ch 6) in this room: it appears only in the offline section.
