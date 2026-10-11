# Open questions / information not retrievable from the screenshots

Ordered by how much the answer would change the diagnosis.

## 1. Is the Noemi Ethernet cable actually live?

You said Noemi and Keller have cable. Sonos shows **Keller = Root Bridge** (so that cable is
live) but **Noemi = Tertiary Node** — three SonosNet hops from the wire. A second wired player
would normally show as an additional Root Bridge / a much shallower tree.

*Check:* link light on the Noemi player and on the Netgear switch port; which VLAN that port is
in. A Sonos player on a different VLAN from the rest will still associate over SonosNet but
will not act as a wired entry point.

## 2. Where is the AP labelled "Kitchen AP" actually mounted?

**Resolved:** the **Keller AP is powered off** — that is why nothing in the basement reads
like a local access point. Three APs are on air: Gallery AP, Kitchen AP, EAP330.

**Still open, and more interesting:** the Kitchen AP does not behave like a kitchen AP.

| Room | Kitchen AP (`6C:4C:BC:76:94:C0`) | Gallery AP |
|---|---|---|
| **Küche** (22:17) | **phone could not hear it** — not in the live list; in the scanner's "last seen" section at 6–11 min | -60 / -55 dBm |
| **Keller** (22:01) | **-63 / -68 dBm — the strongest AP in the room** | not audible |

