from datetime import datetime, timedelta, timezone
import pytest

from app.models.entities import ConnectionMode
from app.schemas.topology import HouseholdSonosSnapshot, PlayerTelemetryDto
from app.modules.watchdog_engine import (
    WatchdogAnomalyType,
    WatchdogAlert,
    WatchdogEngine,
)


def _make_dummy_player(
    rincon_uuid: str,
    zone_name: str,
    room_name: str,
    is_reachable: bool = True,
    ofdm_ani_level: int | None = 2,
    phy_error_rate: float | None = 1.0,
    designated_root: str = "9000.542a1b63fe6e",
    is_ghost_group: bool = False,
) -> PlayerTelemetryDto:
    return PlayerTelemetryDto(
        rincon_uuid=rincon_uuid,
        zone_name=zone_name,
        room_name=room_name,
        is_reachable=is_reachable,
        connection_mode=ConnectionMode.SONOSNET_MODE,
        ieee_channel=6,
        ofdm_ani_level=ofdm_ani_level,
        noise_floor_dbm=-105,
        phy_error_total=10,
        phy_error_rate=phy_error_rate,
        designated_root=designated_root,
        is_ghost_group=is_ghost_group,
    )


def _make_dummy_snapshot(
    players: list[PlayerTelemetryDto],
    designated_stp_root: str = "9000.542a1b63fe6e",
    is_root_healthy: bool = True,
    has_ghost_groups: bool = False,
    ghost_group_zones: list[str] | None = None,
    now: datetime | None = None,
) -> HouseholdSonosSnapshot:
    captured = now or datetime.now(timezone.utc)
    return HouseholdSonosSnapshot(
        batch_id="batch-test",
        captured_at=captured,
        consumer_id="watchdog-test",
        designated_stp_root=designated_stp_root,
        is_root_healthy=is_root_healthy,
        total_players=len(players),
        reachable_players=sum(1 for p in players if p.is_reachable),
        ghost_group_count=len(ghost_group_zones or []),
        has_ghost_groups=has_ghost_groups,
        ghost_group_zones=ghost_group_zones or [],
        players=players,
        mesh_links=[],
    )


def test_ghost_group_detection():
    engine = WatchdogEngine(debounce_seconds=900.0)
    now = datetime(2026, 10, 13, 12, 0, 0, tzinfo=timezone.utc)

    player = _make_dummy_player(
        "RINCON_111", "Küche", "Küche", is_ghost_group=True
    )
    snapshot = _make_dummy_snapshot(
        [player],
        has_ghost_groups=True,
        ghost_group_zones=["Küche"],
        now=now,
    )

    alerts = engine.evaluate_snapshot(snapshot, now=now)
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.anomaly_type == WatchdogAnomalyType.GHOST_GROUP
    assert alert.severity == "CRITICAL"
    assert "Küche" in alert.title
    assert alert.entity_id == "Küche"
    assert alert.cleared is False


