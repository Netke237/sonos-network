# Overview — house network and Sonos

## Stated topology

```
Fritzbox 6660 Cable  →  Firewalla Purple  →  Netgear switch  →  TP-Link EAPs (×4)
                                                                 VLANs: WuTangLan · -Family · -Guest (+ -IOT)
```

- Access points, **confirmed from Omada/EAP UIs** (`omada/`, 21 Sep): **Gallery AP** and
  **Kitchen AP** (both EAP650(EU) v1.0, in Omada) plus a standalone **EAP330** not in Omada.
  A **Keller AP is powered off**. Details: [`docs/wifi/01-access-points.md`](wifi/01-access-points.md).
- Sonos VLAN: **WuTangLan-Family**.
- Sonos wired players as stated: **Noemi** and **Keller**.
- Sonos: 14 players, everything else on Wi-Fi/SonosNet.

## Goals

1. Stable VLANs.
2. Stable Sonos — currently barely usable, streaming is difficult.

## What the evidence actually shows

Everything below is sourced from the screenshots in this repo; see the linked pages.

### A. The house has far more radios than the plan describes

Besides the four EAPs, the following are all live and broadcasting:

- the **Fritzbox 6660** itself, SSID `WuTangLan` — **2.4 GHz `channel 11 (9)`, i.e. 40 MHz
  wide, measured at -39 dBm in the Keller**, and 5 GHz on auto-channel (seen at `36 (50)`,
  160 MHz covering 36–64, and at `116 (114)`);
- a **FRITZ!Box 7490** (2.4 ch 6, 5 GHz ch 40/42);
- `WLAN-A7C604` on two BSSIDs (2.4 ch 6);
- your own **EAP330** still broadcasting its factory SSID **`TP-Link_5G_93E92D`** on 5 GHz
  ch 44 — the same channel as the Gallery AP. It is standalone (not in Omada), runs firmware
  from 2018, and has zero clients;
- five Tapo smart bulbs, a Huawei SUN2000 inverter, an Epson printer Wi-Fi Direct AP
  (-42 dBm in the Elternbad, on 2.4 ch 11) and a TS5100 printer.

→ `docs/wifi/00-ap-and-ssid-inventory.md`

### B. Your own 5 GHz radios all sit in the same 80 MHz block

AP-1 on ch 44 (centre 42), AP-2 on ch 48 (centre 42), the TP-Link on ch 44 (centre 42), the
7490 on ch 40 (centre 42) — and the Fritzbox 6660's 160 MHz channel on top of all of them.
The upper band (100–140) is essentially unused by you. This is the main reason 5 GHz feels
slow and unstable despite good-looking signal bars.

### C. Coverage is mid-green at best, never dark green

Best reading from one of **your own EAPs** anywhere in the house: **-52 dBm** (Wohnzimmer,
2.4 GHz). Dark green starts around -50 dBm, and a room *containing* an AP should read
**-30 to -45 dBm**. None of the four rooms that are supposed to have an EAP reads like that —
the Keller measures its nearest EAP at **-63 dBm**, the Küche at **-60 / -55 dBm** from the
*living-room* AP while its own AP-2 is entirely offline.

The only true dark-green signals in the entire data set belong to devices you probably want
silent: the **Fritzbox at -39 / -40 dBm** and the **Epson printer's Wi-Fi Direct AP at
-42 to -48 dBm on 2.4 GHz channel 11**.

**And across all ten measured rooms, AP-1 (`…4C:BC:76:7C:4x`) is the strongest own AP in
eight of them.** One access point is effectively covering the whole house.

→ per-room pages in `docs/wifi/`

### D. Every 2.4 GHz channel is crowded, and each EAP radio carries five SSIDs

Channel 1: AP-2 + solar inverter + (from 22:05) the Vodafone networks. Channel 6: AP-3 +
two Fritz radios + five Tapo bulbs. Channel 11: AP-1 + **the Fritzbox at 40 MHz width (7–11)**
+ the Epson printer.

By 22:45 it is worse: **AP-3 has moved onto channel 11 as well, also at 40 MHz width** —
three of your own 2.4 GHz radios stacked on one channel, two of them 40 MHz wide. On 2.4 GHz
40 MHz should never be used at all.

Each EAP radio beacons `Admin`, `WuTangLan-Family`, `WuTangLan-Guest`, `WuTangLan-IOT` and a
hidden SSID — ~30–40 beacon streams competing for the airtime that is left. And the Fritzbox,
the Fritz repeaters, the Vodafone boxes and AP-3 are all on **auto-channel and visibly moving
between scans**.

**SonosNet lives on 2.4 GHz, on one fixed channel.** This is why Sonos is dying.

### E. The Sonos mesh is three hops deep and running in maximum interference mitigation

- One Root Bridge (**Keller**, in the basement, itself yellow with ANI 4).
- One Secondary Node (**Küche**).
- **Eleven Tertiary Nodes** — three hops from the wire.
- Three players red with **OFDM ANI 9 / 8** (Wohnzimmer B8:E9:37:E5:15:2B, Fernsehecke LR,
  Fernsehecke RR), two more orange at ANI 6.
- Nothing in the house reaches the Root Bridge above link strength **44**; several players
  (Elternbad `00/16`, Eltern `13/17`, Noemi `16/31`) have effectively no path to it.
- Several of the *strongest* links in the house are in STP `blocking` state because the tree is
  rooted in the basement.
- **Noah** and **Büroecke** do not participate in SonosNet at all — almost certainly because
  both joined over WLAN instead. Büroecke has good Wi-Fi (-52 dBm), so it is not a signal
  problem there; Noah had no live 2.4 GHz network at all in its scan.

→ `docs/sonos/network-matrix.md`, `docs/sonos/devices.md`

### F. The two stated wired players do not both behave as wired

Keller is the Root Bridge, so its cable is live. **Noemi shows as a Tertiary Node** — Sonos is
not using a wire there. → `docs/open-questions.md` item 1.

## Where to look next

Read in this order:

1. `docs/source-images.md` — which screenshot is which room.
2. `docs/wifi/00-ap-and-ssid-inventory.md` — the BSSID → radio → channel key.
3. `docs/sonos/network-matrix.md` — the Sonos evidence.
4. `docs/open-questions.md` — the things to check that the screenshots cannot answer.

No changes to the network have been proposed or made in this pass; this is documentation only.
