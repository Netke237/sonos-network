from __future__ import annotations

import io
import os
from pathlib import Path
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import qrcode
import qrcode.image.svg
from fastapi import (
    Body,
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Base, build_engine_and_sessionmaker
from app.modules.diagnostic_engine import (
    DiagnosticEngine,
    DiagnosticEnginePort,
    FakeNetworkProbeAdapter,
    HttpNetworkProbeAdapter,
    NetworkProbePort,
)
from app.modules.sonos_telemetry import (
    FakeSonosAdapter,
    HttpSonosAdapter,
    SonosTelemetryPort,
)
from app.modules.telemetry_daemon import ScheduledTelemetryCollector
from app.modules.telegram_alerts import (
    AlertChannelPort,
    TelegramAlertAdapter,
)
from app.modules.watchdog_engine import (
    AutoHealCoordinator,
    WatchdogEngine,
    WatchdogEnginePort,
    WatchdogStatusSchema,
)
from app.modules.wifi_omada import (
    FakeWiFiAdapter,
    OmadaAndAdbWiFiAdapter,
    WiFiTelemetryPort,
)
from app.repositories.topology_repository import SqlAlchemyTopologyRepository
from app.schemas.topology import (
    DaemonStatusSchema,
    FloorCreate,
    FloorRead,
    FloorUpdate,
    GhostFlushRequest,
    GhostFlushResult,
    HouseDiagnosticReportSchema,
    HouseOverviewDto,
    HouseholdSonosSnapshot,
    NetworkDeviceCreate,
    NetworkDeviceRead,
    NetworkDeviceUpdate,
    PingSweepResultSchema,
    RoomCreate,
    RoomDiagnosticSummarySchema,
    RoomHistoryResponseSchema,
    RoomRead,
    RoomUpdate,
    SurveyComparisonDeltaSchema,
    SwitchPortCreate,
    SwitchPortRead,
    SwitchPortUpdate,
    TopologyGraphResponse,
    WiFiInfraSnapshot,
    WiFiRoomSurveyCreate,
    WiFiRoomSurveySchema,
)
from app.seeds.initial_seed import seed_initial_data


def create_app(
    database_url: str | None = None,
    sonos_adapter: SonosTelemetryPort | None = None,
    wifi_adapter: WiFiTelemetryPort | None = None,
    probe_adapter: NetworkProbePort | None = None,
    diagnostic_engine: DiagnosticEnginePort | None = None,
    watchdog_engine: WatchdogEnginePort | None = None,
    alert_channel: AlertChannelPort | None = None,
    enable_daemon: bool = False,
) -> FastAPI:
    engine, session_factory = build_engine_and_sessionmaker(database_url)
    default_adapter: SonosTelemetryPort = sonos_adapter or (
        HttpSonosAdapter()
        if os.getenv("SONOS_USE_LIVE_HTTP") == "1"
        else FakeSonosAdapter(probe_interval_sec=0.01)
    )
    default_wifi_adapter: WiFiTelemetryPort = wifi_adapter or (
        OmadaAndAdbWiFiAdapter()
        if os.getenv("OMADA_USE_LIVE_HTTP") == "1"
        else FakeWiFiAdapter()
    )
    default_probe_adapter: NetworkProbePort = probe_adapter or (
        HttpNetworkProbeAdapter()
        if os.getenv("SONOS_USE_LIVE_HTTP") == "1"
        else FakeNetworkProbeAdapter()
    )
    default_diagnostic_engine: DiagnosticEnginePort = (
        diagnostic_engine or DiagnosticEngine()
    )
    default_watchdog_engine: WatchdogEnginePort = (
        watchdog_engine or WatchdogEngine()
    )
    default_alert_channel: AlertChannelPort = (
        alert_channel or TelegramAlertAdapter()
    )
    default_auto_heal_coordinator = AutoHealCoordinator(
        watchdog_engine=default_watchdog_engine,
        sonos_adapter=default_adapter,
        alert_channel=default_alert_channel,
    )
    default_daemon = ScheduledTelemetryCollector(
        session_factory=session_factory,
        sonos_adapter=default_adapter,
        wifi_adapter=default_wifi_adapter,
        auto_heal_coordinator=default_auto_heal_coordinator,
        interval_sec=float(os.getenv("BACKGROUND_POLL_INTERVAL_SEC", "60.0")),
        retention_days=int(os.getenv("TELEMETRY_RETENTION_DAYS", "365")),
        consumer_id="background-60s",
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.engine = engine
        app.state.session_factory = session_factory
        app.state.sonos_adapter = default_adapter
        app.state.wifi_adapter = default_wifi_adapter
        app.state.probe_adapter = default_probe_adapter
        app.state.diagnostic_engine = default_diagnostic_engine
        app.state.watchdog_engine = default_watchdog_engine
        app.state.alert_channel = default_alert_channel
        app.state.auto_heal_coordinator = default_auto_heal_coordinator
        app.state.telemetry_daemon = default_daemon
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with session_factory() as session:
            await seed_initial_data(session)
        daemon_enabled = (
            enable_daemon or os.getenv("ENABLE_TELEMETRY_DAEMON", "0") == "1"
        )
        if daemon_enabled:
            await default_daemon.start()
        try:
            yield
        finally:
            if hasattr(app.state, "telemetry_daemon"):
                await app.state.telemetry_daemon.stop()
            await engine.dispose()

    app = FastAPI(
        title="Home Wi-Fi & Sonos Network Intelligence Platform",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.sonos_adapter = default_adapter
    app.state.wifi_adapter = default_wifi_adapter
    app.state.probe_adapter = default_probe_adapter
    app.state.diagnostic_engine = default_diagnostic_engine
    app.state.watchdog_engine = default_watchdog_engine
    app.state.alert_channel = default_alert_channel
    app.state.auto_heal_coordinator = default_auto_heal_coordinator
    app.state.telemetry_daemon = default_daemon

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
        factory = request.app.state.session_factory
        async with factory() as session:
            yield session

    def get_repo(
        session: AsyncSession = Depends(get_session),
    ) -> SqlAlchemyTopologyRepository:
        return SqlAlchemyTopologyRepository(session)

    def get_sonos_adapter(request: Request) -> SonosTelemetryPort:
        return request.app.state.sonos_adapter

    def get_wifi_adapter(request: Request) -> WiFiTelemetryPort:
        return request.app.state.wifi_adapter

    def get_probe_adapter(request: Request) -> NetworkProbePort:
        return request.app.state.probe_adapter

    def get_diagnostic_engine(request: Request) -> DiagnosticEnginePort:
        return request.app.state.diagnostic_engine

    def get_watchdog_engine(request: Request) -> WatchdogEnginePort:
        return request.app.state.watchdog_engine

    def get_alert_channel(request: Request) -> AlertChannelPort:
        return request.app.state.alert_channel


    @app.get("/api/health")
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/overview", response_model=HouseOverviewDto)
    async def get_overview(
        include_archived: bool = Query(False),
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
        diag_engine: DiagnosticEnginePort = Depends(get_diagnostic_engine),
    ) -> HouseOverviewDto:
        return await repo.get_house_overview(
            include_archived=include_archived,
            diagnostic_engine=diag_engine,
        )

    @app.get("/api/topology", response_model=TopologyGraphResponse)
    async def get_topology_graph(
        layer: str = Query("ALL"),
        layer_filter: str | None = Query(None),
        floor_slug: str | None = Query(None),
        room_slug: str | None = Query(None),
        include_blocking: bool = Query(True),
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
    ) -> TopologyGraphResponse:
        effective_layer = layer_filter or layer
        return await repo.build_unified_graph(
            layer_filter=effective_layer,
            floor_slug=floor_slug,
            room_slug=room_slug,
            include_blocking=include_blocking,
        )


    # --- Floors CRUD ---
    @app.get("/api/floors", response_model=list[FloorRead])
    async def list_floors(
        include_archived: bool = Query(False),
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
    ) -> list[FloorRead]:
        floors = await repo.list_floors(include_archived=include_archived)
        return [FloorRead.model_validate(f) for f in floors]

    @app.post(
        "/api/floors",
        response_model=FloorRead,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_floor(
        payload: FloorCreate,
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
    ) -> FloorRead:
        floor = await repo.create_floor(payload)
        return FloorRead.model_validate(floor)

    @app.put("/api/floors/{floor_id}", response_model=FloorRead)
    async def update_floor(
        floor_id: str,
        payload: FloorUpdate,
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
    ) -> FloorRead:
        floor = await repo.update_floor(floor_id, payload)
        if not floor:
            raise HTTPException(status_code=404, detail="Floor not found")
        return FloorRead.model_validate(floor)

    @app.delete("/api/floors/{floor_id}", response_model=FloorRead)
    async def delete_floor(
        floor_id: str,
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
    ) -> FloorRead:
        floor = await repo.archive_floor(floor_id)
        if not floor:
            raise HTTPException(status_code=404, detail="Floor not found")
        return FloorRead.model_validate(floor)

    # --- Rooms CRUD ---
    @app.get("/api/rooms", response_model=list[RoomRead])
    async def list_rooms(
        include_archived: bool = Query(False),
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
    ) -> list[RoomRead]:
        rooms = await repo.list_rooms(include_archived=include_archived)
        return [RoomRead.model_validate(r) for r in rooms]

    @app.get("/api/rooms/{room_id}", response_model=RoomRead)
    async def get_room(
        room_id: str,
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
    ) -> RoomRead:
        room = await repo.get_room(room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        return RoomRead.model_validate(room)

    @app.post(
        "/api/rooms",
        response_model=RoomRead,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_room(
        payload: RoomCreate,
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
    ) -> RoomRead:
        room = await repo.create_room(payload)
        return RoomRead.model_validate(room)

    @app.put("/api/rooms/{room_id}", response_model=RoomRead)
    async def update_room(
        room_id: str,
        payload: RoomUpdate,
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
    ) -> RoomRead:
        room = await repo.update_room(room_id, payload)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        return RoomRead.model_validate(room)

    @app.delete("/api/rooms/{room_id}", response_model=RoomRead)
    async def delete_room(
        room_id: str,
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
    ) -> RoomRead:
        room = await repo.archive_room(room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        return RoomRead.model_validate(room)

    # --- SwitchPorts CRUD ---
    @app.get("/api/switch-ports", response_model=list[SwitchPortRead])
    async def list_switch_ports(
        include_archived: bool = Query(False),
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
    ) -> list[SwitchPortRead]:
        ports = await repo.list_switch_ports(include_archived=include_archived)
        return [SwitchPortRead.model_validate(p) for p in ports]

    @app.post(
        "/api/switch-ports",
        response_model=SwitchPortRead,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_switch_port(
        payload: SwitchPortCreate,
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
    ) -> SwitchPortRead:
        port = await repo.create_switch_port(payload)
        return SwitchPortRead.model_validate(port)

    @app.put("/api/switch-ports/{port_id}", response_model=SwitchPortRead)
    async def update_switch_port(
        port_id: str,
        payload: SwitchPortUpdate,
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
    ) -> SwitchPortRead:
        port = await repo.update_switch_port(port_id, payload)
        if not port:
            raise HTTPException(status_code=404, detail="SwitchPort not found")
        return SwitchPortRead.model_validate(port)

    @app.delete("/api/switch-ports/{port_id}", response_model=SwitchPortRead)
    async def delete_switch_port(
        port_id: str,
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
    ) -> SwitchPortRead:
        port = await repo.archive_switch_port(port_id)
        if not port:
            raise HTTPException(status_code=404, detail="SwitchPort not found")
        return SwitchPortRead.model_validate(port)

    # --- NetworkDevices CRUD ---
    @app.get("/api/devices", response_model=list[NetworkDeviceRead])
    async def list_devices(
        include_archived: bool = Query(False),
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
    ) -> list[NetworkDeviceRead]:
        devices = await repo.list_devices(include_archived=include_archived)
        return [NetworkDeviceRead.model_validate(d) for d in devices]

    @app.post(
        "/api/devices",
        response_model=NetworkDeviceRead,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_device(
        payload: NetworkDeviceCreate,
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
    ) -> NetworkDeviceRead:
        dev = await repo.create_device(payload)
        return NetworkDeviceRead.model_validate(dev)

    @app.put("/api/devices/{device_id}", response_model=NetworkDeviceRead)
    async def update_device(
        device_id: str,
        payload: NetworkDeviceUpdate,
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
    ) -> NetworkDeviceRead:
        dev = await repo.update_device(device_id, payload)
        if not dev:
            raise HTTPException(status_code=404, detail="NetworkDevice not found")
        return NetworkDeviceRead.model_validate(dev)

    @app.delete("/api/devices/{device_id}", response_model=NetworkDeviceRead)
    async def delete_device(
        device_id: str,
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
    ) -> NetworkDeviceRead:
        dev = await repo.archive_device(device_id)
        if not dev:
            raise HTTPException(status_code=404, detail="NetworkDevice not found")
        return NetworkDeviceRead.model_validate(dev)

    # --- Sonos Telemetry & Actions ---
    @app.get("/api/sonos/telemetry", response_model=HouseholdSonosSnapshot)
    async def get_sonos_telemetry(
        batch_id: str | None = Query(None),
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
        adapter: SonosTelemetryPort = Depends(get_sonos_adapter),
    ) -> HouseholdSonosSnapshot:
        snap = await repo.get_sonos_telemetry(batch_id=batch_id)
        if snap is not None:
            return snap
        if batch_id is not None:
            raise HTTPException(status_code=404, detail="Sonos telemetry batch not found")
        collected = await adapter.collect_household_snapshot(consumer_id="on-demand")
        return await repo.save_sonos_snapshot(collected)

    @app.post("/api/actions/poll-now", response_model=HouseholdSonosSnapshot)
    async def poll_sonos_now(
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
        adapter: SonosTelemetryPort = Depends(get_sonos_adapter),
    ) -> HouseholdSonosSnapshot:
        collected = await adapter.collect_household_snapshot(consumer_id="on-demand")
        return await repo.save_sonos_snapshot(collected)

    @app.post("/api/actions/flush-ghost-groups", response_model=GhostFlushResult)
    async def flush_ghost_groups_action(
        payload: GhostFlushRequest | None = Body(default=None),
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
        adapter: SonosTelemetryPort = Depends(get_sonos_adapter),
    ) -> GhostFlushResult:
        zone_ips = payload.zone_ips if payload else None
        result = await adapter.flush_ghost_groups(zone_ips=zone_ips)
        await repo.apply_ghost_flush(result)
        return result

    # --- Wi-Fi Infrastructure & Room BSSID Surveys ---
    @app.get("/api/wifi/infrastructure", response_model=WiFiInfraSnapshot)
    async def get_wifi_infrastructure(
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
        wifi_adapter: WiFiTelemetryPort = Depends(get_wifi_adapter),
    ) -> WiFiInfraSnapshot:
        infra = await wifi_adapter.collect_wifi_infrastructure()
        return await repo.sync_wifi_infrastructure(infra)

    @app.get(
        "/api/rooms/{room_slug}/surveys",
        response_model=list[WiFiRoomSurveySchema],
    )
    async def list_room_surveys(
        room_slug: str,
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
    ) -> list[WiFiRoomSurveySchema]:
        surveys = await repo.list_room_surveys(room_slug)
        if surveys is None:
            raise HTTPException(status_code=404, detail="Room not found")
        return surveys

    @app.post(
        "/api/rooms/{room_slug}/surveys",
        response_model=WiFiRoomSurveySchema,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_room_survey(
        room_slug: str,
        payload: WiFiRoomSurveyCreate = Body(default_factory=WiFiRoomSurveyCreate),
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
        wifi_adapter: WiFiTelemetryPort = Depends(get_wifi_adapter),
    ) -> WiFiRoomSurveySchema:
        survey = await repo.create_room_survey(room_slug, payload, wifi_adapter)
        if survey is None:
            raise HTTPException(status_code=404, detail="Room not found")
        return survey

    @app.get(
        "/api/rooms/{room_slug}/surveys/delta",
        response_model=SurveyComparisonDeltaSchema,
    )
    async def get_room_survey_delta(
        room_slug: str,
        baseline_slug: str | None = Query(None),
        target_slug: str | None = Query(None),
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
    ) -> SurveyComparisonDeltaSchema:
        delta = await repo.compute_survey_delta(
            room_ref=room_slug,
            baseline_slug=baseline_slug,
            target_slug=target_slug,
        )
        if delta is None:
            raise HTTPException(
                status_code=404,
                detail=f"Room '{room_slug}' or required surveys not found",
            )
        return delta

    @app.websocket("/api/ws/live-rf")
    async def ws_live_rf(
        websocket: WebSocket,
        room_slug: str = "all",
        interval_sec: float = 2.0,
        max_iterations: int | None = None,
    ):
        await websocket.accept()
        consumer_id = f"ws-{uuid.uuid4().hex[:8]}"
        sonos_adapter: SonosTelemetryPort = websocket.app.state.sonos_adapter
        try:
            async for samples in sonos_adapter.stream_room_rf_velocity(
                room_id=room_slug,
                interval_sec=interval_sec,
                consumer_id=consumer_id,
                max_iterations=max_iterations,
            ):
                payload = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "consumer_id": consumer_id,
                    "room_slug": room_slug,
                    "samples": [s.model_dump(mode="json") for s in samples],
                }
                await websocket.send_json(payload)
        except WebSocketDisconnect:
            pass
        except Exception:
            pass

    # --- Deterministic Diagnostics & Ping/Jitter Sweep ---
    @app.get("/api/diagnostics", response_model=HouseDiagnosticReportSchema)
    async def get_house_diagnostics(
        include_archived: bool = Query(False),
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
        diag_engine: DiagnosticEnginePort = Depends(get_diagnostic_engine),
    ) -> HouseDiagnosticReportSchema:
        return await repo.evaluate_house_diagnostics(
            diagnostic_engine=diag_engine,
            include_archived=include_archived,
        )

    @app.get(
        "/api/rooms/{room_slug}/diagnostics",
        response_model=RoomDiagnosticSummarySchema,
    )
    async def get_room_diagnostics(
        room_slug: str,
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
        diag_engine: DiagnosticEnginePort = Depends(get_diagnostic_engine),
    ) -> RoomDiagnosticSummarySchema:
        summary = await repo.evaluate_room_diagnostics(
            room_slug,
            diagnostic_engine=diag_engine,
        )
        if summary is None:
            raise HTTPException(status_code=404, detail="Room not found")
        return summary

    @app.post("/api/actions/ping-sweep", response_model=PingSweepResultSchema)
    async def run_ping_sweep_action(
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
        adapter: SonosTelemetryPort = Depends(get_sonos_adapter),
        probe_adapter: NetworkProbePort = Depends(get_probe_adapter),
    ) -> PingSweepResultSchema:
        snap = await repo.get_sonos_telemetry()
        if snap is None:
            collected = await adapter.collect_household_snapshot(consumer_id="on-demand")
            snap = await repo.save_sonos_snapshot(collected)
        result = await probe_adapter.run_ping_sweep(players=snap.players)
        await repo.apply_ping_sweep(result)
        return result

    # --- 24/7 Background Telemetry Daemon & Historical Trends ---
    @app.get(
        "/api/rooms/{room_slug}/history",
        response_model=RoomHistoryResponseSchema,
    )
    async def get_room_history(
        room_slug: str,
        range: str = Query("24h", pattern="^(1h|24h|7d|30d|90d|365d|1y)$"),
        granularity: str = Query("auto", pattern="^(auto|raw|weekly|monthly)$"),
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
    ) -> RoomHistoryResponseSchema:
        history = await repo.get_room_history(
            room_slug, time_range=range, granularity=granularity
        )
        if not history:
            raise HTTPException(
                status_code=404,
                detail=f"Room '{room_slug}' not found",
            )
        return history

    @app.get("/api/daemon/status", response_model=DaemonStatusSchema)
    async def get_daemon_status(request: Request) -> DaemonStatusSchema:
        daemon: ScheduledTelemetryCollector = request.app.state.telemetry_daemon
        return daemon.status()

    @app.post("/api/daemon/collect-now")
    async def trigger_daemon_collect(request: Request) -> dict[str, Any]:
        daemon: ScheduledTelemetryCollector = request.app.state.telemetry_daemon
        return await daemon.collect_cycle()

    @app.post("/api/daemon/toggle", response_model=DaemonStatusSchema)
    async def toggle_daemon(
        request: Request,
        enabled: bool = Query(True),
    ) -> DaemonStatusSchema:
        daemon: ScheduledTelemetryCollector = request.app.state.telemetry_daemon
        if enabled:
            await daemon.start()
        else:
            await daemon.stop()
        return daemon.status()

    # --- 24/7 Autonomous Watchdog & Telegram Alert Endpoints ---
    @app.get("/api/watchdog/status")
    async def get_watchdog_status(
        engine: WatchdogEnginePort = Depends(get_watchdog_engine),
        channel: AlertChannelPort = Depends(get_alert_channel),
    ) -> dict[str, Any]:
        status_dict = engine.get_status().model_dump()
        status_dict["telegram_configured"] = channel.is_configured()
        return status_dict

    @app.post("/api/watchdog/toggle-auto-heal")
    async def toggle_auto_heal(
        enabled: bool = Query(True),
        engine: WatchdogEnginePort = Depends(get_watchdog_engine),
    ) -> dict[str, Any]:
        engine.set_auto_heal(enabled)
        return {"auto_heal_enabled": engine.is_auto_heal_enabled()}

    @app.post("/api/watchdog/test-alert")
    async def test_watchdog_alert(
        channel: AlertChannelPort = Depends(get_alert_channel),
    ) -> dict[str, Any]:
        delivered = await channel.send_raw_message(
            "🔔 *Test Alert from Sonos Network Watchdog*\n\nAutonomous alerting pipeline is operational."
        )
        return {"status": "ok", "delivered": delivered}

    # --- Mini PC Companion Distribution & QR Code Endpoints ---
    @app.get("/api/companion/qr")
    async def get_companion_qr(request: Request, url: str | None = None) -> Response:
        if not url:
            base_str = str(request.base_url).rstrip("/")
            if request.base_url.hostname in ("127.0.0.1", "localhost", None):
                base_str = os.getenv("MINI_PC_HOST", "http://192.168.55.60:8001").rstrip("/")
            target_url = f"{base_str}/api/companion/apk"
        else:
            target_url = url
        factory = qrcode.image.svg.SvgImage
        img = qrcode.make(target_url, image_factory=factory)
        svg_stream = io.BytesIO()
        img.save(svg_stream)
        return Response(content=svg_stream.getvalue(), media_type="image/svg+xml")

    @app.get("/api/companion/apk")
    async def download_companion_apk() -> Response:
        apk_candidates = [
            Path("backend/app/static/apk/sonos-network-companion.apk"),
            Path("app/static/apk/sonos-network-companion.apk"),
            Path("backend/app/static/apk/app-release.apk"),
            Path("app/static/apk/app-release.apk"),
            Path("backend/app/static/apk/app-debug.apk"),
            Path("android/app/build/outputs/apk/release/app-release.apk"),
            Path("android/app/build/outputs/apk/debug/app-debug.apk"),
            Path("dist/sonos-network-companion.apk"),
        ]
        for candidate in apk_candidates:
            if candidate.exists() and candidate.stat().st_size > 0:
                return FileResponse(
                    str(candidate),
                    media_type="application/vnd.android.package-archive",
                    filename="sonos-network-companion.apk",
                )

        # Mock / fallback APK payload for test and initial development environments
        mock_apk = b"PK\x03\x04\x14\x00\x00\x00\x08\x00SonosNetworkCompanionApkMock"
        return Response(
            content=mock_apk,
            media_type="application/vnd.android.package-archive",
            headers={"Content-Disposition": 'attachment; filename="sonos-network-companion.apk"'},
        )

    @app.get("/install", response_class=HTMLResponse)
    async def install_companion_page(request: Request) -> str:
        base_url = str(request.base_url).rstrip("/")
        if request.base_url.hostname in ("127.0.0.1", "localhost", None):
            base_url = os.getenv("MINI_PC_HOST", "http://192.168.55.60:8001").rstrip("/")
        apk_url = f"{base_url}/api/companion/apk"
        qr_url = f"{base_url}/api/companion/qr"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Sonos Network Companion Installer</title>
  <style>
    body {{
      margin: 0;
      padding: 24px;
      background-color: #0b1329;
      color: #f8fafc;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 90vh;
    }}
    .card {{
      background-color: #1e293b;
      border: 1px solid #334155;
      border-radius: 16px;
      padding: 32px 24px;
      max-width: 440px;
      width: 100%;
      text-align: center;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
    }}
    h1 {{
      font-size: 1.4rem;
      margin: 0 0 8px;
      color: #38bdf8;
    }}
    p {{
      color: #94a3b8;
      font-size: 0.9rem;
      margin: 0 0 20px;
      line-height: 1.4;
    }}
    .qr-container {{
      background: #ffffff;
      padding: 16px;
      border-radius: 12px;
      display: inline-block;
      margin-bottom: 24px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }}
    .qr-container img {{
      display: block;
      width: 220px;
      height: 220px;
    }}
    .btn {{
      display: block;
      background-color: #0284c7;
      color: #ffffff;
      text-decoration: none;
      font-weight: 700;
      font-size: 1rem;
      padding: 14px 20px;
      border-radius: 8px;
      transition: background-color 0.2s;
      margin-bottom: 20px;
    }}
    .btn:hover {{
      background-color: #0369a1;
    }}
    .steps {{
      text-align: left;
      background-color: #0f172a;
      border: 1px solid #334155;
      border-radius: 8px;
      padding: 16px 20px;
      font-size: 0.85rem;
      color: #cbd5e1;
    }}
    .steps ol {{
      margin: 0;
      padding-left: 20px;
    }}
    .steps li {{
      margin-bottom: 8px;
    }}
    .steps li:last-child {{
      margin-bottom: 0;
    }}
    .badge {{
      display: inline-block;
      background-color: #064e3b;
      color: #6ee7b7;
      border: 1px solid #10b981;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 600;
      margin-bottom: 16px;
    }}
  </style>
</head>
<body>
  <div class="card">
    <div class="badge">Local Network & WireGuard Ready</div>
    <h1>Sonos Network Companion</h1>
    <p>Scan the QR code with your Android phone or tap the download button below.</p>
    
    <div class="qr-container">
      <img src="{qr_url}" alt="Scan to install APK"/>
    </div>

    <a href="{apk_url}" class="btn">⬇️ Download Companion APK</a>

    <div class="steps">
      <strong>Installation Instructions:</strong>
      <ol>
        <li>Download the APK file onto your Android device.</li>
        <li>Tap the downloaded file and select <em>Install</em> (allow <em>Unknown Sources</em> if prompted).</li>
        <li>Connect to home Wi-Fi (<code>WuTangLan-Family</code>) or connect your <strong>Firewalla WireGuard VPN</strong>.</li>
        <li>Launch the app to audit room Wi-Fi and monitor live Sonos health.</li>
      </ol>
    </div>
  </div>
</body>
</html>
"""

    return app




app = create_app()


