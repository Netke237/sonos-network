from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import logging
from typing import Any, Protocol
import uuid
from pydantic import BaseModel, Field

logger = logging.getLogger("sonos_network.watchdog_engine")

from app.schemas.topology import HouseholdSonosSnapshot


class WatchdogAnomalyType(str, Enum):
    GHOST_GROUP = "GHOST_GROUP"
    STP_ROOT_USURPED = "STP_ROOT_USURPED"
    EMI_BURST = "EMI_BURST"
    PLAYER_OFFLINE = "PLAYER_OFFLINE"


class WatchdogAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    incident_key: str
    anomaly_type: WatchdogAnomalyType
    severity: str  # CRITICAL | MARGINAL | INFO
    title: str
    description: str
    action_required: str
    remediation_guide: str | None = None
    entity_id: str
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    auto_healed: bool = False
    cleared: bool = False
    resolved_at: datetime | None = None

    def model_post_init(self, __context: Any) -> None:
        if self.remediation_guide is None:
            self.remediation_guide = self.action_required
        if self.cleared and self.resolved_at is None:
            self.resolved_at = datetime.now(timezone.utc)


class IncidentState(BaseModel):
    incident_key: str
    anomaly_type: WatchdogAnomalyType
    entity_id: str
    severity: str
    title: str
    description: str
    action_required: str
    first_detected_at: datetime
    last_alerted_at: datetime
    last_seen_at: datetime
    is_active: bool = True
    auto_healed: bool = False


class WatchdogStatusSchema(BaseModel):
    is_healthy: bool
    active_incidents_count: int
    auto_heal_enabled: bool
    active_alerts: list[WatchdogAlert]
    history: list[WatchdogAlert]


class WatchdogEnginePort(Protocol):
    def evaluate_snapshot(
        self, snapshot: HouseholdSonosSnapshot, now: datetime | None = None
    ) -> list[WatchdogAlert]: ...

    def get_active_incidents(self) -> list[IncidentState]: ...

    def clear_incident(self, incident_key: str) -> None: ...

    def record_auto_heal(self, incident_key: str) -> None: ...

    def set_auto_heal(self, enabled: bool) -> None: ...

    def is_auto_heal_enabled(self) -> bool: ...

    def get_status(self) -> WatchdogStatusSchema: ...