def test_stp_root_usurpation_detection_and_formatting_safety():
    engine = WatchdogEngine(debounce_seconds=900.0)
    now = datetime(2026, 10, 13, 12, 0, 0, tzinfo=timezone.utc)

    # 1. Healthy formatted root: "9000.542a1b63fe6e (Wohnzimmer_Bookshelf 192.168.10.230)"
    healthy_player = _make_dummy_player("RINCON_1", "Wohnzimmer_Bookshelf", "Wohnzimmer")
    healthy_snapshot = _make_dummy_snapshot(
        [healthy_player],
        designated_stp_root="9000.542a1b63fe6e (Wohnzimmer_Bookshelf 192.168.10.230)",
        is_root_healthy=True,
        now=now,
    )
    assert engine.evaluate_snapshot(healthy_snapshot, now=now) == []

    # 2. Rogue root usurpation: Keller root "9000.5caafd595eea"
    rogue_player = _make_dummy_player(
        "RINCON_2", "Keller", "Keller", designated_root="9000.5caafd595eea"
    )
    rogue_snapshot = _make_dummy_snapshot(
        [healthy_player, rogue_player],
        designated_stp_root="9000.5caafd595eea",
        is_root_healthy=False,
        now=now,
    )

    alerts = engine.evaluate_snapshot(rogue_snapshot, now=now)
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.anomaly_type == WatchdogAnomalyType.STP_ROOT_USURPED
    assert alert.severity == "CRITICAL"
    assert alert.entity_id == "household"
    assert "9000.5caafd595eea" in alert.description or "9000.5caafd595eea" in alert.title

    # 3. Rogue player root divergence when designated_stp_root string still reports Wohnzimmer_Bookshelf (P3-CF-02)
    engine_divergent = WatchdogEngine(debounce_seconds=900.0)
    divergent_snapshot = _make_dummy_snapshot(
        [healthy_player, rogue_player],
        designated_stp_root="9000.542a1b63fe6e (Wohnzimmer_Bookshelf 192.168.10.230)",
        is_root_healthy=False,
        now=now,
    )
    divergent_alerts = engine_divergent.evaluate_snapshot(divergent_snapshot, now=now)
    assert len(divergent_alerts) == 1
    # Observed root MUST identify the rogue MAC (9000.5caafd595eea), not falsely accuse Wohnzimmer_Bookshelf
    assert "9000.5caafd595eea" in divergent_alerts[0].title
    assert "9000.5caafd595eea" in divergent_alerts[0].description


def test_emi_burst_detection_and_null_safety():
    engine = WatchdogEngine(debounce_seconds=900.0)
    now = datetime(2026, 10, 13, 12, 0, 0, tzinfo=timezone.utc)

    # Player 1: Beam / Ethernet with None for ofdm_ani_level and None for phy_error_rate
    beam = _make_dummy_player(
        "RINCON_BEAM",
        "Fernsehecke",
        "Fernsehecke",
        ofdm_ani_level=None,
        phy_error_rate=None,
    )
    # Player 2: Wohnzimmer_Buchregal with severe EMI (ANI 9, 1126.0 err/s)
    buchregal = _make_dummy_player(
        "RINCON_BUCH",
        "Wohnzimmer_Buchregal",
        "Wohnzimmer",
        ofdm_ani_level=9,
        phy_error_rate=1126.0,
    )
    # Player 3: Speaker with severe ANI 8 but None for phy_error_rate (P3-CF-01)
    rebooted = _make_dummy_player(
        "RINCON_REBOOTED",
        "Büroecke",
        "Büroecke",
        ofdm_ani_level=8,
        phy_error_rate=None,
    )

    snapshot = _make_dummy_snapshot([beam, buchregal, rebooted], now=now)
    alerts = engine.evaluate_snapshot(snapshot, now=now)

    assert len(alerts) == 2
    alert_names = {a.entity_id for a in alerts}
    assert "Wohnzimmer_Buchregal" in alert_names
    assert "Büroecke" in alert_names

    rebooted_alert = next(a for a in alerts if a.entity_id == "Büroecke")
    assert "OFDM ANI 8" in rebooted_alert.description
    assert "PHY err/s N/A" in rebooted_alert.description


def test_player_offline_detection():
    engine = WatchdogEngine(debounce_seconds=900.0)
    now = datetime(2026, 10, 13, 12, 0, 0, tzinfo=timezone.utc)

    offline_player = _make_dummy_player(
        "RINCON_NICOLAS", "Nicolas", "Nicolas", is_reachable=False
    )
    snapshot = _make_dummy_snapshot([offline_player], now=now)

    alerts = engine.evaluate_snapshot(snapshot, now=now)
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.anomaly_type == WatchdogAnomalyType.PLAYER_OFFLINE
    assert alert.entity_id == "Nicolas"
    assert alert.severity == "CRITICAL"


