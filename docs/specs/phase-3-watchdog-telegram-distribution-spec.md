# Spec: Phase 3 — Autonomous 24/7 Watchdog, Telegram Alerts, Self-Healing Ghost Group Sanitizer & Companion Distribution

## 1. Problem Statement

Phase 1 deployed the centralized Always-On Mini PC platform (`FastAPI + PostgreSQL`), Phase 1.5 delivered the interactive draggable topology canvas, and Phase 2 completed the native Android companion app. While users can manually poll telemetry and trigger 1-click actions from either the web dashboard or Android phone, the system is fundamentally passive:

1. **Passive Incident Discovery**:
   - When a Ghost Group forms (e.g., when a family member ungroups rooms in the official Sonos app while streaming Spotify), the remaining rooms are locked with cloud `"Couldn't play content"` errors and `HTTP 500` join failures. Currently, this is only resolved when Kenneth notices the music stopped and manually clicks "Flush Ghost Groups".
   - When an STP Root Usurpation occurs (e.g., someone patches an Ethernet cable into Noah's or Nicolas' bedroom speaker, or plugs in the basement Play:3), the lower MAC address usurps `Wohnzimmer_Bookshelf` as STP root across the BPDU pass-through `Netgear GS316EP`, causing network detours or loops.
   - When localized non-Wi-Fi EMI spikes (USB-C docks or power supplies near `Wohnzimmer_Buchregal`), PHY error rates surge unnoticed until volume dips (DPC ducking) occur.
2. **Alert Delivery Gap**:
   - There is no proactive alert mechanism when Kenneth is away or not actively looking at the web UI or companion app.
3. **Companion App Distribution Gap**:
   - The Android companion APK is compiled locally during development, but lacks a frictionless distribution mechanism for Kenneth to download and update the app directly on his phone without an IDE or USB cable.

---

## 2. Solution & Scope

1. **Autonomous 24/7 Watchdog Engine (`backend/app/modules/watchdog_engine.py`)**:
   - Evaluates household snapshots periodically (hooked to the 60s background collector daemon) and on-demand.
   - Detects 4 core anomaly classes:
     - `GHOST_GROUP_DETECTED`: Any zone where `is_ghost_group == True`.
     - `STP_ROOT_USURPED`: Designated root is not `9000.542a1b63fe6e` (`Wohnzimmer_Bookshelf`).
     - `EMI_BURST_DETECTED`: Any speaker reporting `phy_error_rate > 100.0` or `ofdm_ani_level >= 7`.
     - `PLAYER_OFFLINE`: Any Sonos player transitioning from reachable to unreachable.
   - **Incident Debouncer**:
     - Tracks incident state keyed by `(anomaly_type, entity_id)` with `first_detected_at`, `last_alerted_at`, and `state`.
     - Suppresses duplicate alerts for 15 minutes while the condition persists.
     - Dispatches an explicit "RESOLVED" notification when the anomaly clears.
2. **Autonomous Ghost Group Self-Healing Policy (`AutoHealPolicy`)**:
   - `auto_heal_ghost_groups` is enabled by default (`true`).
   - When `GHOST_GROUP_DETECTED` occurs, the watchdog automatically executes UPnP `BecomeCoordinatorOfStandaloneGroup` across affected zones within 5 seconds.
   - Posts an immediate notification: *"⚡ Ghost Group Auto-Healed on [Zone]: Restored standalone coordinator to prevent Spotify playback lockup."*
   - Physical faults (STP root usurpation, hardware EMI) are not auto-healed; the watchdog alerts Kenneth with concrete physical remediation instructions.
