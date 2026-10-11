# Wi-Fi: what is actually on the air

Derived from all `Netlog_*.jpg` scans (scanner "Inspector"; `Netlog_*.jpg` taken **19 Sep** 19:42–21:14, room folders **20–21 Sep**).
This page is the key to reading the per-room pages: it maps BSSIDs to physical radios.

## 1. Your own radios (identified by BSSID pattern)

TP-Link EAPs use one BSSID per SSID. On your EAPs the **last two bytes identify the radio**
and the **first byte identifies the SSID**:

| First byte | SSID |
|---|---|
| `72:` | Admin |
| `76:` | WuTangLan-Family |
| `7A:` | WuTangLan-Guest |
| `7E:` | WuTangLan-IOT |
| `82:` | [Hidden SSID] |

| Radio (BSSID tail) | Band | Channel | Notes |
|---|---|---|---|
| **AP-1** `…:4C:BC:76:7C:40` | 2.4 GHz | **11** | 5 SSIDs incl. one hidden |
| **AP-1** `…:4C:BC:76:7C:41` | 5 GHz | **44 (centre 42)** | 5 SSIDs incl. one hidden |
| **AP-2** `…:4C:BC:76:94:C0` | 2.4 GHz | **1** | 5 SSIDs |
| **AP-2** `…:4C:BC:76:94:C1` | 5 GHz | **48 (centre 42)** | 5 SSIDs |
| **AP-3** `86:16:F9:BF:E9:2D/2E/2F` | 2.4 GHz | **6** → **11 (centre 9, 40 MHz)** at 22:45 | Family=2D, Guest=2E, IOT=2F. **2.4 GHz only — no 5 GHz BSSID in this family was ever seen.** |
| **Unknown-3** `84:16:F9:93:E9:2D` | 5 GHz | **44 (centre 42)**, once 36 (42) | broadcasts as **`TP-Link_5G_93E92D`** — **no WuTangLan SSID** |
| **Unknown-3** `84:16:F9:93:E9:2C` | 2.4 GHz | 6 → **11 (9)** at 22:45 | broadcasts as **[Hidden SSID]** — no WuTangLan SSID |

> ### ⚠️ Superseded — see [`01-access-points.md`](01-access-points.md)
>
> The Omada / EAP photos in `omada/` (21 Sep) have confirmed every device identity, so the
> BSSID inference on this page is no longer the best source. In particular:
>
> | BSSID family | Device |
> |---|---|
> | `…:4C:BC:76:7C:4x` (AP-1) | **Gallery AP** — EAP650(EU) v1.0, MAC `6C:4C:BC:76:7C:40` |
> | `…:4C:BC:76:94:Cx` (AP-2) | **Kitchen AP** — EAP650(EU) v1.0, MAC `6C:4C:BC:76:94:C0` |
> | `86:16:F9:BF:E9:2x` + `84:16:F9:93:E9:2C/2D` (AP-3) | **EAP330**, MAC `84:16:F9:93:E9:2B` — standalone, not in Omada |
>
> **`TP-Link_5G_93E92D` is yours**, not a neighbour's — it is the EAP330's factory 5 GHz SSID,
> named after the last three bytes of its MAC (`93:E9:2D`). An earlier version of this page
> concluded otherwise from the fact that it never exceeds -55 dBm in any room. That reading
> was wrong: the signal ceiling is real, but it means **that AP is weak everywhere**, not that
> it is next door.
>
> There are **three** access points, not four. The fourth location (Keller) has an AP that is
> **powered off**.

## 2. Your routers, still broadcasting Wi-Fi

| SSID | BSSID | Vendor | Band | Channel(s) observed |
|---|---|---|---|---|
| **WuTangLan** | `0C:72:74:00:63:9A` | AVM | 2.4 GHz | **11 (centre 9 → 40 MHz wide)** |
| **WuTangLan** | `0C:72:74:00:63:9B` | AVM | 5 GHz | **36 (50)** at 21:00 · **116 (114)** at 22:05 |
| FRITZ!Box 6660 Cable EV | `1C:ED:6F:09:35:23` | AVM | 5 GHz | 116 (114) |
| FRITZ!Box 7490 | `38:10:D5:BA:88:B3` | AVM | 2.4 GHz | 6 |
| FRITZ!Box 7490 | `38:10:D5:BA:88:B4` | AVM | 5 GHz | 40 (42) |
| WLAN-A7C604 | `1C:23:A2:7A:E3:7A` | FRITZ | 2.4 GHz | 6 · also seen on 1 |
| WLAN-A7C604 | `1C:23:A2:7A:E3:7B` | FRITZ | 5 GHz | **52 (50)** |
| WLAN-A7C604 | `38:10:D5:8B:10:56` | AVM | 2.4 GHz | 6 · also seen on 1 |

