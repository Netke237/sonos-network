# Which image belongs to which room

> **Dates.** The in-screenshot clocks of `Netlog_*.jpg` (19:42–21:14) and `Sonos Network.jpg`
> (21:44–22:35) are *later in the day* than the files' creation times on 20 Sep (09:19–13:50),
> so those captures were taken on the evening of **19 Sep**. The room folders
> (`Keller/`, `Fernsehecke/`, `küche_2/`, `Büroecke/`) carry their real date in the filename:
> **20 Sep**. `omada/` and `Kücke_3/` are **21 Sep**.

Mapping taken from the two Telegram screenshots supplied with the request (the caption under
each sent photo is the room name) cross-checked against the file names already in the repo.

| Repo file | Telegram caption | Original filename | Sent | Resolution | Usable? |
|---|---|---|---|---|---|
| `Netlog_elternschlafzimmer.jpg` | Elternschlafzimmer | IMG_20260920_091954_565.jpg | 09:20 | 1220 × 35256 | yes |
| `Netlog_Küche.jpg` | Küche | *(sent inline, no filename)* | 09:20 | **143 × 1280** | **barely** |
| `Netlog_Nicolas.jpg` | Nicolas | IMG_20260920_092112_877.jpg | 09:21 | 1220 × 13560 | yes |
| `Netlog_Keller.jpg` | Keller | *(sent inline, no filename)* | 09:22 | **143 × 1280** | **barely** |
| `Netlog_Wohnzimmer.jpg` | Wohnzimmer | IMG_20260920_092234_903.jpg | 09:22 | 1220 × 21696 | yes |
| `Netlog_Noah.jpg` | Noah | IMG_20260920_092310_315.jpg | 09:23 | 1220 × 18984 | yes |
| `Netlog_Noemi.jpg` | Noemi | IMG_20260920_092335_591.jpg | 09:23 | 1220 × 18984 | yes |
| `Netlog_Galerie.jpg` | Galerie | IMG_20260920_092409_347.jpg | 09:24 | 1220 × 24408 | yes |
| `Netlog_Elternbad.jpg` | Elternbad | IMG_20260920_092430_279.jpg | 09:24 | 1220 × 24408 | yes |
| `Sonos Network.jpg` | Sonos Network | IMG_20260920_135050_653.jpg | 13:51 | 1220 × 32544 | yes |

`Netlog_Keller_2.jpg` and `Netlog_Küche_2.jpg` are **byte-identical** to `Netlog_Keller.jpg`
and `Netlog_Küche.jpg` (same MD5, same 143 × 1280 size) — Telegram re-compressed them on the
way out. They add nothing and can be deleted.

## Second batch — folders added 2026-09-20 ~22:2x

Full-resolution screenshots (1220 × 2712) from the NetSpot / Network Analyzer app.

| Folder | File | Time | Room | Status |
|---|---|---|---|---|
| `Keller/` | `…22-01-12-393` · `…22-01-18-819` · `…22-01-39-811` | 22:01 | Keller | ✅ used → [keller.md](wifi/keller.md) |
| `Fernsehecke/` | `…22-02-17-014_com.miui.gallery.jpg` | 22:02 | — | ❌ screenshot of the gallery app, no data |
| `Fernsehecke/` | `…22-05-18-071` … `…22-05-47-738` (7 files) | 22:05 | **Fernsehecke** | ✅ used → [fernsehecke.md](wifi/fernsehecke.md) |
| `Küche/` | `…22-05-18-071` … `…22-05-47-738` (7 files) | 22:05 | — | ❌ byte-identical copy of the `Fernsehecke/` set |
| `küche_2/` | `…22-16-58-390` … `…22-17-23-753` (7 files) | 22:16–22:17 | **Küche** | ✅ used → [kueche.md](wifi/kueche.md) |
| `Büroecke/` | `…22-45-46-467` … `…22-46-13-983` (7 files) | 22:45–22:46 | **Büroecke** | ✅ used → [bueroecke.md](wifi/bueroecke.md) |
| `Kücke_3/` | `…2026-09-21-21-57-32-442` … `…21-58-39-013` (8 files) | **21 Sep** 21:57–21:58 | **Küche** (second scan) | ✅ used → [kueche.md](wifi/kueche.md) |

### Resolved: the duplicate folder

Each of the seven 22:05 files has the **same MD5 in `Küche/` and in `Fernsehecke/`**:

```
7986cef8… …22-05-18-071      ff001f65… …22-05-28-167      c7eefc85… …22-05-37-655
7705eb63… …22-05-23-141      462dbada… …22-05-33-921      6b3a471c… …22-05-42-275
                                                           c114f4d6… …22-05-47-738
```

The Fernsehecke scan had been copied into `Küche/` as well. A correct Küche scan was supplied
afterwards in `küche_2/` (seven distinct files, 22:16–22:17), so the 22:05 set is the
**Fernsehecke**.

### Files that can be deleted

- `Netlog_Keller.jpg`, `Netlog_Keller_2.jpg`, `Netlog_Küche.jpg`, `Netlog_Küche_2.jpg`
  — unreadable 143 px thumbnails, superseded.
- the whole `Küche/` folder — duplicate of `Fernsehecke/`.
- `Fernsehecke/Screenshot_2026-09-20-22-02-17-014_com.miui.gallery.jpg` — no data.

## Rooms with no scan

- **Eltern** (as distinct from Elternschlafzimmer) — the only room left with a Sonos player
  and no Wi-Fi scan. Everything else is now covered.
