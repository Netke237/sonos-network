# Sonos Network Matrix — transcription

Source: `Sonos Network.jpg` (`192.168.10.229:1400/support/review`), evening of **2026-09-19**, captures at
21:44 / 22:17 / 22:35. The three captures agree, so the picture below is stable, not a snapshot
of one bad moment.

## 1. Per-player state (row headers)

Colour = the colour Sonos gave the row header. OFDM ANI level is the Sonos interference
counter: **0 = clean, 9 = maximum interference mitigation engaged**.

| Player | BSSID | Role | Noise floor (dBm) | OFDM ANI | Health colour |
|---|---|---|---|---|---|
| Noah | 34:7E:5C:35:B2:C0 | *(no role shown)* | -105, -102, -95 | 0 | green |
| Büroecke | 34:7E:5C:35:B0:F4 | *(no role shown)* | -104, -104, -95 | 0 | green |
| **Keller** | 5C:AA:FD:59:5E:EB | **Root Bridge** | -106, -118, -108 | 4 | yellow |
| Fernsehecke (LF,RF) | 94:9F:3E:C0:EE:A2 | Tertiary Node | 0, 0, 0, 0 | undefined | white |
| Noemi | 54:2A:1B:64:26:81 | Tertiary Node | -100, -100, -100 | 1 | green |
| Wohnzimmer | B8:E9:37:E6:09:85 | Tertiary Node | -110, -107, -100 | 6 | orange |
| Nicolas | 34:7E:5C:36:DE:91 | Tertiary Node | -113, -111, -100 | 0 | green |
| Wohnzimmer | 54:2A:1B:63:FE:6F | Tertiary Node | -111, -110, -100 | 4 | yellow |
| Elternbad | 34:7E:5C:31:CE:29 | Tertiary Node | -110, -111, -100 | 6 | orange |
| Wohnzimmer | B8:E9:37:E5:15:2B | Tertiary Node | -111, -109, -100 | 9 | **red** |
| Küche | 34:7E:5C:38:26:E3 | **Secondary Node** | -112, -112, -100 | 0 | green |
| Eltern | 34:7E:5C:38:28:B1 | Tertiary Node | -110, -108, -100 | 4 | yellow |
| Fernsehecke (LR) | 5C:AA:FD:49:0C:CB | Tertiary Node | -109, -105, -100 | 9 | **red** |
| Fernsehecke (RR) | 94:9F:3E:00:29:2F | Tertiary Node | -108, -110, -100 | 8 | **red** |

### What this says immediately

- **Only one Root Bridge: Keller.** Everything else that participates in SonosNet is a
  Secondary or Tertiary node. Exactly one player (Küche) is Secondary; **eleven players are
  Tertiary**, i.e. three hops from the wire.
- **Noemi is a Tertiary Node**, not a Root Bridge and not Secondary. If Noemi really has an
  Ethernet cable plugged in, SonosNet is not using it — see `open-questions.md`.
- **Three players are red (ANI 9 / 8):** Wohnzimmer B8:E9:37:E5:15:2B, Fernsehecke (LR),
  Fernsehecke (RR). Two more are orange (ANI 6): Wohnzimmer B8:E9:37:E6:09:85 and Elternbad.
  ANI 9 means the radio is fighting continuous interference on the SonosNet channel.
- **Keller (the Root Bridge) itself is yellow with ANI 4** and an unusually spread noise floor
  (-106 / -118 / -108). The root of the mesh is already degraded — everything downstream inherits it.
- **Fernsehecke (LF,RF) reports noise floor 0,0,0,0 and an undefined ANI level.** That is not a
  real measurement; that player is not reporting radio statistics at all.

## 2. Link matrix (Inbound / Outbound, STP state)

Read as: *row player → column player*. Numbers are Sonos link-strength units (higher = better;
practical reading: >=50 good, 35–49 usable, <35 marginal). Blank = no link reported.
Colour is the cell colour Sonos assigned (green = good, yellow = marginal, grey = reported but
not rated).

### Links to Keller (Root Bridge) — the ones that matter most

