# House-Wide Network Availability & Room-by-Room Audit

**Repository:** Residential Network & Sonos System  
**Document Created:** 4 October 2026  
**Status:** Grounded in NetX Inspector captures, Omada Controller diagnostics, and live Atheros Rincon driver telemetry.

---

## 1. Executive Channel & AP Architecture (As of 4 Oct 2026)

| Network Element | Hardware / Entity | Band & Channel | Channel Width | Status & Role |
|---|---|---|---|---|
| **Galerie AP** | TP-Link EAP650 EU v1.0 (`...:7C:40` / `:7C:41`) | **2.4 GHz Ch 1**<br>**5 GHz Ch 44 (center 42)** | 20 MHz<br>80 MHz | **Active & Relocated** — Restored off DFS Ch 100 to non-DFS Ch 44. Provides house-wide 1201 Mbps Wi-Fi 6 coverage. |
| **Kitchen AP** | TP-Link EAP650 EU v1.0 (`...:94:C0` / `:94:C1`) | **2.4 GHz Ch 11**<br>**5 GHz Ch 40 (center 38)** | 20 MHz<br>40 MHz | **Active** — Primary coverage for kitchen, garden side, and ground floor rear. |
| **SonosNet Mesh** | 14-Player Sonos System | **2.4 GHz Ch 6** (2437 MHz) | 20 MHz | **Protected** — Channels 1 and 11 are pinned to APs, leaving Channel 6 dedicated to SonosNet. |
| **Sonos HT Backhaul** | Fernsehecke Beam ➔ Surrounds | **5 GHz Ch 48** (5240 MHz) | 40/80 MHz | **Active** — Direct low-latency wireless link for surround channels. |
| **EAP330 Standalone** | TP-Link EAP330 (`84:16:F9...`) | 2.4 GHz Ch 11 / 5 GHz Ch 36 | 40 MHz | **RETIRED & POWERED OFF** — Eliminates historical Ch 11 co-channel conflict with Kitchen AP. |
| **Epson ET-4850** | Wi-Fi Direct (`6A:55:D4...`) | 2.4 GHz Ch 11 / Ch 1 | 20 MHz | **DISABLED** — Eliminates house-wide -42 to -47 dBm rogue interference. |
| **Keller AP** | Standalone TP-Link AP | — | — | **Powered Off** |

---

## 2. Room-by-Room Network Availability & Telemetry

### 2.1 Elternbad (Master Bathroom)
- **Date of Last Data Update:** **4 October 2026, 22:19**
- **Data Source:** NetX Inspector scan on phone (Wi-Fi 6, `WuTangLanFamily @ 1201 Mbps`, 4 screens) + Atheros Rincon driver telemetry.
- **Wi-Fi Availability:**
  - **5 GHz (Galerie AP, Ch 44 @ 80 MHz):** **`-55 dBm`** (`76:4C:BC:76:7C:41`) — **Dark Green, Superb**. Max Wi-Fi 6 link rate: **1201 Mbps**.
  - **5 GHz (Kitchen AP, Ch 40 @ 40 MHz):** **`-91 to -92 dBm`** (`76:4C:BC:76:94:C1`) — Weak / Distant.
  - **2.4 GHz (Galerie AP, Ch 1 @ 20 MHz):** **`-60 to -61 dBm`** (`76:4C:BC:76:7C:40`) — **Solid Green**.
  - **2.4 GHz (Kitchen AP, Ch 11 @ 20 MHz):** **`-85 to -86 dBm`** (`76:4C:BC:76:94:C0`) — Distant.
- **External / Neighbor RF:**
  - `WLAN-A7C604`: 2.4 GHz Ch 11 at `-84 dBm`
  - `Vodafone-DD14`: 2.4 GHz Ch 11 at `-87 dBm`
  - `Vodafone Hotspot`: 2.4 GHz Ch 11 at `-88 dBm`
- **Interference Delta:**
  - The historical **`-42 dBm` Epson Wi-Fi Direct blast on Channel 11 is 100% ELIMINATED**.
  - The EAP330 factory SSID is completely off the air.
