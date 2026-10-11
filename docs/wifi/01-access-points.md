# Access points — confirmed inventory

Source: the five photos in `omada/`, taken 2026-09-21 (08:12 and 19:02).
This page supersedes the BSSID guesswork in
[`00-ap-and-ssid-inventory.md`](00-ap-and-ssid-inventory.md) — the identities below come
straight from the management UIs.

## 1. The three access points

| Doc label | Real name | Model | Base MAC | IP | Managed by |
|---|---|---|---|---|---|
| **AP-1** | **Gallery AP** | EAP650(EU) v1.0 | `6C:4C:BC:76:7C:40` | 192.168.55.79 | Omada controller |
| **AP-2** | **Kitchen AP** | EAP650(EU) v1.0 | `6C:4C:BC:76:94:C0` | 192.168.55.37 | Omada controller |
| **AP-3** | `EAP330-84-16-F9-93-E9-2B` | **EAP330** hw 1.0/2.0 | `84:16:F9:93:E9:2B` | *(not captured)* | **standalone — not in Omada** |

Plus a fourth unit in the **Keller, which is powered off**. It appears in no scan and in no
management UI, so nothing here describes it. **Three APs are on air.**

### BSSID → device, now confirmed

| Base MAC | Device | Derived BSSIDs seen in the scans |
|---|---|---|
| `6C:4C:BC:76:7C:40` | **Gallery AP** | 2.4 GHz `72/76/7A/7E/82:4C:BC:76:7C:40` · 5 GHz `…:7C:41` |
| `6C:4C:BC:76:94:C0` | **Kitchen AP** | 2.4 GHz `72/76/7A/7E/82:4C:BC:76:94:C0` · 5 GHz `…:94:C1` |
| `84:16:F9:93:E9:2B` | **EAP330** | 2.4 GHz `…:2C` (hidden) + `86:16:F9:BF:E9:2D/2E/2F` · 5 GHz `…:2D` (`TP-Link_5G_93E92D`) |

> ### ⚠️ Correction
>
> An earlier version of this documentation concluded that `TP-Link_5G_93E92D`
> (`84:16:F9:93:E9:2C/2D`) was **probably a neighbour's router**, because it never rose above
> -55 dBm in any room.
>
> **That was wrong.** It is your **EAP330**: the device MAC is `84:16:F9:93:E9:2B`, and
> `…:2C` / `…:2D` are its two radios. `TP-Link_5G_93E92D` is its factory 5 GHz SSID, named
> after the last three MAC bytes `93:E9:2D`, never removed.
>
> The -55 dBm ceiling was real but I drew the wrong conclusion from it. The correct reading is
> that **this AP is very weak everywhere in your house** — which is a finding in itself, not
> evidence of a neighbour.

## 2. Gallery AP (EAP650) — `6C:4C:BC:76:7C:40`

| | |
|---|---|
| Status | CONNECTED |
| Firmware | **1.3.6 — update available** (red dot in Omada) |
| CPU / Memory | 5% / **64%** |
| Upload / Download rate | 0 / 0 |
| Health | **No Data** |
| 2.4 GHz | **channel 6**, b/g/n/ax mixed — channel utilization bar **heavily filled** |
| 5 GHz | **channel 100**, a/n/ac/ax mixed — channel utilization **near zero** |

This is the AP that has been carrying the house: strongest own signal in **eight of ten
measured rooms**. That now makes sense — a gallery/landing is central and open, so it reaches
everywhere at a mediocre level and nowhere at a strong one.

## 3. Kitchen AP (EAP650) — `6C:4C:BC:76:94:C0`

| | |
|---|---|
| Status | CONNECTED |
| Firmware | **1.3.6 — update available** |
| CPU / Memory | 7% / **64%** |
| Upload / Download rate | 0 / 0 |
| Health | **No Data** |
| 2.4 GHz | **channel 6**, b/g/n/ax mixed — utilization bar **almost completely filled** |
| 5 GHz | **channel 100**, a/n/ac/ax mixed — utilization **near zero** |

## 4. 🚨 Both EAP650s are on the *same* channels, on *both* bands

| | Gallery AP | Kitchen AP |
|---|---|---|
| 2.4 GHz | **channel 6** | **channel 6** |
| 5 GHz | **channel 100** | **channel 100** |

Your only two managed access points are **fully co-channel on both bands**. They are not
adding capacity — they are talking over each other. Two APs on the same channel share the
airtime of one, and clients in between get collisions from both.

