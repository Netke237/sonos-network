import asyncio
from datetime import datetime, timedelta, timezone
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.main import create_app
from app.models.entities import SonosTelemetrySnapshot
from app.modules.sonos_telemetry import FakeSonosAdapter
from app.modules.telemetry_daemon import ScheduledTelemetryCollector
from app.modules.wifi_omada import FakeWiFiAdapter
from app.repositories.topology_repository import SqlAlchemyTopologyRepository


@pytest.fixture
def test_app():
    app = create_app(
        database_url="sqlite+aiosqlite:///:memory:",
        sonos_adapter=FakeSonosAdapter(),
        wifi_adapter=FakeWiFiAdapter(),
        enable_daemon=False,
    )
    return app


@pytest.mark.asyncio
async def test_daemon_lifespan_starts_and_stops():
    """T7 Seam: Verify that create_app with enable_daemon=True starts collector in lifespan and stops on exit."""
    app = create_app(
        database_url="sqlite+aiosqlite:///:memory:",
        sonos_adapter=FakeSonosAdapter(),
        wifi_adapter=FakeWiFiAdapter(),
        enable_daemon=True,
    )
    assert app.state.telemetry_daemon.status().is_running is False
    async with app.router.lifespan_context(app):
        # Must be running during lifespan
        assert app.state.telemetry_daemon.status().is_running is True
        assert app.state.telemetry_daemon.consumer_id == "background-60s"
    # Must be stopped after lifespan exit
    assert app.state.telemetry_daemon.status().is_running is False


@pytest.mark.asyncio
async def test_daemon_cursor_isolation_against_on_demand(test_app):
    """T7 Seam: Verify consumer_id='background-60s' maintains isolated PHY error cursors from 'on-demand'."""
    adapter = test_app.state.sonos_adapter
    # Background collector poll
    snap_bg1 = await adapter.collect_household_snapshot(consumer_id="background-60s")
    assert snap_bg1.consumer_id == "background-60s"

    # On-demand poll in between
    snap_od1 = await adapter.collect_household_snapshot(consumer_id="on-demand")
    assert snap_od1.consumer_id == "on-demand"

    # Second background poll must use background cursor
    snap_bg2 = await adapter.collect_household_snapshot(consumer_id="background-60s")
    assert snap_bg2.consumer_id == "background-60s"


@pytest.mark.asyncio
async def test_daemon_collect_cycle_and_retention_pruning(test_app):
    """T7 Seam: ScheduledTelemetryCollector runs collection cycle and prunes background samples while preserving historical seeds."""
    async with test_app.router.lifespan_context(test_app):
        session_factory = test_app.state.session_factory
        daemon = ScheduledTelemetryCollector(
            session_factory=session_factory,
            sonos_adapter=test_app.state.sonos_adapter,
            wifi_adapter=test_app.state.wifi_adapter,
            interval_sec=60.0,
            retention_days=7,
            consumer_id="background-60s",
        )

        cycle_res = await daemon.collect_cycle()
        assert cycle_res["status"] == "ok"
        assert cycle_res["total_players"] == 14
        batch_id = cycle_res["batch_id"]

        async with session_factory() as session:
            res = await session.execute(
                select(SonosTelemetrySnapshot).where(
                    SonosTelemetrySnapshot.batch_id == batch_id
                )
            )
            rows = list(res.scalars().all())
            assert len(rows) == 14
            for r in rows:
                assert r.consumer_id == "background-60s"

            # Expired background record
            expired_bg = SonosTelemetrySnapshot(
                batch_id="expired-bg-batch",
                captured_at=datetime.now(timezone.utc) - timedelta(days=10),
                consumer_id="background-60s",
                rincon_uuid="RINCON_EXP_BG",
                zone_name="Nicolas",
                is_reachable=True,
            )
            # Expired historical seed
            hist_seed = SonosTelemetrySnapshot(
                batch_id="hist-seed-batch",
                captured_at=datetime.now(timezone.utc) - timedelta(days=30),
                consumer_id="historical-seed",
                rincon_uuid="RINCON_HIST_SEED",
                zone_name="Nicolas",
                is_reachable=True,
            )
            session.add_all([expired_bg, hist_seed])
            await session.commit()

            repo = SqlAlchemyTopologyRepository(session)
            pruned = await repo.prune_expired_telemetry(retention_days=7, consumer_id="background-60s")
            assert pruned >= 1

            check_bg = await session.execute(
                select(SonosTelemetrySnapshot).where(SonosTelemetrySnapshot.batch_id == "expired-bg-batch")
            )
            assert check_bg.scalar_one_or_none() is None

            check_seed = await session.execute(
                select(SonosTelemetrySnapshot).where(SonosTelemetrySnapshot.batch_id == "hist-seed-batch")
            )
            assert check_seed.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_get_room_history_api(test_app):
    """T7 Seam: GET /api/rooms/{room_slug}/history returns time-series telemetry with all metrics."""
    async with test_app.router.lifespan_context(test_app):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp_24h = await client.get("/api/rooms/nicolas/history?range=24h")
            assert resp_24h.status_code == 200
            data_24h = resp_24h.json()
            assert data_24h["room_slug"] == "nicolas"
            assert data_24h["room_name"] == "Nicolas"
            assert data_24h["time_range"] == "24h"
            assert isinstance(data_24h["samples"], list)
            assert "summary" in data_24h
            if data_24h["samples"]:
                s = data_24h["samples"][0]
                assert "timestamp" in s
                assert "peak_ofdm_ani_level" in s
                assert "total_phy_error_rate" in s
                assert "avg_ping_rtt_ms" in s

            resp_7d = await client.get("/api/rooms/nicolas/history?range=7d")
            assert resp_7d.status_code == 200
            assert resp_7d.json()["time_range"] == "7d"

            resp_inv = await client.get("/api/rooms/nicolas/history?range=invalid")
            assert resp_inv.status_code == 422

            resp_404 = await client.get("/api/rooms/nonexistent-room/history?range=24h")
            assert resp_404.status_code == 404


