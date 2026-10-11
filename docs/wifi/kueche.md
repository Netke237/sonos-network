# Wi-Fi — Küche

Source: `küche_2/Screenshot_2026-09-20-22-16-58-390` … `…-22-17-23-753`
(NetSpot / Network Analyzer "Inspector", 1220 × 2712, seven full-resolution captures).
Time **22:16–22:17** · phone on `WuTangLanFamily @ 1201 Mbps` · `Wi-Fi throttling ON`.

> Supersedes `Netlog_Küche.jpg` / `Netlog_Küche_2.jpg` (143 px Telegram thumbnails, unreadable)
> and the contents of the `Küche/` folder, which turned out to hold a copy of the Fernsehecke
> scan. Everything below comes from `küche_2/`.

## Full list — everything the Küche can actually hear

| SSID | BSSID | Band | Channel | Signal |
|---|---|---|---|---|
| **DIRECT-f1-EPSON-ET-4850** | 6A:55:D4:7D:0B:9B | 2.4 GHz | **11** | **-47 dBm** |
| Admin | 72:4C:BC:76:7C:41 | 5 GHz | 44 (42) | **-55 dBm** |
| Vodafone Hotspot | DE:A6:33:43:EC:0E | 2.4 GHz | 1 | -55 dBm |
| WuTangLan-Family | 76:4C:BC:76:7C:41 | 5 GHz | 44 (42) | **-55 dBm** |
| WuTangLan-Guest | 7A:4C:BC:76:7C:41 | 5 GHz | 44 (42) | -55 dBm |
| WuTangLan-IOT | 7E:4C:BC:76:7C:41 | 5 GHz | 44 (42) | -55 dBm |
| WuTangLan-Family | 76:4C:BC:76:7C:40 | 2.4 GHz | 11 | **-60 dBm** |
| Admin | 72:4C:BC:76:7C:40 | 2.4 GHz | 11 | -61 dBm |
| TP-Link_5G_93E92D | 84:16:F9:93:E9:2D | 5 GHz | 44 (42) | -67 dBm |
| Vodafone-DD14 | DC:A6:33:43:EC:0C | 2.4 GHz | 1 | -72 dBm |
| DIRECT-Ub7F-TS5100series | 6E:F2:D8:E7:FA:7F | 2.4 GHz | 1 | -78 dBm |
| WuTangLan-Guest | 7A:4C:BC:76:7C:40 | 2.4 GHz | 11 | -78 dBm |
| WuTangLan-Family | 86:16:F9:BF:E9:2D | 2.4 GHz | 6 | -84 dBm |
| WuTangLan-IOT | 86:16:F9:BF:E9:2F | 2.4 GHz | 6 | -84 dBm |
| WuTangLan-Guest | 86:16:F9:BF:E9:2E | 2.4 GHz | 6 | -86 dBm |

### Offline in this scan (not in the last scan result)

| SSID | BSSID | Band | Channel | Last seen |
|---|---|---|---|---|
| Admin (AP-2) | 72:4C:BC:76:94:C0 | 2.4 GHz | 1 | ~11 min ago |
| Admin (AP-2) | 72:4C:BC:76:94:C1 | 5 GHz | 48 (42) | ~6 min ago |
| Vodafone Homespot | DE:A6:33:43:EC:10 | 2.4 GHz | 1 | ~6 min ago |
| Vodafone-DD14 | DC:A6:33:43:EC:0D | 5 GHz | **60 (58)** | ~6 min ago |
| WLAN-A7C604 | 1C:23:A2:7A:E3:7A | 2.4 GHz | 1 | ~12 min ago |
| WLAN-A7C604 | 1C:23:A2:7A:E3:7B | 5 GHz | 52 (50) | ~12 min ago |
| WLAN-A7C604 | 38:10:D5:8B:10:56 | 2.4 GHz | 1 | ~11 min ago |
| **WuTangLan** (Fritzbox) | 0C:72:74:00:63:9A | 2.4 GHz | 11 (9) | ~16 min ago |
| **WuTangLan** (Fritzbox) | 0C:72:74:00:63:9B | 5 GHz | 116 (114) | ~12 min ago |

## Assessment

- **Better than the old thumbnail scan suggested, but still poor for a room with an EAP in
  it.** The best own signal is **-55 dBm on 5 GHz / -60 dBm on 2.4 GHz**, both from **AP-1**
  (`…76:7C:4x`) — the same AP that serves the Wohnzimmer, the Galerie, the Elternbad and the
  Fernsehecke. AP-1 is doing most of the work in this house.
- **AP-2 is entirely offline here** (last seen 6–11 minutes ago) and **AP-3 is at -84 to
  -86 dBm** — effectively unusable. So the Küche is being covered from somewhere else
  entirely.
- **If there is an EAP in the Küche, this scan does not see it.** A same-room EAP reads
  -30 to -45 dBm. Nothing of yours is within 10 dB of that. This remains the strongest single
  piece of evidence that the Küche EAP is not running, not adopted, or not where you think.
- **The loudest thing in the kitchen is the Epson printer's Wi-Fi Direct AP at -47 dBm on
  2.4 GHz channel 11** — 13 dB louder than your own 2.4 GHz AP, sitting on the same channel,
  and on the band SonosNet uses.
- The Fritzbox is not heard here at all (offline, 12–16 min). The Küche is at the far end of
  the house from it.

## Why this matters for Sonos

The **Küche player is the only Secondary Node in the whole SonosNet mesh** — the single relay
between the Keller root bridge and the eleven Tertiary nodes. Its own radio stats are good
(green, OFDM ANI 0, noise floor -112/-112/-100), but its link to the Keller root is only
**35 / 38** and its links onward are 22–41. The one relay the entire system depends on is
sitting in the weakest-covered room in the house.

