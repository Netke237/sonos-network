# ADR-0006: Autonomous Watchdog, Telegram Alerts, Self-Healing Ghost Group Sanitizer & Companion Distribution

- **Status:** Accepted
- **Date:** 2026-10-13

## Context

Phase 1 deployed the centralized Mini PC platform (`FastAPI + PostgreSQL`), Phase 1.5 delivered the interactive draggable topology canvas, and Phase 2 completed the native Android companion app. While users can now manually poll telemetry and trigger 1-click actions from either the web dashboard or Android phone, the system is fundamentally passive:

1. **Passive Incident Discovery**:
   - When a Ghost Group forms (e.g., when a family member ungroups rooms in the official Sonos app while streaming Spotify), the remaining rooms are locked with cloud `"Couldn't play content"` errors and `HTTP 500` join failures. Currently, this is only resolved when Kenneth notices the music stopped and manually clicks "Flush Ghost Groups".
   - When an STP Root Usurpation occurs (e.g., someone patches an Ethernet cable into Noah's or Nicolas' bedroom speaker, or plugs in the basement Play:3), the lower MAC address usurps `Wohnzimmer_Bookshelf` as STP root across the BPDU pass-through `Netgear GS316EP`, causing network detours or loops.
   - When localized non-Wi-Fi EMI spikes (USB-C docks or power supplies near `Wohnzimmer_Buchregal`), PHY error rates surge unnoticed until volume dips (DPC ducking) occur.
2. **Alert Delivery Gap**:
   - There is no proactive alert mechanism when Kenneth is away or not actively looking at the web UI or companion app.
3. **Companion App Distribution Gap**:
   - The Android companion APK is compiled locally during development, but lacks a frictionless distribution mechanism for Kenneth to download and update the app directly on his phone without an IDE or USB cable.

## Decision

1. **Autonomous 24/7 Watchdog Engine (`backend/app/modules/watchdog_engine.py`)**:
   - Integrated with the existing background `telemetry_daemon` (running every 60s, or on-demand).
   - Evaluates system state against defined alert thresholds using canonical `WatchdogAnomalyType`:
     - `GHOST_GROUP`: Any zone where `is_ghost_group == True`.
     - `STP_ROOT_USURPED`: Evaluates `snapshot.is_root_healthy is False` or `not snapshot.designated_stp_root.strip().lower().startswith("9000.542a1b63fe6e")`, scoped to a single household-level debounced incident card.
     - `EMI_BURST`: Any speaker with null-safe telemetry reporting `(p.ofdm_ani_level is not None and p.ofdm_ani_level >= 7) or (p.phy_error_rate is not None and p.phy_error_rate > 100.0)`.
     - `PLAYER_OFFLINE`: Any Sonos player transitioning from reachable to unreachable (`is_reachable == False`).
   - **Incident Debouncing**: State transitions trigger alerts once, suppressing duplicate notices for 15 minutes unless state changes or resolves. Auto-healed incidents terminate cleanly without secondary duplicate RESOLVED alerts.

2. **Autonomous Ghost Group Self-Healing Policy (`AutoHealPolicy`)**:
   - `auto_heal_ghost_groups` is enabled by default (`true`).
   - When `GHOST_GROUP` fires, the watchdog automatically executes UPnP `BecomeCoordinatorOfStandaloneGroup` across affected zones within 5 seconds.
   - **Atomic PostgreSQL Synchronization**: Calls `await repo.apply_ghost_flush(flush_result)` immediately to keep the database and all clients synchronized without waiting for the next background collection cycle.
   - Posts an immediate notification: *"⚡ Ghost Group Auto-Healed on [Zone]: Restored standalone coordinator to prevent Spotify playback lockup."*
   - Physical faults (STP root usurpation, hardware EMI) are not auto-healed; the watchdog alerts Kenneth with concrete physical remediation instructions.

3. **Telegram Bot Alert Channel (`TelegramAlertAdapter`)**:
   - Sends formatted Markdown notification cards directly to Kenneth's Telegram chat via Telegram Bot API (`https://api.telegram.org/bot<TOKEN>/sendMessage`).
   - Configuration via environment variables:
     - `TELEGRAM_BOT_TOKEN`: Telegram Bot API token.
     - `TELEGRAM_CHAT_ID`: Recipient Telegram chat ID.
     - `TELEGRAM_ALERTS_ENABLED`: Boolean flag (default `false` if unconfigured, activates when credentials exist).
   - Clean degradation: If credentials are not set, alerts are logged internally without failing daemon runs.
   - REST endpoints exposed on backend:
     - `GET /api/watchdog/status`: Current watchdog state, active alerts, auto-heal history.
     - `POST /api/watchdog/test-alert`: Sends a test alert card to verify Telegram connectivity.
     - `POST /api/watchdog/toggle-auto-heal`: Enables or disables autonomous ghost-group self-healing.

4. **Mini PC Local APK Distribution Server (`/install` & QR Code)**:
   - Backend hosts `GET /api/companion/apk` to download the compiled `sonos-network-companion.apk`.
   - Backend serves `GET /install` containing a mobile-friendly HTML landing page with a dynamic QR code pointing to `http://192.168.55.60:8001/api/companion/apk` (or current host).
   - Web frontend adds an "📱 Install Android App" button in the header that displays the QR code for instant phone camera scanning.
   - Works seamlessly over local Wi-Fi (`192.168.10.0/24`, `192.168.55.0/24`) and Firewalla WireGuard VPN.

5. **GitHub Actions CI/CD Build Workflow**:
   - Adds `.github/workflows/android-release.yml` to compile and verify Android debug/release APK artifacts on git push or workflow dispatch.

## Consequences

- **Positive**:
  - The sound system gains autonomous immunity to the #1 Sonos S2 grouping bug: Ghost groups are flushed automatically before anyone complains of audio failure.
  - Kenneth is notified in real time on Telegram whenever STP roots are usurped or severe RF interference occurs.
  - The Android companion app can be installed and updated on any family phone in 10 seconds via QR code.
- **Trade-offs / Limitations**:
  - Requires Telegram Bot credentials (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`) configured in the Mini PC `.env` to enable Telegram alerts.
  - Mini PC must have the latest compiled APK stored in `backend/app/static/apk/` to serve local QR downloads.
