# Session handoff — home Wi-Fi/VLAN and Sonos troubleshooting

**Prepared:** 1 October 2026, approximately 08:06 CEST  
**Status:** Kitchen EAP relocation measured; Gallery EAP/soundbar before-and-after exercise announced but **no Gallery measurements have yet been submitted**. Continue in the next session.  
**Important instruction for continuation:** When the owner uploads Gallery screenshots, do **not interpret any of them until they explicitly say they are done with all uploads**. Distinguish before and after sets.

## 1. Problem and scope

The owner reports unreliable house Wi-Fi/VLAN connectivity and Sonos streaming/dropouts. The original engineer brief covered evidence from 19–21 September 2026 (network scans, Omada screenshots, Sonos network matrix). Its central hypothesis was crowded/uncoordinated 2.4 GHz radio use, with an additional physical-placement problem. The September observations were a **historical baseline**, not proof of today's state. Since then, AP channels have been adjusted, Fritzbox WLAN reportedly disabled, the Kitchen EAP physically separated from its nearby Sonos, and same-day kitchen scans and Sonos system-information screenshots captured. Do not assert that any one change resolved Sonos playback: no post-change matrix or playback-duration test has been supplied.

Owner-described network topology: cable service → FRITZ!Box 6660 Cable → Firewalla Purple → Netgear switch → TP-Link APs carrying multiple SSIDs/VLANs. FRITZ!Box bridge/router mode, Firewalla VLAN/mDNS/firewall rules, and Netgear model, tagging, STP/RSTP and IGMP settings have **not** been captured. Omada controller runs on a Windows laptop and is not always on. AP management subnet is 192.168.55.0/24; Sonos screenshots show 192.168.10.0/24 addresses. Do not equate matching IP subnet with proof that discovery/streaming paths work correctly.

## 2. September historical baseline from owner-supplied engineer brief

- At one point both Omada EAP650s auto-selected 2.4 GHz channel 6 and 5 GHz channel 100. Earlier scans had Gallery 11/44 and Kitchen 1/48. Omada 2.4 GHz channel 6 utilization was reportedly near saturation; 5 GHz channel 100 looked idle. Channel utilization widget is not a direct measurement of all sources or proof of causality.
- The FRITZ!Box 6660 `WuTangLan` SSID was on air on both bands, reportedly with 40 MHz width on 2.4 GHz; clients sometimes fell back to it. This can bypass the intended Firewalla/VLAN Wi-Fi arrangement; precise routing/topology needs confirmation. Owner later stated the Fritzbox WLAN was disabled; old scanner entries marked offline/last-seen do not disprove that.
- September scans did not hear Kitchen AP in the kitchen on two evenings, although it was reported connected and heard elsewhere. **This finding has been superseded at the later kitchen measurement location**: the AP is now clearly audible there. No proof that it was physically off previously.
- Keller AP off; standalone EAP330 had 0 clients in an earlier Omada view, older 2018 firmware, extra/default SSID and 40 MHz 2.4 GHz at one point. Its current client count/configuration is not verified.
- Strong Epson ET-4850 Wi-Fi Direct on channel 11 and another TS5100 printer Wi-Fi Direct SSID; several IoT/bulb setup SSIDs; many SSIDs/hidden SSIDs on APs. Some nearby FRITZ/repeater networks have unverified ownership. Disable only radios actually owned and not needed.
- Sonos `/support/review` matrix from 19 September had a basement wired root (Keller), one secondary (Küche), many tertiary labels, high OFDM ANI for some units and several blocked links. This is historical diagnostic evidence; node labels/ANI colours/STP blocking alone do not prove a unique fault. Some home-theater products use separate wireless links, and Sonos-capable product models may not all use SonosNet. No new matrix yet.
- Original brief proposed removing unmanaged radios; pinning AP channels; reducing 2.4 GHz SSIDs; correcting AP placement; checking switch/VLANs; assessing wired Sonos and choosing/test-driving SonosNet channel. Treat fixed acceptance thresholds (zero tertiary, all ANI <=3, all links >=45) as proposed diagnostics, not hard universal success criteria. Real-world playback, discovery and roaming matter most.

## 3. Working AP/radio plan and verification status