`0C:72:74:00:63:9A/9B` is the **Fritzbox 6660 Cable** broadcasting the plain SSID `WuTangLan`.
In the Nicolas scan the phone was *"Connected to WuTangLan at 2401Mbps"* — i.e. a client
associated straight to the Fritzbox, not to the EAP/VLAN structure. In every other room the
phone was on `WuTangLanFamily at 1201Mbps`.

**Two things the full-resolution 22:01 / 22:05 scans added:**

1. The Fritzbox's 2.4 GHz radio runs **`channel 11 (9)` — a 40 MHz channel occupying 7–11**.
   On 2.4 GHz that is bad practice anywhere; here it sits on top of AP-1's 2.4 GHz channel 11
   *and* on the band SonosNet uses. In the Keller it reads **-39 dBm**, the strongest signal
   measured anywhere in the house.
2. The Fritzbox's 5 GHz radio is on **auto-channel and moving** — `36 (50)` at 21:00,
   `116 (114)` at 22:05. At `36 (50)` its 160 MHz width covers channels 36–64, i.e. every
   channel your EAPs use. The `WLAN-A7C604` and Vodafone networks also change channel between
   scans, so treat every channel number here as "observed at that moment", not fixed.

## 3. Channel picture

### 2.4 GHz

| Channel | Who is on it |
|---|---|
| **1** | AP-2 (5 SSIDs) · SUN2000-HV2280437924 (Huawei inverter) |
| **6** | AP-3 (3 SSIDs + 1 hidden) · WLAN-A7C604 ×2 · FRITZ!Box 7490 · 5× Tapo_Bulb_* · SG-Gast |
| **11** | AP-1 (5 SSIDs) · **Fritzbox 6660 "WuTangLan"** · Vodafone-DD14 · Vodafone Hotspot · Vodafone Homespot · DIRECT-f1-EPSON-ET-4850 · DIRECT-Ub7F-TS5100series |

All three non-overlapping 2.4 GHz channels are occupied, **channel 11 doubly so by your own
Fritzbox and your own AP-1**, and channel 6 is the busiest channel in the house.

### 5 GHz

| Channel (primary/centre) | Who is on it | Occupied 20 MHz channels |
|---|---|---|
| 36 (50) | **Fritzbox 6660 `WuTangLan`** — 160 MHz wide | **36 · 40 · 44 · 48 · 52 · 56 · 60 · 64** |
| 40 (42) | FRITZ!Box 7490 — 80 MHz | 36 · 40 · 44 · 48 |
| **44 (42)** | **AP-1** — 80 MHz | 36 · 40 · 44 · 48 |
| **44 (42)** | TP-Link_5G_93E92D | 36 · 40 · 44 · 48 |
| **48 (42)** | **AP-2** — 80 MHz | 36 · 40 · 44 · 48 |
| 108 (106) | Vodafone-DD14 | neighbour |
| 116 (114) | FRITZ!Box 6660 Cable EV | neighbour/second Fritz radio |

**Every one of your own 5 GHz radios is stacked in the same 80 MHz block (36–48)**, and the
Fritzbox 6660 sits on top of all of them with a 160 MHz channel that covers 36–64. Nothing of
yours uses the upper band (100–140), which is almost empty apart from two neighbour signals.

## 4. SSID count

Each EAP radio is broadcasting up to **5 SSIDs** (Admin, WuTangLan-Family, WuTangLan-Guest,
WuTangLan-IOT, and one hidden SSID). With 3–4 EAPs × 2 bands × 5 SSIDs that is ~30–40 beacon
streams, plus the two Fritzboxes. On 2.4 GHz that alone consumes a significant share of
airtime before a single byte of data moves — and SonosNet lives on 2.4 GHz.