See `docs/sonos/network-matrix.md`.

## Not retrieved

- Whether an EAP is physically present in the Küche and powered. **Check the Omada controller
  first** — this is still the cheapest test on the list.

---

## Second scan — 21 Sep, 21:57–21:58 (`Kücke_3/`)

Source: `Kücke_3/Screenshot_2026-09-21-21-57-32-442` … `…-21-58-39-013` (eight
full-resolution captures, two list refreshes).

### What the phone could hear

| SSID | BSSID | Band | Channel | Signal |
|---|---|---|---|---|
| Admin | 72:4C:BC:76:7C:40 | 2.4 GHz | **6** | **-57 dBm** |
| WuTangLan-Family | 76:4C:BC:76:7C:40 | 2.4 GHz | 6 | -57 dBm |
| WuTangLan-IOT | 7E:4C:BC:76:7C:40 | 2.4 GHz | 6 | -60 dBm |
| WuTangLan-Family *(connected)* | 76:4C:BC:76:7C:41 | 5 GHz | **100 (106)** | **-63 dBm** |
| Vodafone-DD14 | DC:A6:33:43:EC:0C | 2.4 GHz | 11 | -68 … -79 dBm |
| Vodafone Homespot / Hotspot | DE:A6:33:43:EC:10 / 0E | 2.4 GHz | 11 | -69 … -90 dBm |
| TP-Link_5G_93E92D *(EAP330)* | 84:16:F9:93:E9:2D | 5 GHz | 36 (42) | -70 dBm |
| WLAN-A7C604 | 1C:23:A2:7A:E3:7A / 38:10:D5:8B:10:56 | 2.4 GHz | 1 | -78 … -80 dBm |
| WuTangLan-Guest / -IOT / -Family *(EAP330)* | 86:16:F9:BF:E9:2E / 2F / 2D | 2.4 GHz | **11** | -78 … -82 dBm |
| DIRECT-Ub7F-TS5100series | 6E:F2:D8:E7:FA:7F | 2.4 GHz | 11 | -83 dBm |
| [Hidden SSID] *(EAP330)* | 84:16:F9:93:E9:2C | 2.4 GHz | 11 | -84 dBm |
| FRITZ!Box 6660 Cable EV *(neighbour)* | 1C:ED:6F:09:35:22 | 2.4 GHz | 11 | -85 dBm |
| Vodafone-DD14 | DC:A6:33:43:EC:0D | 5 GHz | 52 (58) | -92 … -96 dBm |
| WLAN-A7C604 | 38:10:D5:8B:10:57 / 1C:23:A2:7A:E3:7B | 5 GHz | 52 | -93 … -95 dBm |

In the second refresh the Gallery AP's 2.4 GHz SSIDs drop to *"Offline, last seen ~1 min"*.

### ✅ The Kitchen AP is not audible in the kitchen — confirmed on two evenings

**No `…:4C:BC:76:94:C0` or `…:94:C1` entry appears anywhere in the eight screenshots** —
not in the live list, and not in the offline section either. On 20 Sep it was at least listed
as "last seen 6–11 min ago"; tonight it is absent entirely.

The kitchen's only usable coverage is the **Gallery AP**, at -57 dBm (2.4 GHz) / -63 dBm
(5 GHz). Channels 6 and 100 match what Omada showed at 19:02 the same day.

### ✅ The phone's Wi-Fi failed during the scan

| Time | Phone status bar | Meaning |
|---|---|---|
| 21:57 | Wi-Fi icon with **`!`**, weak | connected to `WuTangLan-Family`, **no internet** |
| 21:58 | **no Wi-Fi icon**, mobile 5G only | **Wi-Fi dropped** |
| 21:58 | full Wi-Fi 6 bars | reconnected — banner: **`Connected to WuTangLan at 573Mbps`** |

`WuTangLan` is the **Fritzbox 6660's** SSID, and 573 Mbps is exactly the 2×2 Wi-Fi 6 rate on
a **40 MHz 2.4 GHz** channel — the Fritzbox's configuration (`channel 11 (9)`). So:

- **The Fritzbox Wi-Fi is on** as of 21 Sep, 21:58.
- In the kitchen, the phone fell off your VLAN SSID and onto the Fritzbox, **bypassing the
  EAP/VLAN structure**, because nothing better was reachable.

(The Fritzbox BSSID `0C:72:74:00:63:9A` itself is not visible in the captured part of the
list, so this attribution rests on the SSID name and the 573 Mbps link rate.)

### ❌ Not confirmed: that the Kitchen AP is broken

The evidence says the AP is **transmitting — just not into the kitchen**:

1. Omada showed it **`CONNECTED`** at 19:02 on 21 Sep.
2. At 19:02 Omada showed its 2.4 GHz channel **almost fully utilized** — measured by its own
   radio, so the radio was alive.
3. On 20 Sep it was heard **live at -63 dBm in the Keller** and **-63 dBm in the
   Fernsehecke**.

A dead AP would not have been heard in two other rooms. The most likely explanations, in
order: it is **not physically mounted in the kitchen**; it is **shielded** (behind a fridge,
inside a cabinet, above an extractor hood, behind tiles/metal); or its radio is intermittently
failing.

**Decisive test:** Omada → Devices → *Kitchen AP* → Tools → **Locate** (LED blinks). If it
blinks elsewhere, the kitchen has no AP. If it blinks in the kitchen, move it into the open —
ideally ceiling-mounted.