- **Sonos Player in Room:**
  - Model: IKEA SYMFONISK Bookshelf (`RINCON_347E5C31CE2801400`, IP `192.168.10.113`)
  - Connection Mode: **SonosNet Wireless (Ch 6)**
  - Signal / Mesh Links: **SNR 57 / 58 dB to Eltern Bookshelf**; **SNR 54 / 48 dB to Beam**; **0 dB / 0 dB to Keller** (unreachable directly from basement).
  - RF Health: Historically ANI 6; current mesh hops through Eltern/Beam.

---

### 2.2 Noemi (Bedroom)
- **Date of Last Data Update:** **4 October 2026, 20:41**
- **Data Source:** NetX Inspector scan on phone (`WuTangLanFamily @ 573 Mbps`, 4 screens) + Sonos topology probe.
- **Wi-Fi Availability:**
  - **5 GHz (Kitchen AP, Ch 40 @ 40 MHz):** **`-72 dBm`** (`76:4C:BC:76:94:C1`) — Yellow / Acceptable (connected at 573 Mbps).
  - **5 GHz (Galerie AP, Ch 44 @ 80 MHz):** **`-84 to -85 dBm`** (`76:4C:BC:76:7C:41`) — Weak.
  - **2.4 GHz (Kitchen AP, Ch 11 @ 20 MHz):** **`-70 to -77 dBm`** (`76:4C:BC:76:94:C0`) — Yellow / Marginal.
  - **2.4 GHz (Galerie AP, Ch 1 @ 20 MHz):** **`-80 dBm`** (`76:4C:BC:76:7C:40`) — Weak.
- **External / Neighbor RF:**
  - `WLAN-A7C604`: **`-71 dBm` on 2.4 GHz Ch 11** (Loud co-channel contention against Kitchen AP).
  - `WLAN-A7C604`: `-81 dBm` on 5 GHz Ch 52.
  - `WLAN-135463`: `-83 dBm` on 2.4 GHz Ch 1.
- **Sonos Player in Room:**
  - Model: IKEA SYMFONISK Bookshelf (`RINCON_542A1B64268001400`, MAC `54:2A:1B:64:26:80`)
  - Current Status: **Offline / Reconnecting** (Flashing white light pending factory reset/cable check).
  - Connection Recommendation: **Ethernet cable (LAN) on VLAN 10**. Wi-Fi in this room on 2.4 GHz is marginal (-70 to -77 dBm) and suffers neighbor contention on Ch 11.

---

### 2.3 Galerie
- **Date of Last Data Update:** **4 October 2026, 17:00**
- **Data Source:** Post-relocation NetX Inspector scan + Omada Controller live telemetry.
- **Wi-Fi Availability:**
  - **5 GHz (Galerie AP, Ch 44 @ 80 MHz):** **`-45 to -53 dBm`** (`76:4C:BC:76:7C:41`) — **Dark Green, Pristine**. Max link rate: **1201 Mbps**.
  - **2.4 GHz (Galerie AP, Ch 1 @ 20 MHz):** **`-48 to -55 dBm`** (`76:4C:BC:76:7C:40`) — **Dark Green**.
  - **5 GHz (Kitchen AP, Ch 40):** Distant (-75 to -80 dBm).
- **Physical AP State:** Galerie EAP650 physically relocated away from the soundbar. 5 GHz restored via non-DFS Channel 44 (eliminating DFS radar quiet periods).
- **Sonos Presence:** Soundbar (Beam) and surrounds are situated on the main floor below the Galerie opening. Workstation non-Wi-Fi hash (docks, power supplies) isolated above Wohnzimmer Play:1.

---

### 2.4 Wohnzimmer (Living Room)
- **Date of Last Data Update:** **4 October 2026, 19:06**
- **Data Source:** NetX Inspector scan + live Atheros Rincon driver telemetry over UPnP port 1400.
- **Wi-Fi Availability:**
  - **5 GHz (Galerie AP, Ch 44 @ 80 MHz):** **`-54 dBm`** — **Dark Green**.
  - **2.4 GHz (Galerie AP, Ch 1 @ 20 MHz):** **`-52 dBm`** — **Dark Green**.
  - **EAP330 Status:** Powered off. Living room clients cleanly migrated to Galerie and Kitchen APs.