## 5. Signal levels observed (best own-SSID reading per room)

| Room | Best 2.4 GHz | Best 5 GHz | Strongest signal in the room |
|---|---|---|---|
| Wohnzimmer | **-52** (AP-1, ch11) | **-55** (AP-1, ch44) | own AP-1, -52 |
| Galerie | -53 (AP-1, ch11) | -53 (AP-1, ch44) | Tapo_Bulb_9749 -52 |
| Elternschlafzimmer | -57 (AP-1, ch11) | **-54** (AP-1, ch44) | own AP-1, -54 |
| Noemi | **-56** (AP-1, ch11) | -59 (AP-1, ch44) | own AP-1, -56 |
| Elternbad | -56 (AP-1, ch11) | -50 (AP-1, ch44) | DIRECT-f1-EPSON -42 |
| Noah | not seen (offline) | **-61** (AP-1, ch44) | own AP-1, -61 |
| Nicolas | -64 (AP-3, ch6) | -70 (AP-1, ch44) | TP-Link_5G_93E92D -55 |
| **Büroecke** (22:45, full-res) | **-52** (AP-1, ch11) | -54 (AP-1, ch44) | own AP-1, -52 |
| **Fernsehecke** (22:05, full-res) | -55 (AP-1, ch11) | -53 (AP-1, ch44) | **Fritzbox `WuTangLan` -40** |
| **Küche** (22:17, full-res) | -60 (AP-1, ch11) | -55 (AP-1, ch44) | **Epson Wi-Fi Direct -47** |
| **Keller** (22:01, full-res) | **-63** (AP-2, ch1) | **-68** (AP-2, ch48) | **Fritzbox `WuTangLan` -39** |

### Why you never see dark green

The colour bands are roughly: dark green better than about **-50 dBm**, green -50…-60,
yellow-green/yellow -60…-70, orange -70…-80, red worse than -80.

**The best reading from one of your own EAPs anywhere in the house is -52 dBm.** In a room
that *contains* an EAP you should read **-30 to -45 dBm**. You do not, in any room — including
the four rooms you say have an EAP (Keller, Küche, Wohnzimmer, Fernsehecke).

The only genuine dark-green readings in the whole data set come from devices you probably
want silent:

| Signal | What it is | Where |
|---|---|---|
| **-39 dBm** | Fritzbox 6660, 2.4 GHz ch 11 (40 MHz wide) | Keller |
| **-40 dBm** | Fritzbox 6660, 5 GHz ch 116 | Fernsehecke |
| **-42 dBm** | Epson ET-4850 Wi-Fi Direct, 2.4 GHz ch 11 | Elternbad |
| **-47 dBm** | Epson ET-4850 Wi-Fi Direct, 2.4 GHz ch 11 | Küche |
| **-48 dBm** | Epson ET-4850 Wi-Fi Direct, 2.4 GHz ch 11 | Fernsehecke |

So the house is not short of RF energy — it is short of RF energy *from the right radios*.
For the EAPs that points at one of: transmit power turned down, EAPs mounted inside cabinets
or behind metal, or EAPs that are not where you think / not running.

### AP-1 is carrying the house

With ten rooms now measured, **AP-1 (`…4C:BC:76:7C:4x`) is the strongest own-network signal in
eight of them** — Wohnzimmer, Galerie, Elternschlafzimmer, Elternbad, Noemi, Noah, Küche,
Fernsehecke and Büroecke. AP-2 (`…76:94:Cx`) only wins in the Keller (-63 dBm), is **entirely
offline in the Küche scan**, and reads -83 to -92 dBm in the Büroecke. AP-3 only wins in
Nicolas (-64 dBm) and is at -72 to -86 dBm elsewhere.

One access point is effectively serving the whole house. That is the coverage problem in one
sentence.

## 6. Note on "Offline. Last seen ~ N mins ago"

Every scan shows `Wi-Fi throttling ON` in the status line. Android then limits the app to
~4 scans per 2 minutes, so an entry marked *offline* means "not in the most recent scan
result", not necessarily "gone". Treat single offline entries as weak/flapping rather than
absent — except where a whole band is offline (Noah, 2.4 GHz), which is a real gap.