| From | In / Out | STP |
|---|---|---|
| Fernsehecke (LF,RF) | 30 / 25 | forwarding |
| Noemi | 16 / 31 | undefined |
| Wohnzimmer B8:E9:37:E6:09:85 | 40 / 41 | forwarding |
| Nicolas | 26 / 32 | undefined |
| Wohnzimmer 54:2A:1B:63:FE:6F | 39 / 44 | forwarding |
| Elternbad | 00 / 16 | undefined |
| Wohnzimmer B8:E9:37:E5:15:2B | 24 / 23 | forwarding |
| Küche | 35 / 38 | forwarding (yellow) |
| Eltern | 13 / 17 | undefined |
| Noah | — | (no link) |
| Büroecke | — | (no link) |

**Nothing reaches the Root Bridge above 44.** The best path into the wire is ~40, and several
players (Elternbad 00/16, Eltern 13/17, Noemi 16/31) are effectively not reachable from Keller.

### Links to Küche (the only Secondary Node)

| From | In / Out | STP |
|---|---|---|
| Keller | 38 / 34 | forwarding (yellow) |
| Fernsehecke (LF,RF) | 32 / 00 | undefined |
| Noemi | 28 / 41 | forwarding (yellow) |
| Wohnzimmer B8:E9:37:E6:09:85 | 41 / 41 | forwarding (yellow) |
| Nicolas | 00 / 26 | undefined |
| Wohnzimmer 54:2A:1B:63:FE:6F | 32 / 34 | forwarding |
| Elternbad | 20 / 00 | undefined |
| Wohnzimmer B8:E9:37:E5:15:2B | 26 / 00 | undefined |
| Eltern | 22 / 24 | undefined |

### Links to Wohnzimmer B8:E9:37:E6:09:85 (de-facto hub of the mesh)

| From | In / Out | STP |
|---|---|---|
| Noah | 00 / 00 | undefined |
| Keller | 41 / 40 | undefined |
| Fernsehecke (LF,RF) | 57 / 48 | **forwarding (green)** |
| Noemi | 21 / 34 | undefined |
| Nicolas | 39 / 43 | forwarding (yellow) |
| Wohnzimmer 54:2A:1B:63:FE:6F | 49 / 54 | **forwarding (green)** |
| Elternbad | 34 / 35 | forwarding (yellow) |
| Wohnzimmer B8:E9:37:E5:15:2B | 49 / 46 | **forwarding (green)** |
| Küche | 41 / 41 | forwarding (yellow) |
| Eltern | 32 / 35 | undefined |

### Links to Fernsehecke (LF,RF)

| From | In / Out | STP |
|---|---|---|
| Keller | 25 / 30 | undefined |
| Noemi | 25 / 46 | forwarding |
| Wohnzimmer B8:E9:37:E6:09:85 | 48 / 57 | **forwarding (green)** |
| Nicolas | 38 / 49 | **blocking** |
| Wohnzimmer 54:2A:1B:63:FE:6F | 47 / 57 | forwarding |
| Elternbad | 48 / 57 | **blocking** |
| Wohnzimmer B8:E9:37:E5:15:2B | 52 / 58 | **blocking** |
| Küche | 26 / 32 | undefined |
| Eltern | 43 / 54 | **forwarding (green)** |
| Fernsehecke (LR) | 57 / 66 | **forwarding (green)** |
| Fernsehecke (RR) | 60 / 66 | **forwarding (green)** |

### Links to Noemi

| From | In / Out | STP |
|---|---|---|
| Noah | 00 / 00 | undefined |
| Büroecke | — | (no link) |
| Keller | 31 / 16 | undefined |
| Fernsehecke (LF,RF) | 46 / 25 | **blocking** |
| Wohnzimmer B8:E9:37:E6:09:85 | 34 / 21 | undefined |
| Nicolas | 00 / 00 | undefined |
| Wohnzimmer 54:2A:1B:63:FE:6F | 33 / 23 | **blocking** |
| Elternbad | 39 / 27 | **blocking** |
| Wohnzimmer B8:E9:37:E5:15:2B | 33 / 17 | undefined |
| Küche | 41 / 28 | forwarding (yellow) |
| Eltern | 36 / 23 | undefined |

### Remaining columns

