# Wi-Fi — Noah

Source image: `Netlog_Noah.jpg` (Telegram caption **"Noah"**, `IMG_20260920_092310_315.jpg`).
NetX Inspector · 21:03–21:04 · phone on `WuTangLanFamily @ 1201 Mbps` ·
`Wi-Fi throttling ON` · ~7 screens.

## Top of the list

| SSID | BSSID | Band | Channel | Signal |
|---|---|---|---|---|
| Admin | 72:4C:BC:76:7C:41 | 5 GHz | 44 (42) | **-61 dBm** |
| WuTangLan-Family *(connected)* | 76:4C:BC:76:7C:41 | 5 GHz | 44 (42) | **-61 dBm** |
| WuTangLan-Guest | 7A:4C:BC:76:7C:41 | 5 GHz | 44 (42) | -61 dBm |
| WuTangLan-IOT | 7E:4C:BC:76:7C:41 | 5 GHz | 44 (42) | -61 dBm |
| Admin | 72:4C:BC:76:94:C1 | 5 GHz | 48 (42) | -67 dBm |
| WuTangLan-Family | 76:4C:BC:76:94:C1 | 5 GHz | 48 (42) | -67 dBm |

## The 2.4 GHz gap

**No 2.4 GHz network of yours was live in the current scan.** Every 2.4 GHz entry in this
capture sits in the offline section:

| SSID | BSSID | Channel | Last seen |
|---|---|---|---|
| WuTangLan-Guest | 7A:4C:BC:76:7C:40 | 11 | ~3 min ago |
| WuTangLan-Guest | 7A:4C:BC:76:94:C0 | 1 | ~1 min ago |
| WuTangLan-Guest | 86:16:F9:BF:E9:2E | 6 | ~10 min ago |
| WuTangLan-IOT | 7E:4C:BC:76:7C:40 | 11 | ~4 min ago |
| WLAN-A7C604 | 1C:23:A2:7A:E3:7B | — | ~7 min ago |
| SUN2000-HV2280437924 | C4:69:F0:A9:B0:17 | 1 | ~6 min ago |
| DIRECT-Ub7F-TS5100series | 6E:F2:D8:E7:FA:7F | 11 | ~1 min ago |
| Tapo_Bulb_8CD1 / _BAD7 / _C67B | 0C:EF:15:5E:… | 6 | 3–4 min ago |
| Vodafone Homespot | DE:A6:33:43:EC:10 | — | ~1 min ago |

Even allowing for Android scan throttling, a room where **no 2.4 GHz AP is present in a live
scan** is a genuine coverage hole on the band SonosNet depends on.

## Assessment

- 5 GHz only, and at -61 dBm that is already weak for a room a client sits in.
- The Sonos player "Noah" is one of the two players that **do not participate in SonosNet at
  all** (no mesh role, every matrix cell `00 / 00` or blank). The 2.4 GHz hole documented here
  is the likely reason: Noah cannot hear any SonosNet neighbour.

## Not retrieved

- Whether Noah's Sonos is on Wi-Fi (`WuTangLan-Family`) or wired — the support page does not
  show it and the scan cannot.