3. **Telegram Bot Alert Channel (`TelegramAlertAdapter`)**:
   - Sends formatted Markdown notification cards directly to Kenneth's Telegram chat via Telegram Bot API (`https://api.telegram.org/bot<TOKEN>/sendMessage`).
   - Configuration via environment variables (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_ALERTS_ENABLED`).
   - Clean degradation: If credentials are not set, alerts are logged internally without failing daemon runs.
   - REST endpoints exposed on backend:
     - `GET /api/watchdog/status`: Current watchdog state, active alerts, auto-heal history.
     - `POST /api/watchdog/test-alert`: Sends a test alert card to verify Telegram connectivity.
     - `POST /api/watchdog/toggle-auto-heal`: Enables or disables autonomous ghost-group self-healing.
4. **Mini PC Local APK Distribution Server (`/install` & QR Code)**:
   - Backend hosts `GET /api/companion/apk` to download compiled `sonos-network-companion.apk`.
   - Backend serves `GET /install` containing a mobile-friendly HTML landing page with a dynamic QR code pointing to `http://192.168.55.60:8001/api/companion/apk` (or current host).
   - Web frontend adds an "📱 Install Android App" button in the header that displays the QR code for instant phone camera scanning.
   - Works seamlessly over local Wi-Fi (`192.168.10.0/24`, `192.168.55.0/24`) and Firewalla WireGuard VPN.
5. **GitHub Actions CI/CD Build Workflow**:
   - Adds `.github/workflows/android-release.yml` to compile and verify Android debug/release APK artifacts on git push or workflow dispatch.

---

## 3. Deep Modules & Architecture Boundaries (`/codebase-design`)

```
+-----------------------------------------------------------------------------------+
|                        Always-On Telemetry Daemon (60s loop)                      |
+-----------------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------------+
|                                 Watchdog Engine                                   |
|   - Evaluates household snapshots for anomalies                                   |
|   - Manages stateful incident debouncing (15 min window)                          |
+-----------------------------------------------------------------------------------+
          |                                                       |
          v                                                       v
+-----------------------------+               +-------------------------------------+
|     AutoHealCoordinator     |               |         AlertChannelPort            |
|   - If GHOST_GROUP & enabled|               |   - Formats incident cards          |
|   - Invokes UPnP flush      |               |   - Sends Telegram bot messages     |
|   - Records AutoHealEvent   |               |   - Degrades safely if unconfigured |
+-----------------------------+               +-------------------------------------+
                                                                  |
                                                                  v
                                              +-------------------------------------+
                                              |       Kenneth's Telegram Chat       |
                                              |   🚨 STP Root Usurpation Alert      |
                                              |   ⚡ Ghost Group Auto-Healed        |
                                              |   ⚠️ Severe 2.4GHz EMI Spike        |
                                              +-------------------------------------+
```

### Module 1: `WatchdogModule` (`backend/app/modules/watchdog_engine.py`)
- **Seam Protocol Interface**:
  ```python
  class WatchdogAlert(BaseModel):
      id: str
      incident_key: str
      anomaly_type: str        # GHOST_GROUP | STP_ROOT_USURPED | EMI_BURST | PLAYER_OFFLINE
      severity: str            # CRITICAL | MARGINAL | INFO
      title: str
      description: str
      remediation_guide: str
      detected_at: datetime
      auto_healed: bool = False
      resolved_at: datetime | None = None

  class WatchdogEnginePort(Protocol):
      async def inspect_snapshot(self, snapshot: HouseholdSonosSnapshot) -> list[WatchdogAlert]: ...
      async def get_active_incidents(self) -> list[WatchdogAlert]: ...
      async def toggle_auto_heal(self, enabled: bool) -> bool: ...
      def is_auto_heal_enabled(self) -> bool: ...
  ```

### Module 2: `TelegramAlertModule` (`backend/app/modules/telegram_alerts.py`)
- **Seam Protocol Interface**:
  ```python
  class AlertChannelPort(Protocol):
      async def send_alert(self, alert: WatchdogAlert) -> bool: ...
      async def send_raw_message(self, text: str) -> bool: ...
      def is_configured(self) -> bool: ...
  ```

### Module 3: `CompanionDistributionModule` (`backend/app/main.py` + `backend/app/static/`)
- Endpoints:
  - `GET /api/companion/apk`: Serves `sonos-network-companion.apk`.
  - `GET /install`: Responsive HTML QR landing page for phone camera install.

---

## 4. Acceptance Criteria & Invariants

- **[G1] STP Root Preservation**: Alert fires immediately if designated root != `9000.542a1b63fe6e`.
- **[G2] Ghost Group Auto-Heal**: When enabled, ghost groups are flushed within 5 seconds of detection.
- **[G3] Alert Debouncing**: Recurring alert suppressed for 15 minutes unless resolved or state changes.
- **[G4] Telegram Graceful Degradation**: Daemon runs with 0 errors even when Telegram credentials are unset.
- **[G5] 1-Tap QR Distribution**: `/install` renders clean QR code leading directly to APK download.
