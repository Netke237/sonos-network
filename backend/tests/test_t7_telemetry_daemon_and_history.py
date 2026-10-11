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
    )
    return app


@pytest.mark.asyncio
async def test_daemon_collect_cycle_and_retention_pruning(test_app):
    """T7: Daemon runs collection cycle with isolated cursor and prunes old background samples without deleting historical seeds."""
    async with test_app.router.lifespan_context(test_app):
        session_factory = test_app.state.session_factory
        sonos_adapter = test_app.state.sonos_adapter
        wifi_adapter = test_app.state.wifi_adapter

        daemon = ScheduledTelemetryCollector(
            session_factory=session_factory,
            sonos_adapter=sonos_adapter,
            wifi_adapter=wifi_adapter,
            interval_sec=60.0,
            retention_days=7,
            consumer_id="background-60s",
        )

        # Run one collection cycle
        cycle_res = await daemon.collect_cycle()
        assert cycle_res["status"] == "ok"
        assert cycle_res["total_players"] == 14
        batch_id = cycle_res["batch_id"]

        # Verify snapshots were persisted with consumer_id == "background-60s"
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

            # Insert an expired background sample (10 days ago)
            expired_bg = SonosTelemetrySnapshot(
                batch_id="old-bg-batch",
                captured_at=datetime.now(timezone.utc) - timedelta(days=10),
                consumer_id="background-60s",
                rincon_uuid="RINCON_TEST_EXPIRED",
                zone_name="Nicolas",
                is_reachable=True,
            )
            # Insert an expired historical seed sample (30 days ago) with consumer_id == "historical-seed"
            historical_seed = SonosTelemetrySnapshot(
                batch_id="hist-seed-batch",
                captured_at=datetime.now(timezone.utc) - timedelta(days=30),
                consumer_id="historical-seed",
                rincon_uuid="RINCON_TEST_SEED",
                zone_name="Nicolas",
                is_reachable=True,
            )
            session.add_all([expired_bg, historical_seed])
            await session.commit()

            # Execute retention pruning
            repo = SqlAlchemyTopologyRepository(session)
            pruned_count = await repo.prune_expired_telemetry(
                retention_days=7, consumer_id="background-60s"
            )
            assert pruned_count >= 1

            # Verify expired background sample was pruned
            check_bg = await session.execute(
                select(SonosTelemetrySnapshot).where(
                    SonosTelemetrySnapshot.batch_id == "old-bg-batch"
                )
            )
            assert check_bg.scalar_one_or_none() is None

            # Verify historical seed was NOT pruned
            check_seed = await session.execute(
                select(SonosTelemetrySnapshot).where(
                    SonosTelemetrySnapshot.batch_id == "hist-seed-batch"
                )
            )
            assert check_seed.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_get_room_history_api(test_app):
    """T7: GET /api/rooms/{room_slug}/history returns time-series telemetry across 1h, 24h, 7d."""
    async with test_app.router.lifespan_context(test_app):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Query history for 'nicolas' over 24h
            resp_24h = await client.get("/api/rooms/nicolas/history?range=24h")
            assert resp_24h.status_code == 200, resp_24h.text
            data_24h = resp_24h.json()

            assert data_24h["room_slug"] == "nicolas"
            assert data_24h["room_name"] == "Nicolas"
            assert data_24h["time_range"] == "24h"
            assert isinstance(data_24h["samples"], list)
            assert "summary" in data_24h

            # Query history for 'nicolas' over 7d
            resp_7d = await client.get("/api/rooms/nicolas/history?range=7d")
            assert resp_7d.status_code == 200
            data_7d = resp_7d.json()
            assert data_7d["time_range"] == "7d"

            # Check invalid range returns 422
            resp_invalid = await client.get("/api/rooms/nicolas/history?range=invalid")
            assert resp_invalid.status_code == 422

            # Check 404 for unknown room
            resp_404 = await client.get("/api/rooms/unknown-room/history?range=24h")
            assert resp_404.status_code == 404


@pytest.mark.asyncio
async def test_daemon_status_and_collect_now_endpoints(test_app):
    """T7: GET /api/daemon/status and POST /api/daemon/collect-now endpoints."""
    async with test_app.router.lifespan_context(test_app):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Check daemon status
            status_resp = await client.get("/api/daemon/status")
            assert status_resp.status_code == 200
            status_data = status_resp.json()
            assert "is_running" in status_data
            assert "interval_sec" in status_data

            # Trigger an immediate collect cycle
            collect_resp = await client.post("/api/daemon/collect-now")
            assert collect_resp.status_code == 200
            collect_data = collect_resp.json()
            assert collect_data["status"] == "ok"
            assert collect_data["total_players"] == 14
            assert "batch_id" in collect_data
