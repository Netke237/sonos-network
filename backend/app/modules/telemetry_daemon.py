from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.sonos_telemetry import SonosTelemetryPort
from app.modules.wifi_omada import WiFiTelemetryPort
from app.repositories.topology_repository import SqlAlchemyTopologyRepository
from app.schemas.topology import DaemonStatusSchema

logger = logging.getLogger(__name__)


class ScheduledTelemetryCollector:
    """24/7 background telemetry collector polling live Sonos RF/STP and Wi-Fi infrastructure

    on a scheduled loop, persisting snapshots to PostgreSQL with isolated PhyErrorRate delta
    cursors ('background-60s'), and executing automatic retention pruning of expired raw samples.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        sonos_adapter: SonosTelemetryPort,
        wifi_adapter: WiFiTelemetryPort,
        auto_heal_coordinator: Any | None = None,
        interval_sec: float = 60.0,
        retention_days: int = 7,
        consumer_id: str = "background-60s",
    ) -> None:
        self._session_factory = session_factory
        self._sonos_adapter = sonos_adapter
        self._wifi_adapter = wifi_adapter
        self._auto_heal_coordinator = auto_heal_coordinator
        self.interval_sec = interval_sec
        self.retention_days = retention_days
        self.consumer_id = consumer_id
        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._last_cycle_at: datetime | None = None
        self._total_cycles = 0
        self._last_error: str | None = None

    async def collect_cycle(self) -> dict[str, Any]:
        """Executes a single end-to-end collection, persistence, and pruning cycle."""
        executed_at = datetime.now(timezone.utc)
        try:
            sonos_snapshot = await self._sonos_adapter.collect_household_snapshot(
                consumer_id=self.consumer_id
            )
            wifi_snapshot = await self._wifi_adapter.collect_wifi_infrastructure()

            pruned_count = 0
            watchdog_alerts_count = 0
            async with self._session_factory() as session:
                repo = SqlAlchemyTopologyRepository(session)
                saved_snapshot = await repo.save_sonos_snapshot(sonos_snapshot)
                await repo.sync_wifi_infrastructure(wifi_snapshot)
                pruned_count = await repo.prune_expired_telemetry(
                    retention_days=self.retention_days,
                    consumer_id=self.consumer_id,
                )
                if self._auto_heal_coordinator is not None:
                    alerts = await self._auto_heal_coordinator.handle_snapshot(
                        saved_snapshot, repo=repo
                    )
                    watchdog_alerts_count = len(alerts)

            self._last_cycle_at = executed_at
            self._total_cycles += 1
            self._last_error = None

            return {
                "status": "ok",
                "batch_id": sonos_snapshot.batch_id,
                "total_players": len(sonos_snapshot.players),
                "pruned_count": pruned_count,
                "watchdog_alerts_count": watchdog_alerts_count,
                "executed_at": executed_at,
            }
        except Exception as exc:
            self._last_error = str(exc)
            logger.error("Telemetry collection cycle failed: %s", exc, exc_info=True)
            raise

    async def _run_loop(self) -> None:
        logger.info(
            "Starting 24/7 ScheduledTelemetryCollector (interval=%.1fs, retention=%dd)",
            self.interval_sec,
            self.retention_days,
        )
        while self._running:
            try:
                await self.collect_cycle()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning("Error during collector cycle: %s", e)

            try:
                await asyncio.sleep(self.interval_sec)
            except asyncio.CancelledError:
                break

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Stopped ScheduledTelemetryCollector")

    def status(self) -> DaemonStatusSchema:
        return DaemonStatusSchema(
            is_running=self._running,
            interval_sec=self.interval_sec,
            retention_days=self.retention_days,
            last_cycle_at=self._last_cycle_at,
            total_cycles=self._total_cycles,
            last_error=self._last_error,
        )
