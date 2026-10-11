# Home network & Sonos documentation

Transcription and analysis of the Wi-Fi scans (NetX Inspector) and the Sonos support-page
Network Matrix captured on 2026-09-20.

## Index

| Document | Contents |
|---|---|
| **[docs/10-assessment-and-recommendations.md](docs/10-assessment-and-recommendations.md)** | **Start here — what is wrong and what to do about it** |
| [docs/00-overview.md](docs/00-overview.md) | Topology, goals, and what the evidence shows |
| [docs/source-images.md](docs/source-images.md) | Which `.jpg` in this repo belongs to which room |
| [docs/open-questions.md](docs/open-questions.md) | What the screenshots could not answer |
| **[docs/wifi/01-access-points.md](docs/wifi/01-access-points.md)** | **The three access points — models, MACs, firmware, channels (confirmed from Omada)** |
| [docs/wifi/00-ap-and-ssid-inventory.md](docs/wifi/00-ap-and-ssid-inventory.md) | BSSID → radio → channel key, SSID list, channel picture |
| [docs/sonos/devices.md](docs/sonos/devices.md) | The 14 Sonos players |
| [docs/sonos/network-matrix.md](docs/sonos/network-matrix.md) | Full Network Matrix transcription + reading |

### Per-room Wi-Fi

| Room | Page | Best own signal |
|---|---|---|
| Wohnzimmer | [wohnzimmer.md](docs/wifi/wohnzimmer.md) | -52 dBm (2.4) / -55 dBm (5) |
| Galerie | [galerie.md](docs/wifi/galerie.md) | -53 dBm / -53 dBm |
| Elternschlafzimmer | [elternschlafzimmer.md](docs/wifi/elternschlafzimmer.md) | -57 dBm / -54 dBm |
| Elternbad | [elternbad.md](docs/wifi/elternbad.md) | -56 dBm / -50 dBm |
| Noemi | [noemi.md](docs/wifi/noemi.md) | -56 dBm / -59 dBm |
| Noah | [noah.md](docs/wifi/noah.md) | no 2.4 GHz / -61 dBm |
| Büroecke | [bueroecke.md](docs/wifi/bueroecke.md) | -52 dBm / -54 dBm |
| Fernsehecke | [fernsehecke.md](docs/wifi/fernsehecke.md) | -55 dBm / -53 dBm |
| Küche | [kueche.md](docs/wifi/kueche.md) | -60 dBm / -55 dBm |
| Nicolas | [nicolas.md](docs/wifi/nicolas.md) | -64 dBm / -70 dBm |
| Keller | [keller.md](docs/wifi/keller.md) | -63 dBm / -68 dBm |

No scan yet for **Eltern** — the last room with a Sonos player and no Wi-Fi measurement.

## Source files

Screenshots are kept at the repo root (`Netlog_*.jpg`, `Sonos Network.jpg`) and in the
`Keller/`, `Küche/`, `küche_2/`, `Fernsehecke/` and `Büroecke/` folders. Omada and EAP330
management screenshots are in `omada/`.
[docs/source-images.md](docs/source-images.md) lists which file belongs to which room and
which ones are redundant and can be deleted.
Nothing in these documents changes any device configuration.
