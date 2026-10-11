# Assessment and recommendations

Based on the eleven room scans, the Sonos Network Matrix, and the Omada / EAP screenshots in
`omada/` (21 Sep).

**Access points, confirmed:** **Gallery AP** and **Kitchen AP** (both EAP650(EU) v1.0, managed
by Omada) plus a standalone **EAP330** that is not in Omada. A **Keller AP is powered off**.
Full detail: [`wifi/01-access-points.md`](wifi/01-access-points.md).

---

## 1. Do I agree with your analysis?

**Partly.** You are right that the network is not performing. But two things in the premise
need correcting, and the second one is the actual problem.

### ❌ "Dark green everywhere" is the wrong target

In a multi-AP house, dark green in every room is not a goal — it is a *fault*. If every AP is
heard loudly in every room, all four APs interfere with each other, clients cling to the AP
they first joined instead of roaming, and your usable airtime collapses. A correctly designed
multi-AP network looks like this:

| Where you measure | Healthy reading |
|---|---|
| In the room the AP is mounted in | **-35 to -45 dBm** (dark green) |
| Next room / one floor away | -50 to -60 dBm (green) |
| At the cell edge, where the next AP takes over | around -67 dBm |
| Anywhere you actually use a device | better than -67 dBm on 5 GHz |
| At a Sonos player | better than -65 dBm, ideally -55 |

So: **dark green in four rooms, green-to-yellow between them.** Not dark green everywhere.

### ✅ But your readings really are wrong — just not in the way you thought

Here is every room, with the strongest signal from one of *your* APs and which AP it came from:

| Room | Best 2.4 GHz | Best 5 GHz | Which AP |
|---|---|---|---|
| Wohnzimmer 🔵 *has an AP* | -52 | -55 | **AP-1** |
| Büroecke | -52 | -54 | **AP-1** |
| Galerie | -53 | -53 | **AP-1** |
| Fernsehecke 🔵 *has an AP* | -55 | -53 | **AP-1** |
| Elternbad | -56 | -50 | **AP-1** |
| Noemi | -56 | -59 | **AP-1** |
| Elternschlafzimmer | -57 | -54 | **AP-1** |
| Küche 🔵 *has an AP* | -60 | -55 | **AP-1** |
| Noah | *none live* | -61 | **AP-1** |
| Keller 🔵 *has an AP* | -63 | -68 | AP-2 |
| Nicolas | -64 | -70 | AP-3 / AP-1 |

Read that column on the right. **AP-1 is the strongest AP in nine of eleven rooms — including
the Küche and the Fernsehecke, which are supposed to have their own access points.**

That is the finding. You do not have a four-AP network. You have **one AP doing the work of
four**, which is exactly why every room lands in the same mediocre -52…-64 band: they are all
roughly the same distance from the same single radio.

---

## 2. What is actually wrong

### A. You have three APs, and effectively one of them works

| Doc label | Real device | Model | Managed? | Where it is strongest |
|---|---|---|---|---|
| **AP-1** | **Gallery AP** `6C:4C:BC:76:7C:40` | EAP650(EU) v1.0 | Omada | **everywhere** (-52 … -64) |
| **AP-2** | **Kitchen AP** `6C:4C:BC:76:94:C0` | EAP650(EU) v1.0 | Omada | Keller only (-63) |
| **AP-3** | **EAP330** `84:16:F9:93:E9:2B` | EAP330 (Wi-Fi 5) | **no — standalone** | Nicolas only (-64) |
| — | Keller AP | — | — | **powered off** |

The Gallery AP being the one that reaches everywhere now makes sense: a gallery/landing is
central and open, so it covers the whole house at a mediocre level and no room at a strong one.

### B. Even AP-1 is too quiet in its own room

-52 dBm in the room the AP is mounted in is 10–15 dB below where it should be. Causes, in
order of likelihood: **transmit power set to Low in Omada**, the AP mounted inside a media
cabinet / behind the TV / in the rack, or an antenna/mounting problem.

### C. AP-2 is weak even in its own room and drops out

-63 dBm in the Keller, and during the Küche scan it was **entirely offline** for 6–11 minutes.
An AP that disappears for ten minutes at a time is not a coverage problem, it is a fault.

### D. 🚨 Both EAP650s are now on the *same* channel, on *both* bands

Omada, 21 Sep:

| | 2.4 GHz | 5 GHz |
|---|---|---|
| Gallery AP | **channel 6** | **channel 100** |
| Kitchen AP | **channel 6** | **channel 100** |

One day earlier they were on 11/44 and 1/48. **Auto-channel merged them onto the same channel
on both bands within 24 hours.** Two co-channel APs share the airtime of one instead of adding
capacity, and clients between them collide with both.

And Omada's own channel-utilization measurement, on both APs:

| Band / channel | Utilization |
|---|---|
| **2.4 GHz channel 6** | heavily filled (Gallery) to **almost completely saturated** (Kitchen) |
| **5 GHz channel 100** | essentially **idle** on both |

That is the whole problem in one picture. SonosNet lives on 2.4 GHz, and your 2.4 GHz is full
while 5 GHz sits empty.

The one good thing: they did move 5 GHz to **channel 100**, out of the crowded 36–48 block.
Keep that — just put them on *different* upper channels.

### D2. Only one AP covers most of the house

With the Keller AP off, you have **two APs for eleven rooms**, and the Kitchen AP is beaten by
the Gallery AP in its *own* room's neighbours. Nicolas, the furthest room, is the worst in the
house (-64 / -70).

### E. Your 2.4 GHz band is unusable, and that is what kills Sonos

| Channel | What is on it |
|---|---|
| 1 | AP-2 · Huawei SUN2000 inverter · Vodafone ×3 |
| 6 | AP-3 · FRITZ!Box 7490 · WLAN-A7C604 ×2 · 5 × Tapo bulbs · SG-Gast |
| **11** | **AP-1** · **Fritzbox 6660 at 40 MHz (7–11)** · **AP-3 from 22:45, also 40 MHz** · Epson printer · TS5100 printer |

Two separate radios running **40 MHz channels on 2.4 GHz** (the Fritzbox and, since 22:45,
AP-3) is the single worst thing in this list. 2.4 GHz has room for exactly three 20 MHz
channels; a 40 MHz channel eats two of them.

On top of that, each EAP radio beacons **five SSIDs** (Admin, -Family, -Guest, -IOT, plus a
hidden one) — roughly 30–40 beacon streams burning airtime before any data moves.

### F. Loud radios that should not exist

| Signal | Device | Channel |
|---|---|---|
| **-39 dBm** (Keller) | Fritzbox 6660 Wi-Fi | 2.4 GHz ch 11, **40 MHz** |
| **-40 dBm** (Fernsehecke) | Fritzbox 6660 Wi-Fi | 5 GHz ch 116 |
| **-42 / -47 / -48 dBm** | **Epson ET-4850 Wi-Fi Direct** | 2.4 GHz ch 11 |
| -74 … -78 dBm | TS5100 printer Wi-Fi Direct | 2.4 GHz |

The only true dark-green signals in the entire data set come from a router whose Wi-Fi is
supposed to be off and a printer broadcasting an ad-hoc AP nobody uses.

The Fritzbox is also a **VLAN hole**: in the Nicolas scan your phone was connected to plain
`WuTangLan` at 2401 Mbps — straight to the router, bypassing the EAPs and your VLANs entirely.

### G. All of your 5 GHz radios are in one 80 MHz block

On 20 Sep: Gallery AP on 44 (42), Kitchen AP on 48 (42), the EAP330 on 44 (42), the FRITZ!Box
7490 on 40 (42) — all four in channels 36–48 — with the Fritzbox 6660's 160 MHz channel at
36 (50) over the top.

**By 21 Sep both EAP650s had moved to channel 100**, which is the right band — they just both
went to the *same* channel. The EAP330 is still down in 44 (42). Channels 100–140 are almost
empty; put the two EAP650s on 100 and 116 and leave them there.

### H. The Sonos mesh is three hops deep and rooted in the worst possible place

- **Keller = Root Bridge**, in the basement, next to the -39 dBm Fritzbox. Its own noise floor
  is already degraded (ANI 4).
- **Küche = the only Secondary Node** — the single relay the whole system depends on — in the
  room with the weakest own-AP coverage.
- **Eleven players are Tertiary Nodes**: three hops from the wire. Each SonosNet hop roughly
  halves throughput.
- Nothing reaches the root above link strength **44**. Elternbad (`00/16`), Eltern (`13/17`)
  and Noemi (`16/31`) effectively cannot reach it at all.