| Device | 2.4 GHz | 5 GHz | Confidence / open point |
|---|---|---|---|
| Gallery EAP650, management IP 192.168.55.79, MAC ending `7C:40` | Intended channel 1, 20 MHz, Auto mode, Medium power per earlier configuration walkthrough | Channel 100, 80 MHz, Auto mode, Medium power per earlier walkthrough; kitchen scans show channel 100 with centre 106 | **Conflict:** current kitchen scans at 07:12 and 07:51 show live Gallery 2.4 GHz BSSID `76:4C:BC:76:7C:40` on **channel 6**, not intended channel 1. Inspect current Omada applied settings; do not mark channel 1 as implemented. 5 GHz channel 100 appears in scans. DFS channel; observe radar/channel changes. |
| Kitchen EAP650, management IP 192.168.55.37, MAC ending `94:C0` | Channel 11, 20 MHz, Medium power reportedly selected; scan confirms channel 11 but not power/width | Channel 40 with centre 38 (40 MHz), Medium power reportedly selected; scan confirms `40 (38)` | Read back width, power and Wireless Mode in Omada. Auto mode preferred over earlier suggested `b/g/n mixed` to retain AX capability. |
| EAP330 standalone | Channel 11 in scans, 20 MHz selected in walkthrough; initially screen showed 20 dBm, proposal 16 dBm **not verified as applied** | Channel 36 with centre 38 in kitchen scans (`36 (38)`), width implied 40 MHz by scanner | Channel 36/40 MHz shares 36–40 block with Kitchen channel 40/40 MHz. Weak at kitchen (-74 to -80 dBm on 5 GHz), but overlap should be assessed where the EAP330 is actually used. Exact placement and final configuration unknown. |
| Keller AP | Reportedly off | Reportedly off | Model/location/purpose and final decision unresolved. |
| FRITZ!Box 6660 Wi-Fi | Owner reports disabled; verify live scan/settings | Owner reports disabled; verify live scan/settings | Offline/last-seen scanner entries are not proof of live radio. |
| SonosNet | Actual 2.4 GHz channel **unknown** | N/A | Read in Sonos settings, not an ordinary Wi-Fi network scanner. Do not blindly set channel 6 while Gallery is visibly on channel 6. |

EAP650 BSSID scheme useful for sorting scanner entries: `76:4C:BC:76:94:C0` = Kitchen Family 2.4; `76:4C:BC:76:94:C1` = Kitchen Family 5; `76:4C:BC:76:7C:40` = Gallery Family 2.4; `76:4C:BC:76:7C:41` = Gallery Family 5. Prefixes `72` Admin, `7A` Guest, `7E` IoT, `82` hidden are other SSIDs on the same EAP radio. EAP330 5 GHz Family BSSID observed starting `86:16:F9...` is **not** Kitchen EAP. Multiple SSIDs on one radio reporting the same RSSI are not independent signal measurements.

**Critical correction to preceding assistant replies:** Despite earlier advice and a claimed intended channel 1, screenshots taken in the kitchen **after the relocation** show live Gallery Family 2.4 GHz around -72 dBm on **channel 6**. The prior assistant described the observation but did not explicitly flag it as an unresolved configuration discrepancy. Re-check it, rather than treating Gallery=1 / SonosNet=6 as already implemented.

## 4. Kitchen before/after physical relocation — 1 October 2026

Owner stated the Kitchen Sonos was immediately near/on the Kitchen EAP. First screenshot set taken near 07:12–07:13 with AP close to Sonos; the AP was moved and repeat screenshots taken near 07:51. Earlier assistant characterized the relocation as creating more separation, but the **new physical distance, mounting and exact phone position are not documented**. The scans all display `Wi-Fi throttling ON`; signal values are snapshots with ordinary spatial/device variation. Compare the *same BSSID/SSID/band*, not different APs sharing an SSID.

| Network/radio | Before move | After move | Difference | Evidence |
|---|---:|---:|---:|---|
| Kitchen Family 2.4 GHz `76:4C:BC:76:94:C0`, ch 11 | -55 dBm | -52 dBm | +3 dB | Network Analyzer/Inspector screenshots, ~07:12 vs ~07:51 |
| Kitchen Family 5 GHz `76:4C:BC:76:94:C1`, ch `40 (38)` | -47 dBm | -45 dBm | +2 dB | Same screenshot batches; later 5 GHz screenshots were supplied after an initial incomplete comparison |
| Gallery Family 2.4 GHz `76:4C:BC:76:7C:40`, ch 6 in visible scans | -64 dBm | -72 dBm | -8 dB snapshot difference | Might reflect phone position/scan variability; **not** a Gallery AP intervention yet |
| Gallery Family 5 GHz `76:4C:BC:76:7C:41`, ch `100 (106)` | -89 dBm in 07:13 screenshot | Not captured clearly in repeat set | No reliable comparison | Other Gallery SSIDs around -88 dBm before |
| EAP330 Family 5 GHz `86:16:F9:C0:E9:2E`, ch `36 (38)` | about -77 dBm | -80 dBm | About -3 dB snapshot | Other EAP330 5 GHz SSIDs ~-74 to -79 dBm |
| EAP330 Family 2.4 GHz, ch 11 | -78 dBm | -85 dBm | -7 dB snapshot | Location/scan variability not controlled |
| Phone status banner | Connected to `WuTangLan-Family` at 573 Mbps | Same banner at 573 Mbps | No displayed change | Link-rate banner **does not identify the associated BSSID** and is not throughput, latency or streaming quality proof |

