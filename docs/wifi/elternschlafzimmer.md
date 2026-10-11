# Wi-Fi — Elternschlafzimmer

Source image: `Netlog_elternschlafzimmer.jpg` (Telegram caption **"Elternschlafzimmer"**,
`IMG_20260920_091954_565.jpg`). NetX Inspector · 19:42 → 19:54 (several scans) · phone on
`WuTangLanFamily @ 1201 Mbps` · `Wi-Fi throttling ON` · ~13 screens, the longest capture.

## Top of the list (19:42 scan)

| SSID | BSSID | Band | Channel | Signal |
|---|---|---|---|---|
| Admin | 72:4C:BC:76:7C:41 | 5 GHz | 44 (42) | **-54 dBm** |
| WuTangLan-Family *(connected)* | 76:4C:BC:76:7C:41 | 5 GHz | 44 (42) | **-54 dBm** |
| WuTangLan-Guest | 7A:4C:BC:76:7C:41 | 5 GHz | 44 (42) | -54 dBm |
| WuTangLan-IOT | 7E:4C:BC:76:7C:41 | 5 GHz | 44 (42) | -54 dBm |
| WuTangLan-Guest | 7A:4C:BC:76:7C:40 | 2.4 GHz | 11 | -57 dBm |
| [Hidden SSID] | 82:4C:BC:76:7C:41 | 5 GHz | 44 (42) | -57 dBm |

## Later in the same capture (19:43 / 19:54 scans)

| SSID | BSSID | Band | Channel | Signal |
|---|---|---|---|---|
| DIRECT-Ub7F-TS5100series | 6E:F2:D8:E7:FA:7F | 2.4 GHz | 11 | -80 dBm |
| FRITZ!Box 7490 | 38:10:D5:BA:88:B3 | 2.4 GHz | 6 | -80 dBm |
| [Hidden SSID] | 84:16:F9:93:E9:2C | 2.4 GHz | 6 | -78 dBm |
| Admin | 72:4C:BC:76:7C:40 | 2.4 GHz | 11 | -79 dBm |
| WuTangLan-IOT | 86:16:F9:BF:E9:2F | 2.4 GHz | 6 | -80 dBm |
| Admin | 72:4C:BC:76:94:C1 | 5 GHz | 48 (42) | -87 dBm |
| WuTangLan-Family | 76:4C:BC:76:94:C1 | 5 GHz | 48 (42) | -87 dBm |
| WuTangLan-Guest | 7A:4C:BC:76:94:C1 | 5 GHz | 48 (42) | -91 dBm |
| WuTangLan-IOT | 7E:4C:BC:76:94:C1 | 5 GHz | 48 (42) | -91 dBm |
| DIRECT-Ub7F-TS5100series | 6E:F2:D8:E7:FA:7F | 2.4 GHz | 6 | -94 dBm |

Note the drift within twelve minutes: AP-1 on 2.4 GHz goes from **-57 dBm** at 19:42 to
**-79 dBm** at 19:54. Either the phone moved, or the link is genuinely unstable at this
position. The 19:42 numbers are the favourable case.

## Assessment

- Usable only via **AP-1 on 5 GHz (-54 dBm)**. AP-2 is at -87 to -91 dBm here, i.e. useless.
- 2.4 GHz from AP-1 is borderline (-57 best, -79 at the worst moment). SonosNet runs on
  2.4 GHz — the Sonos player "Eltern" in the matrix is yellow with ANI 4 and reaches the
  Keller root at only 13/17, which fits.
- No dark green anywhere.

## Not retrieved

- Why the reading drifted 22 dB in twelve minutes (phone moved vs. AP roaming/power change) —
  not determinable from screenshots.
