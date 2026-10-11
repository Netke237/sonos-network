# Wi-Fi — Keller

Source: `Keller/Screenshot_2026-09-20-22-01-12-393`, `…-22-01-18-819`, `…-22-01-39-811`
(NetSpot / Network Analyzer "Inspector", 1220 × 2712, full resolution).
Time **22:01** · phone on `WuTangLanFamily @ 1201 Mbps` · `Wi-Fi throttling ON`.

> Supersedes the earlier low-resolution `Netlog_Keller.jpg` / `Netlog_Keller_2.jpg`
> (143 px Telegram thumbnails). Those are a different, earlier scan and remain unreadable;
> everything below comes from the new full-resolution screenshots.

## Full list

| SSID | BSSID | Band | Channel | Signal |
|---|---|---|---|---|
| **WuTangLan** (Fritzbox 6660) | 0C:72:74:00:63:9A | 2.4 GHz | **11 (centre 9 → 40 MHz wide)** | **-39 dBm** |
| WuTangLan-Family | 76:4C:BC:76:94:C0 | 2.4 GHz | 1 | -63 dBm |
| WuTangLan-Guest | 7A:4C:BC:76:94:C0 | 2.4 GHz | 1 | -63 dBm |
| WuTangLan-IOT | 7E:4C:BC:76:94:C0 | 2.4 GHz | 1 | -63 dBm |
| WLAN-A7C604 | 1C:23:A2:7A:E3:7A | 2.4 GHz | 1 | -66 dBm |
| WuTangLan-Family *(connected)* | 76:4C:BC:76:94:C1 | 5 GHz | 48 (42) | -68 dBm |
| Admin | 72:4C:BC:76:94:C1 | 5 GHz | 48 (42) | -68 … -70 dBm |
| WuTangLan-Guest | 7A:4C:BC:76:94:C1 | 5 GHz | 48 (42) | -68 … -70 dBm |
| WuTangLan-IOT | 7E:4C:BC:76:94:C1 | 5 GHz | 48 (42) | -68 … -70 dBm |
| WLAN-A7C604 | 1C:23:A2:7A:E3:7B | 5 GHz | **52 (50)** | -75 dBm |
| TP-Link_5G_93E92D | 84:16:F9:93:E9:2D | 5 GHz | 44 (42) | -76 … -79 dBm |
| WuTangLan-IOT | 86:16:F9:BF:E9:2F | 2.4 GHz | — | -82 dBm |

## Assessment

> **The Keller access point is powered off** (confirmed 21 Sep). The readings below are
> therefore coverage *from elsewhere in the house*, not from a local AP.


- **The only strong signal in the basement is the Fritzbox 6660's own Wi-Fi at -39 dBm.**
  That is the one genuine "dark green" reading anywhere in the house — and it is the router
  whose Wi-Fi is supposed to be off.
- **The nearest live AP is the "Kitchen AP"** (`6C:4C:BC:76:94:C0`) at **-63 dBm on 2.4 GHz**
  and **-68 dBm on 5 GHz**. The **Gallery AP** does not appear at all in this scan.
  Notably, the Kitchen AP is the *strongest* AP down here while being **entirely undetectable
  in the Küche itself** — see [`01-access-points.md` §6b](01-access-points.md) — which raises
  the question of where that unit is actually mounted.
- **The Fritzbox is running a 40 MHz channel on 2.4 GHz** — `channel: 11 (9)` means primary 11,
  centre 9, i.e. it occupies channels 7–11. On 2.4 GHz that is bad practice at the best of
  times; here it sits directly on top of AP-1's 2.4 GHz channel 11 **and** on the band SonosNet
  uses, at -39 dBm. This is very likely the single biggest contributor to the Sonos problem.
- `WLAN-A7C604` is dual-band (2.4 ch 1 + 5 GHz ch 52) and also lives down here.

## Why this matters for Sonos

The **Keller Sonos player is the SonosNet Root Bridge**. Its own radio stats are yellow
(OFDM ANI 4, noise floor -106 / -118 / -108), and nothing in the house reaches it above link
strength 44. A root bridge sitting next to a 40 MHz-wide 2.4 GHz router transmitting at
-39 dBm explains that noise floor directly. See `docs/sonos/network-matrix.md`.

## Not retrieved

- Whether there is a physical EAP in the Keller at all, and if so which BSSID it is.
- The exact position of the Fritzbox relative to the Sonos Keller player.