**Interpretation:** Kitchen EAP remains strong/clearly visible after moving, improving approximately 3 dB at 2.4 GHz and 2 dB at 5 GHz in the reported sample. This is a *modest snapshot improvement*; not enough evidence to attribute causally to reduced interference or claim Sonos performance improved. The earlier claim that the phone was definitely associated with the Kitchen AP is **not proven by the displayed banner alone**; separately read the phone's connected BSSID in Android/Omada. An earlier Sonos Network view reportedly showed the Kitchen Sonos using Gallery BSSID on channel 6 at that time, but current Sonos screenshots identify Kitchen as SonosNet (wireless), so do not infer its current AP association from phone scans.

Other screenshot observations from the earlier discussion: Epson ET-4850 Wi-Fi Direct had been strong (~-50 dBm) in kitchen on ch 11; owner reported five Tapo bulb setup SSIDs on ch 6 not yet joined to `WuTangLan-IOT`; hidden SSIDs still present; prior Fritzbox network entries shown offline/last-seen. Confirm current state rather than assume corrective measures completed. The screenshot sets show a TS5100-series Wi-Fi Direct network around -89 to -91 dBm and an unverified `WLAN-A7C604` on ch 11 around -73 to -81 dBm. A scanner can reveal Wi-Fi BSSIDs/RSSI; it cannot show non-Wi-Fi interference or SonosNet quality comprehensively.

## 5. Sonos status at about 07:56, after Kitchen EAP move

Sonos **About Your System** screenshots taken at approximately 07:56. They establish displayed status/connection type at one moment, **not** whether playback is reliable or whether the mesh/STP tree improved. IPs below are transcribed from screenshots where legible; cross-check before configuration changes.

| Displayed device | Displayed status | Connection type | IP if shown |
|---|---|---|---|
| Play:1 Fernsehecke (Left Surround) | Connected | Home Theater (wireless) | 192.168.10.102 shown in screenshot; see caveat below |
| Play:3 Keller | Connected | SonosNet (ethernet) | 192.168.10.217 |
| Bookshelf: Küche | Connected | SonosNet (wireless) | 192.168.10.202 |
| Bookshelf: Nicolas | Connected | WiFi | 192.168.10.165 |
| Bookshelf: Noah | Connected | SonosNet (wireless) | 192.168.10.229 |
| Bookshelf: Büroecke | Not Connected | no connection type shown | Unavailable |
| Bookshelf: Eltern | Connected | WiFi | 192.168.10.131 |
| Bookshelf: Elternbad | Connected | SonosNet (wireless) | 192.168.10.113 |
| Beam: Fernsehecke | Connected | SonosNet (wireless) | 192.168.10.241 |
| Bookshelf: Noemi | Not Connected | no connection type shown | Unavailable |
| Bookshelf: Portable | Not Connected | no connection type shown | Unavailable |
| Play:1 Wohnzimmer, serial ending `09:84:1` | Connected | SonosNet (wireless) | 192.168.10.160 |
| Play:1 Wohnzimmer, serial ending `15:2A:7` | Connected | SonosNet (wireless) | 192.168.10.101 |
| Bookshelf: Wohnzimmer, serial ending `FE:6E:E` | Connected | SonosNet (wireless) | 192.168.10.230 |

**Correction to preceding assistant answer:** It previously stated Keller had IP `192.168.10.102`. The screenshot instead displays **Keller `192.168.10.217`**, while `192.168.10.102` appears on the preceding *Fernsehecke left surround* entry. Keller is the only displayed Ethernet Sonos product in this screenshot set; this alone does not conclusively establish the STP root election. Noemi is currently disconnected despite earlier claim it was cabled; inspect its power/cable/switch/VLAN before attributing failure. Noah is **now on SonosNet**, whereas the older matrix indicated it was off that mesh. Elternbad is SonosNet in these screenshots, correcting the earlier textual recap that listed it as Wi-Fi. Büroecke has no IP and is disconnected; do not list it as connected Wi-Fi. Nicolas and Eltern display WiFi; bonded surrounds can show Home Theater (wireless), which is distinct from a separate ordinary Wi-Fi AP association. If portable product is powered off/away, its disconnected state may be expected.

