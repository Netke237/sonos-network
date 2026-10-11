# Wi-Fi — Noemi

Source image: `Netlog_Noemi.jpg` (Telegram caption **"Noemi"**, `IMG_20260920_092335_591.jpg`).
NetX Inspector · 21:08 · phone on `WuTangLanFamily @ 1201 Mbps` · `Wi-Fi throttling ON` ·
~7 screens.

## Top of the list

| SSID | BSSID | Band | Channel | Signal |
|---|---|---|---|---|
| WuTangLan-Family | 76:4C:BC:76:7C:40 | 2.4 GHz | 11 | **-56 dBm** |
| Admin | 72:4C:BC:76:7C:41 | 5 GHz | 44 (42) | -59 dBm |
| WuTangLan-Guest | 7A:4C:BC:76:7C:41 | 5 GHz | 44 (42) | -59 dBm |
| WuTangLan-IOT | 7E:4C:BC:76:7C:41 | 5 GHz | 44 (42) | -59 dBm |
| Admin | 72:4C:BC:76:7C:40 | 2.4 GHz | 11 | -60 dBm |
| WuTangLan-Family *(connected)* | 76:4C:BC:76:7C:41 | 5 GHz | 44 (42) | **-61 dBm** |

Only **AP-1** appears at the top of the list in this room. AP-2 and AP-3 are further down /
in the offline section.

## Assessment

- AP-1 at -56 dBm (2.4) / -59 dBm (5) — mid-green, nothing better.
- You said Noemi has a **cable** for its Sonos player. The Sonos support page contradicts
  that: Noemi is listed as a **Tertiary Node** (i.e. three hops of SonosNet away from the
  wire), not a Root Bridge and not a Secondary Node, and its link to the Keller root is only
  `16 / 31`. If a cable is really plugged in and active, Sonos is not seeing it.
  See `docs/open-questions.md` — this is the single most worthwhile thing to check first.

## Not retrieved

- Whether the Ethernet run to Noemi is live (link light, correct VLAN/port on the Netgear
  switch). Not visible in any screenshot.
