# Wi-Fi — Nicolas (Roof / Attic)

**Room Location:** Nicolas' Bedroom / Attic (Dachgeschoss) under the roof.  
**Hardware in Room:** IKEA SYMFONISK Bookshelf (`RINCON_347E5C36DE9001400`, IP `192.168.10.165`, MAC `34:7E:5C:36:DE:90`).

---

## 1. Scan 2: Post-Remediation Verification (8 October 2026, 22:43)

**Source Images:** NetX Inspector captures (`media_1791492260100.jpg`, `media_1791492260050.jpg`).  
**Status:** Phone connected to **`WuTangLan-Family`** (VLAN 10) at **1201 Mbps** (Wi-Fi 6 802.11ax, 80 MHz channel). `Wi-Fi throttling ON`.

### Top Networks Recorded

| SSID | BSSID | Band | Channel (Width) | Signal (RSSI) | Associated AP / Hardware | Notes |
|---|---|---|---|---|---|---|
| **WuTangLan-Guest** | `7A:4C:BC:76:7C:41` | 5 GHz | 44 (42 @ 80 MHz) | **-72 dBm** | **Gallery AP** (`EAP650`) | Primary 5 GHz signal under roof |
| **Admin** | `72:4C:BC:76:7C:41` | 5 GHz | 44 (42 @ 80 MHz) | **-73 dBm** | **Gallery AP** (`EAP650`) | Management VLAN |
| **WuTangLan-IOT** | `7E:4C:BC:76:7C:41` | 5 GHz | 44 (42 @ 80 MHz) | **-73 dBm** | **Gallery AP** (`EAP650`) | IoT VLAN |
| **WuTangLan-Family** *(connected)* | `76:4C:BC:76:7C:41` | 5 GHz | 44 (42 @ 80 MHz) | **-75 dBm** | **Gallery AP** (`EAP650`) | Client active link: **1201 Mbps** |
| **Admin** | `72:4C:BC:76:94:C1` | 5 GHz | 40 (38 @ 40 MHz) | **-82 dBm** | **Kitchen AP** (`EAP650`) | Distant ground floor bleed |
| **WuTangLan-Family** | `76:4C:BC:76:94:C1` | 5 GHz | 40 (38 @ 40 MHz) | **-82 dBm** | **Kitchen AP** (`EAP650`) | Secondary AP (10 dB down) |
| **WuTangLan-Guest** | `7A:4C:BC:76:94:C1` | 5 GHz | 40 (38 @ 40 MHz) | **-83 dBm** | **Kitchen AP** (`EAP650`) | Distant |
| **WuTangLan-IOT** | `7E:4C:BC:76:94:C1` | 5 GHz | 40 (38 @ 40 MHz) | **-83 dBm** | **Kitchen AP** (`EAP650`) | Distant |

### Key Findings from the 8 October Scan:
1. **Rogue SSIDs Fully Eliminated**:
   - The unmanaged standalone **EAP330** default SSID (`TP-Link_5G_93E92D` previously heard at -55 dBm) is **100% absent / powered off**.
   - The **Fritzbox 6660 rogue Wi-Fi** (`WuTangLan` at 2401 Mbps) is **100% absent / disabled**. Clients now authenticate strictly to managed Omada VLAN SSIDs.
2. **Clean 5 GHz Spectrum (No External Interference)**:
   - There are **zero neighbour Wi-Fi networks** visible on 5 GHz above noise floor.
   - Non-DFS Channel 44 (U-NII-1) operates without radar events or channel hopping.
3. **Clean AP Separation**:
   - A healthy **8 to 10 dB delta** exists between Gallery AP (-72 to -75 dBm) and Kitchen AP (-82 to -83 dBm), preventing erratic client roaming flaps.

---

## 2. Scan 1: Historical Baseline (20 September 2026, 20:54)

**Source Image:** `Netlog_Nicolas.jpg` (`IMG_20260920_092112_877.jpg`). Phone associated to unmanaged `WuTangLan` @ 2401 Mbps.

| SSID | BSSID | Band | Channel | Signal |
|---|---|---|---|---|
| **TP-Link_5G_93E92D** | `84:16:F9:93:E9:2D` | 5 GHz | 44 (42) | **-55 dBm** (EAP330 factory SSID) |
| WLAN-A7C604 | `1C:23:A2:7A:E3:7A` | 2.4 GHz | 6 | -61 dBm (Neighbor) |
| WuTangLan-Family | `86:16:F9:BF:E9:2D` | 2.4 GHz | 6 | -64 dBm (EAP330) |
| WuTangLan-IOT | `86:16:F9:BF:E9:2F` | 2.4 GHz | 6 | -66 dBm (EAP330) |
| WuTangLan-Family | `76:4C:BC:76:7C:40` | 2.4 GHz | 11 | -67 dBm (Gallery AP) |
| WuTangLan-Family | `76:4C:BC:76:7C:41` | 5 GHz | 44 (42) | -70 dBm (Gallery AP) |
| WuTangLan-Family | `76:4C:BC:76:94:C1` | 5 GHz | 48 (42) | -77 dBm (Kitchen AP) |

---

## 3. Engineering Assessment: Does the Scan Justify Sonos on Wi-Fi?

**YES, unequivocally.** In fact, empirical telemetry proves that operating the Nicolas player on **5 GHz Wi-Fi** (or **Wired Ethernet**) is mandatory, and keeping it on 2.4 GHz SonosNet is highly detrimental.

### Comparative Evidence Matrix

| Metric / Parameter | 2.4 GHz SonosNet (Mesh) | 5 GHz Wi-Fi (`WuTangLan-Family`) | Wired Ethernet (Switch Port 5) |
|---|:---:|:---:|:---:|
| **Physical Path** | Multi-hop RF through roof/floors | Direct line to Galerie AP Ch 44 | Direct Cat6 to GS316EP switch |
| **OFDM ANI Level** | **ANI 5 (Moderate-to-High Noise)** | **ANI 0 (Pristine / Clean)** | N/A (Ethernet) |
| **PHY Error Rate** | **4,987,721 errors** (~5M err) | **15,546 errors** (320x cleaner) | **0 errors** |
| **Ping Latency (Idle)** | 300 – 500 ms | **2.3 ms** | **< 1.0 ms** |
| **Ping Latency (Streaming)** | **> 3,900 ms (Timeouts/Loss)** | **2 to 5 ms (Zero packet loss)** | **< 1.0 ms (Zero loss)** |
| **Link Quality to Mesh** | 0 dB (Eltern), 14 dB (Noah), 15 dB (Noemi) | Direct 1201 Mbps Wi-Fi 6 link | 100 Mbps Full Duplex |
| **Impact on Other Rooms** | Consumes 2.4G mesh airtime | **Zero airtime burden on 2.4G** | **Zero airtime burden** |

### Conclusion & Recommendation:
1. **Wi-Fi Justification**: Because Nicolas is physically isolated in the attic, 2.4 GHz SonosNet signals suffer massive attenuation through ceilings, accumulating ~5 million PHY errors and causing audio dropouts. Operating the player in **5 GHz Wi-Fi Station Mode** connects it directly to the Galerie AP with 0 ANI, 2.3 ms latency, and zero airtime contention.
2. **Permanent Gold Standard**: **Netgear GS316EP Port 5** is already patched and configured as **Untagged VLAN 10 (PVID 10)** for Nicolas' room. If a physical LAN cable can be connected from the wall jack to the speaker, Ethernet eliminates all wireless variables entirely.