Moving the EAP did **not** cause the Kitchen Sonos to migrate to home Wi-Fi; it continues to report SonosNet (wireless). This is not, by itself, a fault. SonosNet's channel, new network matrix, interference indicators, and real playback performance **have not** been recorded after the move. Avoid asserting AP signal increase equals Sonos improvement.

## 6. Outstanding configuration and engineering questions

1. **Gallery AP 2.4 GHz ch 6 vs intended ch 1:** open current Omada radio settings and read back actual channel, width, power, auto/RRM schedule; compare with fresh live BSSID scan. Do this before attempting to reserve channel 6 for SonosNet.
2. **Gallery AP physical relocation:** owner is about to collect *before* network screenshots near soundbar, move AP, then collect *after*. Await explicit completion. Track Gallery Family BSSIDs `…:7C:40` and `…:7C:41`, same phone location, scan times, widths, channels and Sonos proximity; note any concurrent radio-setting changes.
3. **Kitchen EAP:** record actual mounting, cable/link LEDs, switch-port errors, applied Wireless Mode/width/power and client association. The latest phone signal is good; its Internet/DHCP stability still needs testing.
4. **EAP330:** exact location/current purpose, current clients, 2.4 GHz power and width, 5 GHz channel/width. Current `36 (38)` overlaps Kitchen `40 (38)` if both use the 36–40/40 MHz block; quantify whether overlap matters near its service area, then retire/reconfigure if appropriate. Do not factory reset before documenting config/dependencies.
5. **SonosNet:** read actual channel from Sonos; capture fresh `/support/review` matrix or diagnostics; compare link paths/ANI before and after placement changes. Test grouped playback for an explicit period and log any dropouts, room, time and playback source.
6. **Noemi:** check device power, physical Ethernet link, switch port, untagged Sonos VLAN (if designed that way), DHCP/IP, port isolation; distinguish prior 'wired' claim from current disconnected screenshot.
7. **Fritzbox, printers, Tapo bulbs and hidden SSIDs:** verify actual Fritzbox WLAN off with live scans and Fritzbox settings; disable unnecessary Wi-Fi Direct on owned printers if not needed; pair bulbs to 2.4 GHz IoT SSID and confirm IoT VLAN addressing; document hidden/Admin/Guest SSIDs before disabling or moving bands.
8. **Switch/Firewalla:** document actual Netgear model, port PVID/tagging, STP/RSTP, IGMP snooping, topology and Firewalla VLAN/DHCP/mDNS/SSDP/firewall behavior; do this *before* adding a second wired Sonos to avoid potential loops/blocked paths.
9. **Outcomes over heuristics:** validate client BSSID and IP/VLAN in each room, kitchen connection stability, measured 5 GHz coverage, Sonos discovery and sustained playback. Do not assume every player should be SonosNet-capable or that zero tertiary nodes is a requirement.

## 7. Next-session protocol

Owner's last instruction (08:02): "I am now in gallery where the soundbar is it's near the EAP I will measure the network and post pictures before moving the EAP then after wait until I tell you that I am done with the upload before interpretation." Assistant agreed. The user then requested this handoff instead of uploading Gallery evidence here. **Next assistant should acknowledge receipt of incoming screenshots only, without analysis, until the owner explicitly says all Gallery uploads are complete.** Separate labeled before/after batches; do not conflate Gallery with Kitchen; explain any ambiguity only after completion. Once complete, compare same Gallery BSSIDs and channels/widths, watch the open channel-6 discrepancy, assess phone proximity and AP–soundbar separation, and avoid claiming direct Sonos improvements from Wi-Fi RSSI alone. If owner starts a new session without images from the previous one, request screenshots anew or work from the saved values here.

## 8. Provenance and confidence

- Historical September evidence is transcribed from the owner-provided engineer brief; original `Netlog_*.jpg`, September `omada/` images and Sonos `/support/review` matrix were **not independently opened in this conversation**. The Claude artifact URL failed to fetch; the full brief pasted by the owner was used instead.
- Current kitchen observations derive from owner-uploaded Inspector screenshots at 07:12–07:13 and 07:51, and Sonos About Your System screenshots at 07:56. Attached image files in this conversation include kitchen scans `1000011171.jpg`–`1000011183.jpg` (sequence not always chronological in file list; filename `1000011179.jpg` appeared twice) and Sonos screenshots `1000011184.jpg`–`1000011187.jpg`. These attachments may not carry into the next session; this handoff records the values.
- The screenshots use Android scan throttling; do not treat missing or 'offline/last seen' rows as proof that an AP is down. Captured link rate 573 Mbps is not a throughput benchmark. Small 2–3 dB shifts may reflect measurement variation as well as relocation. Do not infer non-Wi-Fi spectrum occupancy from an ordinary Wi-Fi scanner.
