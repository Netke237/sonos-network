from datetime import datetime, timezone
import pytest
from unittest.mock import AsyncMock

from app.main import create_app
from app.models.entities import ConnectionMode
from app.schemas.topology import (
    GhostFlushResult,
    GhostFlushZoneResult,
    HouseholdSonosSnapshot,
    PlayerTelemetryDto,
)
from app.modules.watchdog_engine import (
    WatchdogAnomalyType,
    WatchdogEngine,
    AutoHealCoordinator,
)
from app.modules.sonos_telemetry import FakeSonosAdapter
from app.modules.wifi_omada import FakeWiFiAdapter
from app.repositories.topology_repository import SqlAlchemyTopologyRepository


class MockAlertChannel:
    def __init__(self):
        self.sent_alerts = []

    def is_configured(self) -> bool:
        return True

    async def send_alert(self, alert) -> bool:
        self.sent_alerts.append(alert)
        return True

    async def send_raw_message(self, text: str) -> bool:
        return True


def _make_ghost_snapshot(now: datetime) -> HouseholdSonosSnapshot:
    player = PlayerTelemetryDto(
        rincon_uuid="RINCON_KUECHE",
        zone_name="Küche",
        room_name="Küche",
        is_reachable=True,
        connection_mode=ConnectionMode.SONOSNET_MODE,
        ieee_channel=6,
        ofdm_ani_level=2,
        noise_floor_dbm=-105,
        phy_error_total=5,
        phy_error_rate=0.5,
        ip_address="192.168.10.150",
        designated_root="9000.542a1b63fe6e",
        is_ghost_group=True,
    )
    return HouseholdSonosSnapshot(
        batch_id="batch-ghost",
        captured_at=now,
        consumer_id="test",
        designated_stp_root="9000.542a1b63fe6e",
        is_root_healthy=True,
        total_players=1,
        reachable_players=1,
        ghost_group_count=1,
        has_ghost_groups=True,
        ghost_group_zones=["Küche"],
        players=[player],
        mesh_links=[],
    )


@pytest.mark.asyncio
async def test_auto_heal_coordinator_triggers_flush_and_db_sync():
    now = datetime(2026, 10, 13, 14, 0, 0, tzinfo=timezone.utc)
    engine = WatchdogEngine()
    channel = MockAlertChannel()

    sonos_adapter = FakeSonosAdapter(probe_interval_sec=0.01)
    fake_flush = GhostFlushResult(
        flushed_count=1,
        flushed_zones=["Küche"],
        results=[
            GhostFlushZoneResult(
                zone_name="Küche",
                rincon_uuid="RINCON_KUECHE",
                ip_address="192.168.10.150",
                previous_group_id="RINCON_GHOST:1",
                new_group_id="RINCON_KUECHE:0",
                status="FLUSHED",
            )
        ],
        captured_at=now,
    )
    sonos_adapter.flush_ghost_groups = AsyncMock(return_value=fake_flush)

    repo_mock = AsyncMock(spec=SqlAlchemyTopologyRepository)

    coordinator = AutoHealCoordinator(
        watchdog_engine=engine,
        sonos_adapter=sonos_adapter,
        alert_channel=channel,
    )

    snapshot = _make_ghost_snapshot(now)
    alerts = await coordinator.handle_snapshot(snapshot, repo=repo_mock)

    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.anomaly_type == WatchdogAnomalyType.GHOST_GROUP
    assert alert.auto_healed is True

    # 1. UPnP flush executed targeting ONLY affected zone IP (P3-CF-04)
    sonos_adapter.flush_ghost_groups.assert_awaited_once_with(zone_ips=["192.168.10.150"])

    # 2. Atomic PostgreSQL synchronization executed (P3-F-02)
    repo_mock.apply_ghost_flush.assert_awaited_once_with(fake_flush)

    # 3. Dispatched alert card via Telegram
    assert len(channel.sent_alerts) == 1
    assert channel.sent_alerts[0].auto_healed is True


@pytest.mark.asyncio
async def test_auto_heal_coordinator_disabled_policy():
    now = datetime(2026, 10, 13, 14, 0, 0, tzinfo=timezone.utc)
    engine = WatchdogEngine()
    engine.set_auto_heal(False)
    channel = MockAlertChannel()

    sonos_adapter = FakeSonosAdapter(probe_interval_sec=0.01)
    sonos_adapter.flush_ghost_groups = AsyncMock()

    repo_mock = AsyncMock(spec=SqlAlchemyTopologyRepository)

    coordinator = AutoHealCoordinator(
        watchdog_engine=engine,
        sonos_adapter=sonos_adapter,
        alert_channel=channel,
    )

    snapshot = _make_ghost_snapshot(now)
    alerts = await coordinator.handle_snapshot(snapshot, repo=repo_mock)

    assert len(alerts) == 1
    assert alerts[0].auto_healed is False

    # No flush executed when disabled
    sonos_adapter.flush_ghost_groups.assert_not_awaited()
    repo_mock.apply_ghost_flush.assert_not_awaited()

    # Standard critical alert dispatched
    assert len(channel.sent_alerts) == 1
    assert channel.sent_alerts[0].auto_healed is False


@pytest.mark.asyncio
async def test_daemon_loop_hooks_auto_heal():
    sonos_adapter = FakeSonosAdapter(probe_interval_sec=0.01)
    wifi_adapter = FakeWiFiAdapter()
    engine = WatchdogEngine()
    channel = MockAlertChannel()

    app = create_app(
        database_url="sqlite+aiosqlite:///:memory:",
        sonos_adapter=sonos_adapter,
        wifi_adapter=wifi_adapter,
        watchdog_engine=engine,
        alert_channel=channel,
    )

    async with app.router.lifespan_context(app):
        daemon = app.state.telemetry_daemon
        cycle_result = await daemon.collect_cycle()
        assert cycle_result["status"] == "ok"
        assert "watchdog_alerts_count" in cycle_result


@pytest.mark.asyncio
async def test_auto_heal_failed_flush_keeps_alert_active():
    """P3-R2-03: When UPnP flush returns FAILED status or does not include zone, alert is not marked auto_healed."""
    now = datetime(2026, 10, 13, 14, 0, 0, tzinfo=timezone.utc)
    engine = WatchdogEngine()
    channel = MockAlertChannel()

    sonos_adapter = FakeSonosAdapter(probe_interval_sec=0.01)
    failed_flush = GhostFlushResult(
        flushed_count=0,
        flushed_zones=[],
        results=[
            GhostFlushZoneResult(
                zone_name="Küche",
                rincon_uuid="RINCON_KUECHE",
                ip_address="192.168.10.150",
                previous_group_id="RINCON_GHOST:1",
                new_group_id="RINCON_KUECHE:0",
                status="FAILED",
            )
        ],
        captured_at=now,
    )
    sonos_adapter.flush_ghost_groups = AsyncMock(return_value=failed_flush)

    coordinator = AutoHealCoordinator(
        watchdog_engine=engine,
        sonos_adapter=sonos_adapter,
        alert_channel=channel,
    )

    snapshot = _make_ghost_snapshot(now)
    alerts = await coordinator.handle_snapshot(snapshot)

    assert len(alerts) == 1
    assert alerts[0].auto_healed is False
    assert len(engine.get_active_incidents()) == 1
    assert engine.get_status().is_healthy is False