- **Sonos Players in Room (3 Players):**
  1. **Wohnzimmer 1 (Play:1 far, `15-2A-7`):** IP `192.168.10.101` | Ch 6 | **OFDM ANI: 9 (Severe)** | Noise: -110 dBm | PHY Errors: ~1,126 err/s. (Interference confirmed as non-Wi-Fi RF from Galerie workstation above).
  2. **Wohnzimmer 2 (Play:1 near, `09-84-1`):** IP `192.168.10.160` | Ch 6 | **OFDM ANI: 9 (Severe)** | Noise: -110 dBm | PHY Errors: ~789 err/s.
  3. **Wohnzimmer 3 (Bookshelf, `FE-6E-E`):** IP `192.168.10.230` | Ch 6 | **OFDM ANI: 6 (Moderate)** | Noise: -111 dBm | Links: 30–57 dB SNR to all speakers house-wide. **Prime candidate for wired STP root**.

---

### 2.5 Fernsehecke (Home Theater Area)
- **Date of Last Data Update:** **4 October 2026, 19:06**
- **Data Source:** Live Atheros Rincon driver query + historical scan baseline (20 Sep 22:01).
- **Wi-Fi Availability:**
  - **5 GHz (Galerie AP, Ch 44):** **`-55 dBm`** — Solid Green.
  - **2.4 GHz (Galerie AP, Ch 1):** **`-58 dBm`** — Solid Green.
  - **2.4 GHz (Kitchen AP, Ch 11):** **`-68 dBm`** — Yellow.
- **Sonos Players in Room (Home Theater Setup):**
  1. **Beam (Front LF,RF):** IP `192.168.10.241` | SonosNet Ch 6 | HT Backhaul Ch 48 (5 GHz) | Links: **49 to 63 dB SNR** across all active rooms.
  2. **Fernsehecke Left Surround (LR):** IP `192.168.10.102` | **5 GHz Ch 48 (Satellite)** | **OFDM ANI: 0 (Clean)** | Noise: -106 dBm.
  3. **Fernsehecke Right Surround (RR):** MAC `94:9F:3E:00:29:2E` | Bonded 5 GHz surround to Beam.

---

### 2.6 Küche (Kitchen)
- **Date of Last Data Update:** **4 October 2026, 19:06**
- **Data Source:** Live Atheros Rincon telemetry + historical scan baseline (21 Sep 21:58).
- **Wi-Fi Availability:**
  - **2.4 GHz (Kitchen AP, Ch 11 @ 20 MHz):** Local access point.
  - **5 GHz (Kitchen AP, Ch 40 @ 40 MHz):** Local access point.
  - **5 GHz (Galerie AP, Ch 44 @ 80 MHz):** **`-55 to -60 dBm`** (strong penetration from Galerie).
- **Interference Delta:**
  - **Epson ET-4850 Wi-Fi Direct (-47 dBm on Ch 11) is DISABLED**.
- **Sonos Player in Room:**
  - Model: IKEA SYMFONISK Bookshelf (`RINCON_347E5C3826E201400`, IP `192.168.10.202`)
  - Connection Mode: **SonosNet Wireless (Ch 6)**
  - RF Health: **OFDM ANI: `0` (Clean)** (Massive improvement from previous red/orange state). Noise: -100 dBm.
  - Link Quality: SNR 30/18 dB to Wohnzimmer Bookshelf; SNR 34/32 dB to Noah.

---

### 2.7 Keller (Basement)
- **Date of Last Data Update:** **4 October 2026, 19:00**
- **Data Source:** Live Atheros driver diagnostics on wired Play:3 + baseline scan (20 Sep 22:01).
- **Wi-Fi Availability:**
  - **Keller AP:** Powered off.
  - **Kitchen AP (Ch 11 / Ch 40):** **`-63 / -68 dBm`** (strongest AP heard in basement).
  - **FRITZ!Box 6660 Wi-Fi:** Rogue 40 MHz Wi-Fi disabled / offline.
- **Sonos Player in Room:**
  - Model: Sonos Play:3 (`RINCON_5CAAFD595EEA01400`, IP `192.168.10.217`)
  - Connection Mode: **SonosNet (Ethernet)** — **Current STP Root Bridge**.
  - Ping Latency: **1 to 3 ms** (Wired to switch).
  - RF Health: **OFDM ANI: `5` (Moderate)** | Noise: -106 dBm.
  - Topological Bottleneck: Trapped behind basement concrete; **0 dB SNR** to Elternbad, Noemi, and RR; marginal 14–18 dB to bedrooms.

---