@pytest.mark.asyncio
async def test_daemon_status_and_collect_now_endpoints(test_app):
    """T7 Seam: GET /api/daemon/status and POST /api/daemon/collect-now endpoints."""
    async with test_app.router.lifespan_context(test_app):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            status_resp = await client.get("/api/daemon/status")
            assert status_resp.status_code == 200
            status_data = status_resp.json()
            assert "is_running" in status_data
            assert "interval_sec" in status_data

            collect_resp = await client.post("/api/daemon/collect-now")
            assert collect_resp.status_code == 200
            collect_data = collect_resp.json()
            assert collect_data["status"] == "ok"
            assert collect_data["total_players"] == 14
            assert "batch_id" in collect_data


@pytest.mark.asyncio
async def test_get_room_history_yearly_and_rollup_buckets(test_app):
    """T7 Seam: GET /api/rooms/{room_slug}/history with range=1y/30d/90d supports weekly/monthly rollups."""
    async with test_app.router.lifespan_context(test_app):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp_1y = await client.get("/api/rooms/nicolas/history?range=1y&granularity=monthly")
            assert resp_1y.status_code == 200
            data_1y = resp_1y.json()
            assert data_1y["time_range"] == "1y"
            assert data_1y["granularity"] == "monthly"
            assert "rollup_buckets" in data_1y
            assert isinstance(data_1y["rollup_buckets"], list)
            if data_1y["rollup_buckets"]:
                b = data_1y["rollup_buckets"][0]
                assert "bucket_key" in b
                assert "bucket_label" in b
                assert "start_date" in b
                assert "end_date" in b
                assert "sample_count" in b
                assert "health_grade" in b

            resp_30d = await client.get("/api/rooms/nicolas/history?range=30d&granularity=weekly")
            assert resp_30d.status_code == 200
            data_30d = resp_30d.json()
            assert data_30d["time_range"] == "30d"
            assert data_30d["granularity"] == "weekly"


@pytest.mark.asyncio
async def test_daemon_toggle_endpoint(test_app):
    """T7 Seam: POST /api/daemon/toggle?enabled=false/true toggles the background daemon state."""
    async with test_app.router.lifespan_context(test_app):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Toggle OFF
            off_resp = await client.post("/api/daemon/toggle?enabled=false")
            assert off_resp.status_code == 200
            assert off_resp.json()["is_running"] is False

            # Toggle ON
            on_resp = await client.post("/api/daemon/toggle?enabled=true")
            assert on_resp.status_code == 200
            assert on_resp.json()["is_running"] is True