class WatchdogEngine:
    def __init__(
        self,
        debounce_seconds: float = 900.0,
        auto_heal_enabled: bool = True,
    ) -> None:
        self.debounce_seconds = debounce_seconds
        self._auto_heal_enabled = auto_heal_enabled
        self._incidents: dict[str, IncidentState] = {}
        self._history: list[WatchdogAlert] = []

    def is_auto_heal_enabled(self) -> bool:
        return self._auto_heal_enabled

    def set_auto_heal(self, enabled: bool) -> None:
        self._auto_heal_enabled = enabled

    def get_active_incidents(self) -> list[IncidentState]:
        return [
            inc
            for inc in self._incidents.values()
            if inc.is_active and not inc.auto_healed
        ]

    def clear_incident(self, incident_key: str) -> None:
        if incident_key in self._incidents:
            self._incidents[incident_key].is_active = False

    def record_auto_heal(self, incident_key: str) -> None:
        if incident_key in self._incidents:
            self._incidents[incident_key].auto_healed = True

    def get_status(self) -> WatchdogStatusSchema:
        active = self.get_active_incidents()
        active_alerts: list[WatchdogAlert] = [
            WatchdogAlert(
                id=str(uuid.uuid4()),
                incident_key=inc.incident_key,
                anomaly_type=inc.anomaly_type,
                severity=inc.severity,
                title=inc.title,
                description=inc.description,
                action_required=inc.action_required,
                entity_id=inc.entity_id,
                detected_at=inc.first_detected_at,
                auto_healed=inc.auto_healed,
                cleared=False,
            )
            for inc in active
        ]
        return WatchdogStatusSchema(
            is_healthy=len(active) == 0,
            active_incidents_count=len(active),
            auto_heal_enabled=self._auto_heal_enabled,
            active_alerts=active_alerts,
            history=list(self._history[-50:]),
        )

    def evaluate_snapshot(
        self, snapshot: HouseholdSonosSnapshot, now: datetime | None = None
    ) -> list[WatchdogAlert]:
        current_time = now or datetime.now(timezone.utc)
        current_detected: dict[str, dict] = {}

        # 1. Evaluate Ghost Groups (P3-CF-08: deduplicated union of header zones and player flags)
        if snapshot.has_ghost_groups or any(p.is_ghost_group for p in snapshot.players):
            zones_set = set(snapshot.ghost_group_zones)
            for p in snapshot.players:
                if p.is_ghost_group:
                    zones_set.add(p.zone_name or p.room_name or p.rincon_uuid)
            zones = sorted(zones_set)
            for zone in zones:
                key = f"{WatchdogAnomalyType.GHOST_GROUP.value}:{zone}"
                current_detected[key] = {
                    "anomaly_type": WatchdogAnomalyType.GHOST_GROUP,
                    "entity_id": zone,
                    "severity": "CRITICAL",
                    "title": f"Ghost Group Detected on {zone}",
                    "description": f"Zone '{zone}' is operating under a mismatched coordinator Group ID prefix, risking cloud streaming playback lockups.",
                    "action_required": "Trigger UPnP BecomeCoordinatorOfStandaloneGroup across affected zones.",
                }

        # 2. Evaluate STP Root Usurpation (P3-CF-02: always scan players for rogue root MAC)
        root_mac_prefix = "9000.542a1b63fe6e"
        designated_root = snapshot.designated_stp_root.strip()
        is_usurped = False
        observed_root = designated_root

        if snapshot.is_root_healthy is False or not designated_root.lower().startswith(root_mac_prefix):
            is_usurped = True

        for p in snapshot.players:
            if p.designated_root and not p.designated_root.strip().lower().startswith(root_mac_prefix):
                is_usurped = True
                observed_root = p.designated_root.strip()
                break

        if is_usurped:
            # Consolidate household into single incident key (P3-F-05)
            key = f"{WatchdogAnomalyType.STP_ROOT_USURPED.value}:household"
            current_detected[key] = {
                "anomaly_type": WatchdogAnomalyType.STP_ROOT_USURPED,
                "entity_id": "household",
                "severity": "CRITICAL",
                "title": f"STP Root Bridge Usurped: {observed_root}",
                "description": f"Observed STP Designated Root '{observed_root}' usurped Wohnzimmer_Bookshelf (9000.542a1b63fe6e), risking network detours and broadcast loops.",
                "action_required": "Unplug Ethernet from rogue node (Keller) or disable Wi-Fi/SonosNet on secondary wired leaf; preserve Wohnzimmer_Bookshelf as sole root bridge.",
            }

        # 3. Evaluate EMI Burst (P3-CF-01: Null-safe Atheros formatting)
        for p in snapshot.players:
            has_emi = (p.ofdm_ani_level is not None and p.ofdm_ani_level >= 7) or (
                p.phy_error_rate is not None and p.phy_error_rate > 100.0
            )
            if has_emi:
                speaker = p.zone_name or p.room_name or p.rincon_uuid
                key = f"{WatchdogAnomalyType.EMI_BURST.value}:{speaker}"
                severity = "CRITICAL" if (p.phy_error_rate is not None and p.phy_error_rate > 100.0) or (
                    p.ofdm_ani_level is not None and p.ofdm_ani_level >= 8
                ) else "MARGINAL"
                ani_str = f"OFDM ANI {p.ofdm_ani_level}" if p.ofdm_ani_level is not None else "OFDM ANI N/A"
                phy_str = f"{p.phy_error_rate:.1f} PHY err/s" if p.phy_error_rate is not None else "N/A PHY err/s"
                current_detected[key] = {
                    "anomaly_type": WatchdogAnomalyType.EMI_BURST,
                    "entity_id": speaker,
                    "severity": severity,
                    "title": f"Severe 2.4 GHz EMI Burst on {speaker}",
                    "description": f"Player '{speaker}' recorded {ani_str} and {phy_str}, risking DPC volume ducking and packet drops.",
                    "action_required": "Inspect local USB-C docks / power supplies near speaker; relocate speaker 1-2m laterally.",
                }

        # 4. Evaluate Player Reachability Transitions
        for p in snapshot.players:
            if not p.is_reachable:
                speaker = p.zone_name or p.room_name or p.rincon_uuid
                key = f"{WatchdogAnomalyType.PLAYER_OFFLINE.value}:{speaker}"
                current_detected[key] = {
                    "anomaly_type": WatchdogAnomalyType.PLAYER_OFFLINE,
                    "entity_id": speaker,
                    "severity": "CRITICAL",
                    "title": f"Sonos Player Offline: {speaker}",
                    "description": f"Player '{speaker}' ({p.rincon_uuid}) failed reachability probe across VLAN 10.",
                    "action_required": "Check player power cord, Ethernet link, or Wi-Fi AP association.",
                }

        alerts_to_emit: list[WatchdogAlert] = []

        # Process detected anomalies with debouncing
        for key, data in current_detected.items():
            if key in self._incidents and self._incidents[key].is_active:
                inc = self._incidents[key]
                inc.last_seen_at = current_time
                elapsed = (current_time - inc.last_alerted_at).total_seconds()
                if elapsed >= self.debounce_seconds:
                    # Debounce interval expired: re-alert
                    inc.last_alerted_at = current_time
                    alert = WatchdogAlert(
                        incident_key=key,
                        anomaly_type=data["anomaly_type"],
                        severity=data["severity"],
                        title=f"[REPEATING] {data['title']}",
                        description=data["description"],
                        action_required=data["action_required"],
                        entity_id=data["entity_id"],
                        detected_at=current_time,
                        cleared=False,
                    )
                    alerts_to_emit.append(alert)
                    self._history.append(alert)
            else:
                # Brand new or reactivated incident
                inc = IncidentState(
                    incident_key=key,
                    anomaly_type=data["anomaly_type"],
                    entity_id=data["entity_id"],
                    severity=data["severity"],
                    title=data["title"],
                    description=data["description"],
                    action_required=data["action_required"],
                    first_detected_at=current_time,
                    last_alerted_at=current_time,
                    last_seen_at=current_time,
                    is_active=True,
                    auto_healed=False,
                )
                self._incidents[key] = inc
                alert = WatchdogAlert(
                    incident_key=key,
                    anomaly_type=data["anomaly_type"],
                    severity=data["severity"],
                    title=data["title"],
                    description=data["description"],
                    action_required=data["action_required"],
                    entity_id=data["entity_id"],
                    detected_at=current_time,
                    cleared=False,
                )
                alerts_to_emit.append(alert)
                self._history.append(alert)

        # Process cleared incidents
        for key, inc in list(self._incidents.items()):
            if inc.is_active and key not in current_detected:
                inc.is_active = False
                if inc.auto_healed:
                    # P3-F-06: Suppress secondary RESOLVED card for auto-healed incidents
                    continue

                resolve_alert = WatchdogAlert(
                    incident_key=key,
                    anomaly_type=inc.anomaly_type,
                    severity="INFO",
                    title=f"RESOLVED: {inc.title}",
                    description=f"Condition on '{inc.entity_id}' has normalized. Telemetry within healthy parameters.",
                    action_required="None. Anomaly cleared.",
                    entity_id=inc.entity_id,
                    detected_at=current_time,
                    cleared=True,
                )
                alerts_to_emit.append(resolve_alert)
                self._history.append(resolve_alert)

        return alerts_to_emit