### 2.8 Büroecke (Office Corner)
- **Date of Last Data Update:** **4 October 2026, 19:01** (Sonos cross-matrix) / **20 September 2026, 22:46** (NetX scan).
- **Wi-Fi Availability:**
  - **5 GHz (Galerie AP, Ch 44 @ 80 MHz):** **`-52 dBm`** — Strong Green.
  - **2.4 GHz (Galerie AP, Ch 1 @ 20 MHz):** **`-56 dBm`** — Solid Green.
  - **Kitchen AP (Ch 11 / Ch 40):** `-70 / -75 dBm`.
  - **Interference Delta:** Epson Wi-Fi Direct (-64 dBm) eliminated.
- **Sonos Player in Room:**
  - Model: IKEA SYMFONISK Bookshelf (`RINCON_347E5C35B0F401400`)
  - Connection Mode: **SonosNet Wireless (Ch 6)**
  - Link Quality: **SNR 63 / 56 dB to Beam** (Superb); **SNR 41 / 43 dB to Wohnzimmer Bookshelf** (Solid).

---

### 2.9 Noah (Bedroom)
- **Date of Last Data Update:** **4 October 2026, 19:06** (Sonos live telemetry) / **19 September 2026, 21:05** (NetX scan).
- **Wi-Fi Availability:**
  - **5 GHz (Galerie AP, Ch 44 @ 80 MHz):** **`-57 dBm`** — Solid Green.
  - **2.4 GHz (Galerie AP, Ch 1 @ 20 MHz):** **`-60 dBm`** — Green.
- **Sonos Player in Room:**
  - Model: IKEA SYMFONISK Bookshelf (`RINCON_347E5C35B2C001400`, IP `192.168.10.229`)
  - Connection Mode: **SonosNet Wireless (Ch 6)**
  - RF Health: **OFDM ANI: `4` (Moderate)** | Noise: -100 dBm.
  - Link Quality: SNR 27/49 dB to Beam; SNR 36/26 dB to Wohnzimmer Bookshelf; weak link to basement Keller.

---

### 2.10 Nicolas (Bedroom / Attic Roof)
- **Date of Last Data Update:** **8 October 2026, 22:43** (NetX scan: `media_1791492260100.jpg`, `media_1791492260050.jpg`) / **5 October 2026** (Sonos live telemetry).
- **Wi-Fi Availability:**
  - **5 GHz (Galerie AP, Ch 44 @ 80 MHz):** **`-72 to -75 dBm`** (`76:4C:BC:76:7C:41`) — **Primary AP**. Negotiated link rate on phone: **1201 Mbps** (Wi-Fi 6 802.11ax).
  - **5 GHz (Kitchen AP, Ch 40 @ 40 MHz):** **`-82 to -83 dBm`** (`76:4C:BC:76:94:C1`) — Distant bleed (clean 8–10 dB delta below Galerie).
  - **Sanitization Status:** Rogue Fritzbox 6660 Wi-Fi (`WuTangLan` @ 2401 Mbps) and unmanaged EAP330 (`TP-Link_5G_93E92D` @ -55 dBm) are **100% eliminated**. Zero neighbor interference on 5 GHz.
- **Sonos Player in Room:**
  - Model: IKEA SYMFONISK Bookshelf (`RINCON_347E5C36DE9001400`, IP `192.168.10.165`)
  - Connection Mode Evaluation:
    - **5 GHz Wi-Fi (`WuTangLan-Family` on Galerie AP Ch 44):** **OFDM ANI: 0 (Pristine)** | Ping: **2.3 ms** | PHY Errors: 15,546. Strongly justified over SonosNet.
    - **2.4 GHz SonosNet Mesh:** **OFDM ANI: 5 (High)** | Ping: >3,900 ms | PHY Errors: 4,987,721 (~5M errors). Severe attenuation through roof/floors to other bedrooms.
    - **Wired Ethernet Option:** Switch Port 5 on Netgear GS316EP (`192.168.55.155`) is configured for Untagged VLAN 10 (PVID 10). Preferred if wall jack is patched.

---

### 2.11 Elternschlafzimmer (Master Bedroom)
- **Date of Last Data Update:** **4 October 2026, 19:06** (Sonos live telemetry) / **19 September 2026, 21:10** (NetX scan).
- **Wi-Fi Availability:**
  - **5 GHz (Galerie AP, Ch 44 @ 80 MHz):** **`-52 dBm`** — Strong Green.
  - **2.4 GHz (Galerie AP, Ch 1 @ 20 MHz):** **`-55 dBm`** — Solid Green.