Omada reports it CONNECTED throughout. ("Offline" is the scanner's label for *not heard by the phone*, not an AP fault — and this comes from the Wi-Fi scan, not the Sonos matrix, where the Küche player is healthy.) An AP that cannot be heard in the room it is named
after, but is the loudest thing a floor below, is probably not mounted where its name says.

*Check:* Omada → Devices → Kitchen AP → Tools → **Locate** (flashes its LED). Two minutes.
- If it is in or near the **Keller** → the **Küche has no AP at all**, and the Küche hosts the
  only SonosNet Secondary Node.
- If it really is in the Küche → its radios dropped out for 6–11 minutes as seen from the same
  room, which is a fault. Check its mounting, PoE port and transmit power.

## 3. ~~Is `TP-Link_5G_93E92D` yours or a neighbour's?~~ — resolved: **yours**

It is your **EAP330** (`84:16:F9:93:E9:2B`), broadcasting its factory 5 GHz SSID, named after
the last three bytes of its MAC. `…:2C` and `…:2D` are its two radios. My earlier "probably a
neighbour's" reading was wrong — the -55 dBm ceiling is real, but it means that AP is **weak
everywhere**, not that it is next door.

**What remains open about it:**

- **Where is it physically?** Strongest in Nicolas (-55 dBm 5 GHz / -64 dBm 2.4 GHz), weak
  everywhere else, -82 dBm in the Keller. Not same-room strength anywhere.
- **Adopt it or retire it?** It is standalone (not in Omada), firmware from **September 2018**,
  clock wrong by eight years, **zero clients**, and its 5 GHz radio carries only the factory
  SSID — your three VLAN SSIDs exist on its 2.4 GHz radio only. See
  [`wifi/01-access-points.md`](wifi/01-access-points.md).

## 3b. 🚨 Both EAP650s are on the same channel — pin them now

As of 21 Sep both **Gallery AP** and **Kitchen AP** report 2.4 GHz **channel 6** and 5 GHz
**channel 100**. One day earlier they were on 11/44 and 1/48. Auto-channel merged them onto
the same channel on both bands within 24 hours — they now share airtime instead of adding
capacity.

Omada's own channel-utilization bars on both APs show **2.4 GHz channel 6 heavily to almost
completely saturated**, and **5 GHz channel 100 essentially idle**.

*Do:* pin 2.4 GHz to 1 and 11 (leave 6 for SonosNet), and pin 5 GHz to two different channels
in the upper band, e.g. 100 and 116.

## 3c. The Omada controller runs on a laptop

The UI is at `https://127.0.0.1:8043` on the HP laptop — a software controller. When that
machine is off, nothing manages the APs, which is almost certainly why **Device Health reads
"No Data"** for both and the dashboard shows `APs 0/0/0/2`.

*Consider:* an OC200/OC300, a Docker container on a NAS, or a Raspberry Pi so the controller
is always on.

## 4. Why is the Fritzbox 6660 still broadcasting Wi-Fi? *(now the top suspect)*

The full-resolution 22:01 / 22:05 scans made this much worse than it first looked:

- **2.4 GHz: `channel 11 (9)` — a 40 MHz-wide channel occupying 7–11**, measured at
  **-39 dBm in the Keller**. That is the strongest signal anywhere in the house, it sits on
  top of AP-1's 2.4 GHz channel, and it sits on the band SonosNet uses — right next to the
  SonosNet **Root Bridge**, which is the Keller player.
- **5 GHz: auto-channel and roaming** — `36 (50)` at 21:00 (160 MHz, covering 36–64, i.e. every
  channel your EAPs use), `116 (114)` at 22:05, measured at -40 dBm.
- In the Nicolas scan a client (your phone) was associated to it at 2401 Mbps, bypassing the
  EAP/VLAN structure entirely.

*Check:* if the intent is Fritzbox → Firewalla → switch → EAPs with VLANs on the EAPs, the
Fritzbox radios should be **off**. Leaving them on (a) blankets your 5 GHz low band,
(b) puts a loud 40 MHz transmitter on 2.4 GHz next to the Sonos root bridge, and (c) gives
clients a way onto a network that bypasses your VLANs.

## 4b. ~~Which room is the 22:05 scan?~~ — resolved

The 22:05 set is the **Fernsehecke**; the Küche was re-scanned separately in `küche_2/`
at 22:16–22:17. Both rooms are now documented.

## 5. ~~Which physical EAP is which BSSID?~~ — resolved

Confirmed from the Omada and EAP330 screenshots in `omada/`: `…76:7C:4x` = **Gallery AP**,
`…76:94:Cx` = **Kitchen AP** (both EAP650), `84:16:F9:93:E9:2B` family = **EAP330**
(standalone). The Keller AP is powered off. See
[`wifi/01-access-points.md`](wifi/01-access-points.md).

## 6. Why 5 SSIDs per radio?

Each EAP radio broadcasts `Admin`, `WuTangLan-Family`, `WuTangLan-Guest`, `WuTangLan-IOT`
**and a hidden SSID** — five per radio, ten per EAP. You described three VLANs.

*Check:* what the `Admin` SSID and the hidden SSID are for, and whether either can be
restricted to 5 GHz or removed. Every extra SSID costs 2.4 GHz airtime that SonosNet needs.

## 7. Sonos details not on the captured page

- Model and firmware of each player.
- Which SonosNet channel is in use (the support page section showing it was not captured).
- Per-player IP addresses.
- Whether Noah and Büroecke are on Wi-Fi (`WuTangLan-Family`) — they have no SonosNet role and
  no mesh links at all.

*Check:* Sonos app → Settings → System → About My System, or
`http://<player-ip>:1400/support/review` scrolled to the top section.

## 8. Missing netlogs

Only **Eltern** (as distinct from Elternschlafzimmer) still has no scan.

## 8c. Did you switch the Fritzbox Wi-Fi off at ~22:00?

> **Update 21 Sep, 21:58:** the Fritzbox Wi-Fi is **on**. In the second Küche scan the phone
> dropped off `WuTangLan-Family` and reconnected to **`WuTangLan` at 573 Mbps** — the
> Fritzbox's SSID, at exactly its 40 MHz 2.4 GHz link rate. Whatever happened on 20 Sep, it
> is broadcasting now and clients are falling back onto it. See [`wifi/kueche.md`](wifi/kueche.md).

Across three independent scans the Fritzbox's two radios stop at a fixed wall-clock time and
never reappear: 2.4 GHz last seen **~22:01**, 5 GHz last seen **~22:05**. The Fritz repeaters
(`WLAN-A7C604`) stop at ~22:05–22:06 too. The Fernsehecke scan at 22:05 still saw the
Fritzbox 5 GHz at -40 dBm while its 2.4 GHz had already been gone four minutes — both radios
are in the same box, so distance alone does not explain that.

*Check:* if you did disable it, that is exactly the right move. If you did not, the Fritzbox
may have rebooted or dropped its radios by itself, which is worth knowing.
Details in [`docs/wifi/bueroecke.md`](wifi/bueroecke.md).

## 8b. The Epson ET-4850's Wi-Fi Direct AP

`DIRECT-f1-EPSON-ET-4850` (`6A:55:D4:7D:0B:9B`) is on **2.4 GHz channel 11 — AP-1's channel
and the band SonosNet uses** — and it is one of the loudest signals in the house:
**-42 dBm** (Elternbad), **-47 dBm** (Küche), **-48 dBm** (Fernsehecke), -59 dBm (Wohnzimmer).

*Check:* the printer's network settings — Wi-Fi Direct can usually be turned off entirely
while keeping the printer on the normal network. Free win, costs nothing.

## 9. Everything is on auto-channel — and AP-3 is now 40 MHz on 2.4 GHz

Channel numbers move between scans:

| Radio | Seen on |
|---|---|
| Fritzbox 6660, 5 GHz | 36 (50) at 21:00 · 116 (114) at 22:05 |
| Fritzbox 6660, 2.4 GHz | **11 (9) — 40 MHz wide**, throughout |
| `WLAN-A7C604`, 2.4 GHz | 6 in most scans · 1 at 22:01 and later |
| Vodafone-DD14 / Hotspot / Homespot, 2.4 GHz | 11 at 21:14 · 1 from 22:05 on |
| Vodafone-DD14, 5 GHz | 108 (106) at 21:00 · 60 (58) at 22:17 |
| **AP-3** (`86:16:F9:BF:E9:2x`), 2.4 GHz | 6 in most scans · 1 in the Elternbad capture · **11 (9), 40 MHz wide, at 22:45** |

**The AP-3 move is the serious one.** At 22:45 it sits on `channel 11 (9)` — a 40 MHz channel
occupying 7–11 — directly on top of AP-1's 2.4 GHz channel 11, with the Epson printer there
too. On 2.4 GHz, 40 MHz should never be used at all: it leaves no clean channel for anything
else, SonosNet included.

*Check, in Omada:*
1. Set **2.4 GHz channel width to 20 MHz** on every EAP. Non-negotiable.
2. **Pin** the EAPs to fixed, non-overlapping 2.4 GHz channels (1 / 6 / 11) instead of auto.
3. Pin 5 GHz to spread across the band rather than all sitting in 36–48.

With this many radios hunting for a clear channel simultaneously, auto-channel makes the
situation oscillate — and SonosNet, which sits on one fixed channel, cannot follow.

---

## 10. Netgear switch model and STP architecture — RESOLVED (5 Oct 2026)

- **Device:** **NETGEAR GS316EP** (16-Port Gigabit PoE+ Smart Managed Plus Switch, 15 PoE+ ports).
- **IP Address:** `192.168.55.155` (Management VLAN 55).
- **Web UI:** `http://192.168.55.155/homepage.html` (`/wmi/login`).
- **Known Port Mappings:**
  - Port 1: `Firewalla In` (Uplink to Firewalla Purple)
  - Port 2: `Basem. Laptop`
  - Port 3: `Desktop`
  - Port 4: `MiniComputer`
  - Port 5: `Nicolas`
  - Port 6: `Noemi`
- **STP Capabilities & Architecture:**
  - The GS316EP is a **Smart Managed Plus** switch: it does **not** have an active IEEE 802.1D/802.1w STP bridge engine (no configurable bridge priority or STP toggle).
  - It operates in **BPDU Flooding / Pass-Through Mode**, transparently forwarding IEEE 802.1D BPDUs between ports.
  - Sonos handles loop prevention internally between wired units via SonosNet STP.
  - **Critical Settings for Sonos:**
    1. `Loop Detection / Prevention` under Diagnostics must remain **DISABLED** (prevents switch from shutting down Sonos ports).
    2. `Broadcast Filtering` under Switching -> QoS must remain **DISABLED** (prevents dropping Sonos SSDP discovery).
    3. All wired Sonos ports (Port 6 Noemi, Wohnzimmer, Keller) must be configured as **Untagged VLAN 10 (`WuTangLan-Family`) with PVID = 10**.