This is also *new*. In the scans one day earlier (2026-09-20) they were on different channels:

| | 2.4 GHz | 5 GHz |
|---|---|---|
| Gallery AP, 20 Sep | ch 11 | ch 44 (42) |
| Kitchen AP, 20 Sep | ch 1 | ch 48 (42) |
| **Both APs, 21 Sep** | **ch 6** | **ch 100** |

Auto-channel moved them onto the same channel within 24 hours. This is the strongest argument
yet for **pinning channels manually**.

One genuinely good thing did come out of it: they moved **5 GHz to channel 100**, out of the
crowded 36–48 block. Keep that — just put them on *different* channels up there (e.g. 100 and
116).

## 5. 🚨 Channel utilization confirms the whole diagnosis

Omada's own measurement, from both APs:

| Band / channel | Utilization bar |
|---|---|
| **2.4 GHz channel 6** | heavily filled on Gallery AP, **almost completely filled** on Kitchen AP |
| **5 GHz channel 100** | essentially empty on both |

This is the entire Sonos problem in one picture. **SonosNet lives on 2.4 GHz**, and your
2.4 GHz is saturated — by your own two co-channel APs, the EAP330, the printers, the bulbs and
the neighbours. Meanwhile 5 GHz is sitting idle.

## 6. The EAP330 — `84:16:F9:93:E9:2B`

From its own standalone web UI (photo taken 08:12):

| | |
|---|---|
| Device name | `EAP330-84-16-F9-93-E9-2B` |
| Model / hardware | EAP330, hw 1.0/2.0 |
| Firmware | **1.4.0 Build 20180925 Rel. 37155(4555)** — dated **September 2018** |
| System time | **2018-03-05 02:46:07** — clock is wrong by ~8 years (no NTP) |
| Uptime | 31 days 18:46:19 |
| CPU0 / CPU1 / Memory | 2% / 1% / 27% |
| **Total clients** | **0** |
| Managed by | **nobody** — its own standalone UI, "AP List" contains only itself |

### Problems with this unit

1. **It is not in Omada.** It sits outside your controller, so it does not follow your channel
   plan, SSID plan, power settings or firmware policy. That explains every oddity in the scan
   data: a different BSSID scheme, only 3 SSIDs instead of 5, a leftover factory SSID, and a
   2.4 GHz radio that wandered onto `channel 11 (9)` at 40 MHz while the others were elsewhere.
2. **Firmware from September 2018.** Eight years old.
3. **Its clock is wrong by eight years**, so its logs are meaningless and it has no working
   NTP — a sign it may not have correct DNS/gateway settings either.
4. **Zero clients.** Nothing is using it.
5. **Its 5 GHz radio serves only the factory SSID.** `TP-Link_5G_93E92D` is the only SSID on
   `…:2D`. Your three WuTangLan VLAN SSIDs exist on its 2.4 GHz radio only. So half of this AP
   contributes nothing, while still transmitting beacons.
6. **It is weak everywhere** — never above -64 dBm (2.4 GHz) or -55 dBm (5 GHz) in eleven
   rooms, and -82 dBm in the Keller.
7. **It is Wi-Fi 5 (AC), not Wi-Fi 6**, unlike the two EAP650s — so it also drags down any
   client that does attach to it.

### What to do with it

Either **adopt it into Omada** (the EAP330 is supported by the Omada SDN controller; it will
need a firmware update first, and adopting it wipes its standalone config), or **retire it**.
Given that it has zero clients, is eight years old, and its 5 GHz radio is not serving your
VLANs, retiring it is the cleaner option — the two EAP650s already cover more of the house
than it does.

Do **not** leave it as it is. An unmanaged AP that ignores your channel plan and broadcasts a
factory SSID is actively costing you 2.4 GHz airtime.

## 6b. 🚩 Is the "Kitchen AP" actually in the Küche?

Two readings sit badly together:

| Observation | Source |
|---|---|
| In the **Küche**, the phone **could not hear the Kitchen AP at all.** No `…:94:C0` / `…:94:C1` entry is in the live list. Three of its BSSIDs sit in the scanner's *"Offline. Last seen"* section: `72:…:94:C0` Admin 2.4 GHz (~11 min), `72:…:94:C1` Admin 5 GHz (~6 min), `7E:…:94:C0` IOT 2.4 GHz (~11 min). The room was covered only by the **Gallery AP** (-60 / -55 dBm). | `küche_2/` `…22-17-14-559`, `…22-17-23-753` |
| In the **Keller**, the Kitchen AP is the **strongest** AP in the room (-63 dBm 2.4 GHz / -68 dBm 5 GHz), and the Gallery AP is not audible at all. | `Keller/`, 22:01 |
| Omada reports the Kitchen AP as **CONNECTED** the whole time. | `omada/`, 21 Sep |

