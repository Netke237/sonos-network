# Wi-Fi — Galerie

Source image: `Netlog_Galerie.jpg` (Telegram caption **"Galerie"**, `IMG_20260920_092409_347.jpg`).
Scan app: NetX Inspector · time 21:11–21:12 · phone associated to `WuTangLanFamily @ 1201 Mbps`
· `Wi-Fi throttling ON`. The image is a scroll capture of ~9 screens.

## Top of the list (strongest first)

| SSID | BSSID | Band | Channel | Signal |
|---|---|---|---|---|
| WuTangLan-Family *(connected)* | 76:4C:BC:76:7C:41 | 5 GHz | 44 (42) | **-53 dBm** |
| WuTangLan-Guest | 7A:4C:BC:76:7C:41 | 5 GHz | 44 (42) | -53 dBm |
| WuTangLan-IOT | 7E:4C:BC:76:7C:41 | 5 GHz | 44 (42) | -53 dBm |
| Admin | 72:4C:BC:76:7C:41 | 5 GHz | 44 (42) | -53 dBm |
| Admin | 72:4C:BC:76:7C:40 | 2.4 GHz | 11 | -53 dBm |
| WuTangLan-Family | 76:4C:BC:76:7C:40 | 2.4 GHz | 11 | -53 dBm |
| Admin | 72:4C:BC:76:94:C0 | 2.4 GHz | 1 | -55 dBm |
| WuTangLan-Guest | 7A:4C:BC:76:94:C0 | 2.4 GHz | 1 | -56 dBm |
| WuTangLan-IOT | 7E:4C:BC:76:94:C0 | 2.4 GHz | 1 | -56 dBm |
| Tapo_Bulb_9749 | 0C:EF:15:5E:97:49 | 2.4 GHz | 6 | -52 dBm |
| Tapo_Bulb_9084 | 0C:EF:15:5E:90:84 | 2.4 GHz | 6 | -53 dBm |
| Vodafone-DD14 | DC:A6:33:43:EC:0C | 2.4 GHz | 11 | -64 dBm |
| DIRECT-f1-EPSON-ET-4850 | 6A:55:D4:7D:0B:9B | 2.4 GHz | 11 | -68 dBm |
| Tapo_Bulb_C6B1 | 0C:EF:15:5E:C6:B1 | 2.4 GHz | 6 | -95 dBm |

Also present but marked offline in the capture: `FRITZ!Box 6660 Cable EV` (5 GHz ch 116/114),
`FRITZ!Box 7490` (5 GHz ch 40/42), `DIRECT-Ub7F-TS5100series` (2.4 ch 11), `Tapo_Bulb_8CD1`,
`Tapo_Bulb_9CD4`, and the whole `WuTangLan` / `-Family` / `-Guest` / `-IOT` set from the
Fritzbox and from AP-2 / AP-3.

## Assessment

- Only **AP-1** (`…76:7C:4x`) is meaningfully present, at **-53 dBm on both bands**. AP-2 is
  ~3 dB weaker on 2.4 GHz and not usable on 5 GHz here.
- You say there is an EAP in the Galerie. **-53 dBm is not what a same-room AP looks like.**
  A same-room EAP reads -30 to -45 dBm. Either the Galerie EAP is not AP-1, or it is turned
  down / enclosed / not running.
- Nothing here is "dark green" because nothing here is stronger than -52 dBm.
- The strongest signal in the room is a **smart bulb** (Tapo_Bulb_9749, -52 dBm) sitting on
  2.4 GHz channel 6.

## Not retrieved

- Per-BSSID transmit power, 802.11 mode (a/n/ac/ax), and channel width beyond what the app prints.
- Which physical EAP `…76:7C:4x` is — that mapping has to come from the Omada controller.