| From \ To | Elternbad | Wz 63:FE:6F | Eltern | Nicolas | Wz E5:15:2B |
|---|---|---|---|---|---|
| Keller | 00 / 00 | 44 / 39 | 16 / 13 | 32 / 24 | 23 / 24 |
| Fernsehecke (LF,RF) | 57 / 48 | 57 / 47 **blocking** | **54 / 43 green** | 49 / 37 | 58 / 52 |
| Noemi | 27 / 39 | 23 / 33 | 23 / 36 | 00 / 00 | 17 / 33 |
| Wz E6:09:85 | 35 / 34 (yellow) | **54 / 49 green** | 35 / 32 | **43 / 38 (yellow)** | **46 / 49 green** |
| Nicolas | 00 / 20 | 40 / 42 **blocking** | 00 / 24 | — | 42 / 49 **blocking** |
| Wz 63:FE:6F | 31 / 34 | — | 33 / 34 | 42 / 40 | 50 / 56 |
| Elternbad | — | 34 / 31 **blocking** | 57 / 54 | 20 / 00 | 37 / 40 **blocking** |
| Wz E5:15:2B | 40 / 37 | 56 / 50 **blocking** | 37 / 33 | 49 / 42 | — |
| Küche | 00 / 19 | 34 / 32 | 24 / 22 | 00 / 00 | 00 / 00 |
| Eltern | 54 / 57 **blocking** | 35 / 33 **blocking** | — | 24 / 00 | 33 / 37 |
| Fernsehecke (LR) / (RR) | — | — | — | — | — |

### Rows with essentially no mesh participation

- **Noah** and **Büroecke**: every matrix cell for these two is blank or `00 / 00 undefined`,
  and neither has a mesh role. They are not participating in SonosNet at all.

  The most likely explanation is simply that **both players joined over WLAN rather than over
  SonosNet** — a Sonos player connected by Wi-Fi does not join the mesh and shows no node role.
  The Büroecke scan (22:45) supports this: Wi-Fi there is good (-52 dBm from AP-1), so the
  player is not short of signal, it is just not on SonosNet. Noah is a different case — that
  room had **no live 2.4 GHz network at all** in its scan, so it may have fallen back to Wi-Fi
  because SonosNet was unreachable.

  Mixing Wi-Fi players and SonosNet players in one system is itself a known source of
  instability: the two halves cannot relay for each other, and group playback has to cross
  between them.
- **Fernsehecke (LR)** and **Fernsehecke (RR)**: they only link to Fernsehecke (LF,RF)
  (57/66 and 60/66, green, forwarding) — correct for bonded surrounds — but their own ANI is
  9 and 8, so those surround links are running in heavy interference.

## 3. Reading of the matrix

1. **The mesh is far too deep.** One Root Bridge (Keller), one Secondary (Küche), eleven
   Tertiary nodes. Every stream to most rooms is Keller → Küche → some node → the player.
   Each SonosNet hop roughly halves throughput and adds latency; three hops is where dropouts start.
2. **Keller is a bad place for the Root Bridge.** The best link into it is 44, and five players
   cannot see it usefully at all. A basement root cannot serve the upper floors.
3. **SonosNet is being jammed.** Five players are orange/red on OFDM ANI (4–9). ANI 9 on three
   players means the radio is permanently in maximum interference-mitigation mode. That matches
   the Wi-Fi scans: SonosNet runs on one fixed 2.4 GHz channel, and the netlogs show 2.4 GHz
   channels 1 / 6 / 11 all crowded (see `docs/wifi/`).
4. **STP is blocking many of the good links.** Several of the strongest links in the house
   (Elternbad→Fernsehecke 48/57, Wz E5:15:2B→Fernsehecke 52/58, Nicolas→Wz E5:15:2B 42/49,
   Wz E5:15:2B→Wz 63:FE:6F 56/50) are in `blocking` state, because the spanning tree is rooted
   in the basement. The mesh is forced onto weaker paths.
5. **The real hub is a Wohnzimmer player (B8:E9:37:E6:09:85)**, not the Root Bridge. Most green
   links in the house terminate there, yet it is itself orange with ANI 6.

## 4. Not retrieved from these screenshots

- Model of each player, firmware version, per-player IP address.
- Which SonosNet channel is in use (that part of the support page was not captured).
- Which players are cabled. Only Keller behaves like a wired root; Noemi does not.