- Three players are **red at OFDM ANI 8–9** — radios permanently in maximum interference
  mitigation.
- Several of the *strongest* links in the house sit in STP `blocking` state, because the
  spanning tree is rooted in the basement.
- **Noah and Büroecke are not on SonosNet at all** — they joined over Wi-Fi. Mixing Wi-Fi and
  SonosNet players in one system is itself a known instability.

---

## 3. What to do

Ordered by benefit-per-effort. Steps 1 and 2 are free and can be done tonight.

### Step 0 — ~~Look in Omada~~ — done, see [`wifi/01-access-points.md`](wifi/01-access-points.md)

Still worth noting from Omada, because the photos did not show it: **the transmit power
setting for each radio on both EAP650s**. That is the most likely explanation for -52 dBm in
the Gallery AP's own room.

### Step 1 — Silence the radios that should not be transmitting *(free, biggest Sonos win)*

1. **Fritzbox 6660 → Wi-Fi OFF, both bands, and Mesh/Repeater off.**
   This removes a 40 MHz transmitter at -39 dBm sitting next to the Sonos root bridge, frees
   5 GHz 36–64, and closes the VLAN bypass.
   *It may already be off — both radios stopped being seen at ~22:01 and ~22:05 on 20 Sep.
   Confirm.*
2. **Epson ET-4850 → turn Wi-Fi Direct off.** Keep the printer on the normal network. This is
   the loudest thing on 2.4 GHz channel 11 in three separate rooms. Free, zero downside.
3. **TS5100 printer → same.**
4. **FRITZ!Box 7490 and the `WLAN-A7C604` repeaters** — identify them. If they are yours,
   disable their Wi-Fi (keep DECT on the 7490 if you use it) or unplug them.
5. **Decide the EAP330's fate — adopt it into Omada, or retire it.** It is standalone, runs
   firmware from September 2018, has a clock eight years out of date, serves **zero clients**,
   carries your VLAN SSIDs on 2.4 GHz only, and its 5 GHz radio broadcasts nothing but the
   factory SSID `TP-Link_5G_93E92D`. Given all that, **retiring it is the cleaner option**.
   Leaving it as-is costs you 2.4 GHz airtime for no benefit.

Expected: 2.4 GHz gets dramatically quieter, and the Sonos OFDM ANI values should start
falling within an hour.

### Step 2 — Fix the EAP radio settings in Omada *(free — do this one first if you do nothing else)*

6. **Pin the channels. Both EAP650s are currently on the same channel on both bands** (2.4 ch 6,
   5 GHz ch 100) because auto-channel put them there. Set:

   | | 2.4 GHz | 5 GHz (80 MHz) |
   |---|---|---|
   | **Gallery AP** | channel **1** | channel **100** (centre 106) |
   | **Kitchen AP** | channel **11** | channel **116** (centre 122) |
   | *(SonosNet)* | **channel 6 — leave free** | — |

   Keep them in the upper 5 GHz band: Omada already moved them to 100, and channels 100–140
   are almost empty in every scan in this repo.
7. **2.4 GHz channel width → 20 MHz on both APs.** Non-negotiable. (The EAP330 was running
   40 MHz on 2.4 GHz on 20 Sep.)
8. **Turn off Omada's automatic channel re-optimisation** once you have pinned channels —
   otherwise it will merge them again.
9. **Cut the SSIDs on 2.4 GHz.** Keep only `WuTangLan-Family` and `WuTangLan-IOT` there. Move
   `Admin`, `WuTangLan-Guest` and the hidden SSID to **5 GHz only**. That removes ~40% of the
   2.4 GHz beacon load at no cost to you.
10. **Delete the hidden SSID if you do not use it.** Hiding an SSID adds no security and it
    still beacons.
11. **Check transmit power.** If 2.4 GHz is on Low, that alone explains the missing dark green.
    Set 5 GHz to High and 2.4 GHz to Medium — you want clients pushed onto 5 GHz, but not
    2.4 GHz so weak that Sonos suffers.
12. **Update the EAP650 firmware.** Both are on 1.3.6 with an update flagged in Omada.

### Step 3 — Fix the physical deployment

13. **Turn the Keller AP back on, or remove it from the plan.** With it off you are covering
    eleven rooms with two APs.