- **Sonos Player in Room:**
  - Model: IKEA SYMFONISK Bookshelf (`RINCON_347E5C3828B001400`, IP `192.168.10.131`)
  - Connection Mode: **SonosNet Wireless (Ch 6)**
  - RF Health: **OFDM ANI: `4` (Moderate)** | Noise: -110 dBm.
  - Link Quality: **SNR 57 / 58 dB to Elternbad Bookshelf**; **SNR 55 / 45 dB to Beam**; **SNR 36 / 36 dB to Wohnzimmer Bookshelf**.

---

## 3. Master Summary Table (Room-by-Room)

| Room | Last Data Update | Best 5 GHz AP & RSSI | Best 2.4 GHz AP & RSSI | Sonos Connection Mode | Sonos OFDM ANI | Primary RF Finding / Action |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **Elternbad** | **4 Oct 22:19** | Galerie Ch 44 (**-55 dBm**) | Galerie Ch 1 (**-60 dBm**) | SonosNet Ch 6 | Dense (via Eltern) | **1201 Mbps Wi-Fi 6 restored; Epson -42 dBm gone.** |
| **Noemi** | **4 Oct 20:41** | Kitchen Ch 40 (**-72 dBm**) | Kitchen Ch 11 (**-70 dBm**) | Reconnecting | N/A (Offline) | **2.4G marginal + neighbor on Ch 11; cable strongly advised.** |
| **Galerie** | **4 Oct 17:00** | Galerie Ch 44 (**-45 dBm**) | Galerie Ch 1 (**-48 dBm**) | Via main floor | N/A | **AP relocated away from soundbar; stable on Ch 44.** |
| **Wohnzimmer** | **4 Oct 19:06** | Galerie Ch 44 (**-54 dBm**) | Galerie Ch 1 (**-52 dBm**) | SonosNet Ch 6 | **9 / 9 / 6** | **EAP330 powered off; non-Wi-Fi dock noise from Galerie.** |
| **Fernsehecke** | **4 Oct 19:06** | Galerie Ch 44 (**-55 dBm**) | Galerie Ch 1 (**-58 dBm**) | SonosNet / 5G HT | **0 (Clean)** | **Beam reaches all rooms at 49–63 dB SNR; Ch 48 HT clean.** |
| **Küche** | **4 Oct 19:06** | Galerie Ch 44 (**-55 dBm**) | Kitchen Ch 11 (Local) | SonosNet Ch 6 | **0 (Clean)** | **Epson Wi-Fi Direct disabled ➔ ANI dropped to 0!** |
| **Keller** | **4 Oct 19:00** | Kitchen Ch 40 (**-68 dBm**) | Kitchen Ch 11 (**-63 dBm**) | **SonosNet (Ethernet)** | **5 (Moderate)** | **Current Root Bridge; isolated behind basement concrete.** |
| **Büroecke** | **4 Oct 19:01** | Galerie Ch 44 (**-52 dBm**) | Galerie Ch 1 (**-56 dBm**) | SonosNet Ch 6 | Good (via Beam) | **Epson -64 dBm gone; 63 dB SNR link to Beam.** |
| **Noah** | **4 Oct 19:06** | Galerie Ch 44 (**-57 dBm**) | Galerie Ch 1 (**-60 dBm**) | SonosNet Ch 6 | **4 (Moderate)** | **Solid coverage from Galerie AP; weak link to basement.** |
| **Nicolas** | **8 Oct 22:43** | Galerie Ch 44 (**-72 dBm**) | Kitchen Ch 11 (Distant) | **Wi-Fi 5 GHz / Cable** | **0 (Wi-Fi) / 5 (Mesh)** | **Rogue Wi-Fi gone; 5 GHz Wi-Fi (ANI 0, 2.3ms) or Switch Port 5 cable strongly justified over 2.4G mesh.** |
| **Eltern** | **4 Oct 19:06** | Galerie Ch 44 (**-52 dBm**) | Galerie Ch 1 (**-55 dBm**) | SonosNet Ch 6 | **4 (Moderate)** | **Dense 58 dB link to Elternbad; solid links to Beam/Wz.** |