> **What "offline" means here.** It is the *scanner app's* label for "my phone did not hear
> this in its recent scans". It does **not** mean the AP was switched off or disconnected —
> Omada showed the Kitchen AP as `CONNECTED`. This finding comes from the **Wi-Fi scan**, not
> from the Sonos matrix; the Küche **Sonos player** is healthy in the matrix (green, Secondary
> Node, OFDM ANI 0).
>
> The scan runs with `Wi-Fi throttling ON` (Android limits scan frequency), so one missed scan
> could flag an entry. But 6–11 minutes is several consecutive scans, during which the Gallery
> AP was heard normally. "Last seen ~11 min" at 22:17 ≈ 22:06 — when the phone was in the
> Fernsehecke hearing the Kitchen AP at -63 dBm. It lost it on walking **into** the kitchen.

An access point that cannot be heard in the room it is named after, but is the loudest thing
one floor down, is probably **not mounted where its name says**. Omada names are user-assigned
and do not follow the hardware.

*Worth doing:* physically locate the unit with MAC `6C:4C:BC:76:94:C0` / IP `192.168.55.37`.
Omada can flash its LED (Devices → Kitchen AP → Tools → **Locate**), which makes this a
two-minute job. If it turns out to be in or near the Keller, then the Küche has **no access
point at all** — and the Küche is where the only SonosNet Secondary Node lives.

The alternative explanation is that it *is* in the kitchen but its radios are dropping out
(they were unreachable for 6–11 minutes from the same room), which is a fault rather than a
placement problem. Either way it needs looking at.

## 7. The Omada controller runs on a laptop

The controller UI is at **`https://127.0.0.1:8043`** on the Windows/HP laptop in the photos —
i.e. a **software controller**, not a hardware controller or OC200, and not a cloud controller.
Site name: **`NeubibergerStr`**.

Consequences:

- **When that laptop is off or asleep, you have no controller.** The APs keep serving clients,
  but nothing collects statistics, applies schedules, or makes auto-channel decisions
  consistently.
- This is almost certainly why **Device Health shows "No Data"** for both APs, and why the
  dashboard reads `APs 0 / 0 / 0 / 2` (Good 0, Fair 0, Poor 0, No Data 2).
- It also means channel decisions are made from whatever partial picture the controller had
  when it last ran — another reason to pin channels instead of relying on auto.

If you want the network managed continuously, move the controller to something always-on: an
**OC200/OC300 hardware controller**, a Docker container on a NAS, or a Raspberry Pi.

## 8. Management network

The APs are on **192.168.55.0/24** (192.168.55.79 and 192.168.55.37), while Sonos is on
**192.168.10.0/24** (the support page was at 192.168.10.229). A separate management subnet is
good practice — just make sure the controller can always reach 192.168.55.0/24, or adoption
and statistics will keep failing.

## 9. What this changes in the earlier analysis

| Earlier statement | Now |
|---|---|
| "Four EAPs, only three BSSID groups visible — one is missing." | Correct, and explained: the fourth is the **Keller AP, powered off**. |
| "`TP-Link_5G_93E92D` is probably a neighbour's router." | **Wrong.** It is your EAP330's factory SSID. |
| "AP-1 is the strongest in eight of ten rooms; one AP is covering the house." | Confirmed — and it is the **Gallery AP**, which is why. |
| "APs are all on the living floor / basement, nothing upstairs." | **Wrong.** The Gallery AP is upstairs, and it is the one that works. |
| "Two 40 MHz radios on 2.4 GHz channel 11." | Still true on 20 Sep. By 21 Sep both EAP650s had moved to ch 6 together. |
| "Pin the channels." | Now urgent — auto-channel put both APs on the same channel within a day. |

## 10. Still unknown

- **Where the EAP330 physically is.** It is strongest in **Nicolas** (-55 dBm on 5 GHz,
  -64 dBm on 2.4 GHz) and weak everywhere else, which suggests somewhere near that bedroom —
  but -55 dBm is still not same-room strength, so it may be enclosed or turned down.
- **Transmit power settings** for the two EAP650s — not visible in the photos. This is the
  most likely explanation for -52 dBm in the Gallery AP's own room.
- Whether the EAP330 has a working gateway/DNS (its clock suggests not).