class AutoHealCoordinator:
    def __init__(
        self,
        watchdog_engine: WatchdogEnginePort,
        sonos_adapter: Any,
        alert_channel: Any | None = None,
    ) -> None:
        self.watchdog_engine = watchdog_engine
        self.sonos_adapter = sonos_adapter
        self.alert_channel = alert_channel

    async def handle_snapshot(
        self,
        snapshot: HouseholdSonosSnapshot,
        repo: Any | None = None,
        now: datetime | None = None,
    ) -> list[WatchdogAlert]:
        alerts = self.watchdog_engine.evaluate_snapshot(snapshot, now=now)
        flush_res = None
        for alert in alerts:
            if (
                alert.anomaly_type == WatchdogAnomalyType.GHOST_GROUP
                and not alert.cleared
                and self.watchdog_engine.is_auto_heal_enabled()
            ):
                try:
                    if flush_res is None:
                        logger.info("Executing autonomous UPnP Ghost Group flush...")
                        flush_res = await self.sonos_adapter.flush_ghost_groups()
                        if repo is not None:
                            # Atomic PostgreSQL synchronization (P3-F-02)
                            await repo.apply_ghost_flush(flush_res)
                    self.watchdog_engine.record_auto_heal(alert.incident_key)
                    alert.auto_healed = True
                except Exception as err:
                    logger.error("Auto-heal flush failed for zone %s: %s", alert.entity_id, err)

            if self.alert_channel is not None:
                await self.alert_channel.send_alert(alert)

        return alerts

