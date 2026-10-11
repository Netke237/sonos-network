# Sonos Devices — Master Inventory & Live Telemetry Map

**Household ID:** `Sonos_jbR4d1RTAceFFMXen533ak2ODa.715OQVIoIp0ZP0L2LA2q`  
**Software Build:** `86.8-78270` (S2 Generation 2)  
**Subnet / VLAN:** VLAN 10 (`WuTangLan-Family`, `192.168.10.0/24`)

---

## 1. Verified 14-Player Hardware & Network Inventory (October 2026)

| # | Zone Name (Current) | Hardware Model | IP Address | Base MAC | SonosNet BSSID | RINCON UUID / Serial | Connection Mode & STP Role |
|---|---|---|---|---|---|---|---|
| 1 | **`Wohnzimmer_Bookshelf`** | SYMFONISK Bookshelf | `192.168.10.230` | `54:2A:1B:63:FE:6E` | `54:2A:1B:63:FE:6F` | `RINCON_542A1B63FE6E01400` | **SonosNet (Ethernet)** — **Active STP Root Bridge** (`9000.542a1b63fe6e`, Cost 0) |
| 2 | **`Wohnzimmer_Esstisch`** | Sonos Play:1 | `192.168.10.160` | `B8:E9:37:E6:09:84` | `B8:E9:37:E6:09:85` | `RINCON_B8E937E6098401400` | SonosNet Wireless (Ch 6, Direct to Root) |
| 3 | **`Wohnzimmer_Buchregal`** | Sonos Play:1 | `192.168.10.101` | `B8:E9:37:E5:15:2A` | `B8:E9:37:E5:15:2B` | `RINCON_B8E937E5152A01400` | SonosNet Wireless (Ch 6, Direct to Root) |
| 4 | **`Fernsehecke (LF,RF)`** | Sonos Beam | `192.168.10.241` | `94:9F:3E:C0:EE:A1` | `94:9F:3E:C0:EE:A2` | `RINCON_949F3EC0EEA101400` | SonosNet Wireless (Ch 6) + 5 GHz HT Master (Ch 48) |
| 5 | **`Fernsehecke (LR)`** | Sonos Play:1 | `192.168.10.102` | `5C:AA:FD:49:0C:CA` | `5C:AA:FD:49:0C:CB` | `RINCON_5CAAFD490CCA01400` | Home Theater Satellite (5 GHz Ch 48 to Beam) |
| 6 | **`Fernsehecke (RR)`** | Sonos One / Play:1 | *(Bonded via Beam)* | `94:9F:3E:00:29:2E` | `94:9F:3E:00:29:2F` | `RINCON_949F3E00292E01400` | Home Theater Satellite (5 GHz Ch 48 to Beam) |
| 7 | **`Keller`** | Sonos Play:3 | `192.168.10.217` | `5C:AA:FD:59:5E:EA` | `5C:AA:FD:59:5E:EB` | `RINCON_5CAAFD595EEA01400` | SonosNet Wireless Leaf (Unplugged from Ethernet to prevent basement root trap) |
| 8 | **`Küche`** | SYMFONISK Bookshelf | `192.168.10.202` | `34:7E:5C:38:26:E2` | `34:7E:5C:38:26:E3` | `RINCON_347E5C3826E201400` | SonosNet Wireless (Ch 6) |
| 9 | **`Büroecke`** | SYMFONISK Bookshelf | `192.168.10.151` | `34:7E:5C:35:B0:F4` | `34:7E:5C:35:B0:F5` | `RINCON_347E5C35B0F401400` | SonosNet Wireless (Ch 6, Direct to Root/Beam) |
| 10 | **`Noah`** | SYMFONISK Bookshelf | `192.168.10.229` | `34:7E:5C:35:B2:C0` | `34:7E:5C:35:B2:C1` | `RINCON_347E5C35B2C001400` | SonosNet Wireless (Ch 6) — Wall port patched to Switch Port 7 (VLAN 10) |
| 11 | **`Noemi`** | SYMFONISK Bookshelf | `192.168.10.244` | `54:2A:1B:64:26:80` | `54:2A:1B:64:26:81` | `RINCON_542A1B64268001400` | SonosNet Wireless (Ch 6) — Wall port patched to Switch Port 6 (VLAN 10) |
| 12 | **`Nicolas`** | SYMFONISK Bookshelf | `192.168.10.165` | `34:7E:5C:36:DE:90` | `34:7E:5C:36:DE:91` | `RINCON_347E5C36DE9001400` | Wi-Fi Station (5 GHz Ch 44) / SonosNet — Wall port patched to Switch Port 5 (VLAN 10) |
| 13 | **`Eltern`** | SYMFONISK Bookshelf | `192.168.10.131` | `34:7E:5C:38:28:B0` | `34:7E:5C:38:28:B1` | `RINCON_347E5C3828B001400` | SonosNet Wireless (Ch 6) |
| 14 | **`Elternbad`** | SYMFONISK Bookshelf | `192.168.10.113` | `34:7E:5C:31:CE:28` | `34:7E:5C:31:CE:29` | `RINCON_347E5C31CE2801400` | SonosNet Wireless (Ch 6) |

---

## 2. Historical Baseline Notes (19 September 2026)

Source: `Sonos Network.jpg` — Sonos support page `http://192.168.10.229:1400/support/review`, captured on **2026-09-19** at 21:44, 22:17, and 22:35.

- **BSSID Mapping:** The SonosNet BSSID in the matrix is the player's Ethernet MAC + 1 (standard Atheros Rincon convention).
- **Wohnzimmer Disambiguation (Resolved 5 Oct 2026):** Previously, three standalone players (`54:2A:1B:63:FE:6E`, `B8:E9:37:E6:09:84`, and `B8:E9:37:E5:15:2A`) shared the identical `<roomName>Wohnzimmer</roomName>`, causing UI selection collisions and silent group drops in the Sonos app. They are now uniquely named `Wohnzimmer_Bookshelf`, `Wohnzimmer_Esstisch`, and `Wohnzimmer_Buchregal`.
- **Root Bridge Transition (Resolved 5 Oct 2026):** Previously, `Keller` (`192.168.10.217`) was wired to Ethernet and acted as the STP Root Bridge from behind dense basement concrete (0 dB SNR to upper bedrooms). `Keller` has been unplugged from Ethernet, and `Wohnzimmer_Bookshelf` (`192.168.10.230`) is now the central ground-floor wired Root Bridge.