14. **The Kitchen AP is underperforming.** It is beaten by the Gallery AP even in the Küche
    (-60/-55 from the Gallery AP vs the Kitchen AP entirely offline for 6–11 minutes during
    that scan). Check its mounting, its PoE port, and its transmit power.
15. **Find the EAP330.** It is strongest in Nicolas (-55 dBm) and weak everywhere else. If you
    keep it, put it where it is needed and adopt it into Omada.
16. **Mount them in the open** — ceiling or high on a wall. Not behind the TV, not in a media
    cabinet, not inside the rack. A closed cabinet costs 10–20 dB.
17. **Move the Omada controller off the laptop.** It runs at `https://127.0.0.1:8043` on the
    HP; when that machine is off you have no controller, no statistics (hence "No Data" health)
    and no consistent channel management. An OC200/OC300, a NAS container or a Raspberry Pi
    fixes it.

### Step 4 — Fix Sonos

16. **Choose one mode and stick to it. Recommendation: SonosNet.** Do not run some players on
    Wi-Fi and some on SonosNet.
17. **Fix the Noemi cable first.** Sonos says Noemi is a *Tertiary Node*, so it is not being
    used as a wired entry point. Check the link light and — most likely culprit — **which VLAN
    that switch port is in.** If the Noemi port is not in the same VLAN as the rest of Sonos,
    the player cannot act as a wired bridge. Same check for every wired Sonos port.
18. **Better still: wire the Wohnzimmer player `B8:E9:37:E6:09:85`.** It is already the de-facto
    hub of the mesh — most of the green links in the house terminate there. Wiring it moves the
    root out of the basement and turns a three-hop tree into roughly a one-hop tree.
19. **Set the SonosNet channel manually to 6** (after step 2 frees it). Sonos app → Settings →
    System → Network → SonosNet Channel.
20. **Take Noah and Büroecke off Wi-Fi** so they join SonosNet — or accept them on Wi-Fi and
    move everything to Wi-Fi. Do not mix.
21. **Reboot, and if needed factory-reset, the Fernsehecke soundbar** (`94:9F:3E:C0:EE:A2`).
    It reports noise floor `0,0,0,0` and ANI `undefined` — it is not reporting radio statistics
    at all, which usually means a stuck radio.
22. **Rename the three players all called "Wohnzimmer"** so diagnostics stay readable.

---

## 4. What to expect

| | Now | After steps 1–2 (one evening, free) | After steps 3–4 |
|---|---|---|---|
| APs on air | 2 managed + 1 unmanaged | 2 managed, EAP330 adopted or retired | 3 managed |
| Both EAP650s co-channel | **yes** — 2.4 ch 6 *and* 5 GHz ch 100 | **no** — pinned 1/11 and 100/116 | no |
| 2.4 GHz ch 6 utilization (Omada) | heavily to **almost fully saturated** | should drop sharply | low |
| Rooms with an AP | -52 … -63 dBm | unchanged | **-35 … -45 dBm** |
| Worst room (Nicolas) | -64 / -70 dBm | unchanged | -50 … -55 dBm |
| Free 2.4 GHz channel for Sonos | none | **channel 6** | channel 6 |
| Sonos OFDM ANI | 3 players at 8–9, 2 at 6 | should fall toward 0–3 | 0–2 |
| SonosNet depth | 1 root + 1 secondary + **11 tertiary** | unchanged | 1 root + mostly **secondary** |
| Sonos streaming | frequent dropouts | noticeably better | stable |

**Steps 1 and 2 cost nothing and should fix most of the Sonos problem on their own.**
Step 3 is what finally gets you the dark green — in the rooms where it belongs.

---

## 5. Caveats

- Device identities are now **confirmed** from the Omada and EAP330 UIs — see
  [`wifi/01-access-points.md`](wifi/01-access-points.md). What is still unknown is **where the
  EAP330 physically sits** and **what transmit power** each EAP650 radio is set to.
- Signal readings come from one phone in one position per room; a metre either way can change
  them by several dB. The *pattern* across eleven rooms is solid; individual numbers are not
  precise.
- Whether the FRITZ!Box 7490 and `WLAN-A7C604` are yours or a neighbour's is still unknown.
- No scan exists for **Eltern**.
- See [`open-questions.md`](open-questions.md) for the full list of what the screenshots
  could not answer.