def test_incident_debouncing_and_repetition():
    debounce_sec = 600.0  # 10 minutes
    engine = WatchdogEngine(debounce_seconds=debounce_sec)

    t0 = datetime(2026, 10, 13, 12, 0, 0, tzinfo=timezone.utc)
    offline_player = _make_dummy_player(
        "RINCON_NICOLAS", "Nicolas", "Nicolas", is_reachable=False
    )
    snapshot0 = _make_dummy_snapshot([offline_player], now=t0)

    # Initial alert fires at t0
    alerts0 = engine.evaluate_snapshot(snapshot0, now=t0)
    assert len(alerts0) == 1

    # Repeat poll after 2 minutes (t0 + 120s) -> suppressed by debouncer
    t1 = t0 + timedelta(seconds=120)
    snapshot1 = _make_dummy_snapshot([offline_player], now=t1)
    alerts1 = engine.evaluate_snapshot(snapshot1, now=t1)
    assert len(alerts1) == 0

    # Repeat poll after 11 minutes (t0 + 660s) -> fires repeat alert
    t2 = t0 + timedelta(seconds=660)
    snapshot2 = _make_dummy_snapshot([offline_player], now=t2)
    alerts2 = engine.evaluate_snapshot(snapshot2, now=t2)
    assert len(alerts2) == 1
    assert alerts2[0].anomaly_type == WatchdogAnomalyType.PLAYER_OFFLINE


def test_natural_clearing_vs_auto_heal_suppression():
    engine = WatchdogEngine(debounce_seconds=900.0)
    t0 = datetime(2026, 10, 13, 12, 0, 0, tzinfo=timezone.utc)

    # 1. Natural clearing test (Player comes back online)
    offline_player = _make_dummy_player(
        "RINCON_1", "Eltern", "Elternschlafzimmer", is_reachable=False
    )
    snap_offline = _make_dummy_snapshot([offline_player], now=t0)
    alerts_off = engine.evaluate_snapshot(snap_offline, now=t0)
    assert len(alerts_off) == 1

    # Player recovers online at t1
    t1 = t0 + timedelta(seconds=60)
    online_player = _make_dummy_player(
        "RINCON_1", "Eltern", "Elternschlafzimmer", is_reachable=True
    )
    snap_online = _make_dummy_snapshot([online_player], now=t1)
    alerts_cleared = engine.evaluate_snapshot(snap_online, now=t1)
    assert len(alerts_cleared) == 1
    assert alerts_cleared[0].cleared is True
    assert alerts_cleared[0].severity == "INFO"
    assert "RESOLVED" in alerts_cleared[0].title

    # 2. Auto-heal suppression test (P3-F-06)
    t2 = t1 + timedelta(seconds=60)
    ghost_player = _make_dummy_player(
        "RINCON_2", "Küche", "Küche", is_ghost_group=True
    )
    snap_ghost = _make_dummy_snapshot(
        [online_player, ghost_player],
        has_ghost_groups=True,
        ghost_group_zones=["Küche"],
        now=t2,
    )
    alerts_ghost = engine.evaluate_snapshot(snap_ghost, now=t2)
    assert len(alerts_ghost) == 1
    ghost_key = alerts_ghost[0].incident_key

    # Mark auto_healed on engine
    engine.record_auto_heal(ghost_key)

    # Next cycle at t3, ghost group is gone (healed)
    t3 = t2 + timedelta(seconds=60)
    healed_player = _make_dummy_player(
        "RINCON_2", "Küche", "Küche", is_ghost_group=False
    )
    snap_healed = _make_dummy_snapshot(
        [online_player, healed_player],
        has_ghost_groups=False,
        ghost_group_zones=[],
        now=t3,
    )
    alerts_healed = engine.evaluate_snapshot(snap_healed, now=t3)
    # MUST be 0 alerts — redundant RESOLVED card suppressed for auto-healed incidents
    assert len(alerts_healed) == 0


def test_auto_heal_toggle():
    engine = WatchdogEngine()
    assert engine.is_auto_heal_enabled() is True
    engine.set_auto_heal(False)
    assert engine.is_auto_heal_enabled() is False
    engine.set_auto_heal(True)
    assert engine.is_auto_heal_enabled() is True
