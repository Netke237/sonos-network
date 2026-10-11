from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Body, Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Base, build_engine_and_sessionmaker
from app.modules.sonos_telemetry import (
    FakeSonosAdapter,
    HttpSonosAdapter,
    SonosTelemetryPort,
)
from app.repositories.topology_repository import SqlAlchemyTopologyRepository
from app.schemas.topology import (
    FloorCreate,
    FloorRead,
    FloorUpdate,
    GhostFlushRequest,
    GhostFlushResult,
    HouseOverviewDto,
    HouseholdSonosSnapshot,
    NetworkDeviceCreate,
    NetworkDeviceRead,
    NetworkDeviceUpdate,
    RoomCreate,
    RoomRead,
    RoomUpdate,
    SwitchPortCreate,
    SwitchPortRead,
    SwitchPortUpdate,
)
from app.seeds.initial_seed import seed_initial_data


def create_app(
    database_url: str | None = None,
    sonos_adapter: SonosTelemetryPort | None = None,
) -> FastAPI:
    engine, session_factory = build_engine_and_sessionmaker(database_url)
    default_adapter: SonosTelemetryPort = sonos_adapter or (
        HttpSonosAdapter()
        if os.getenv("SONOS_USE_LIVE_HTTP") == "1"
        else FakeSonosAdapter(probe_interval_sec=0.01)
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.engine = engine
        app.state.session_factory = session_factory
        app.state.sonos_adapter = default_adapter
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with session_factory() as session:
            await seed_initial_data(session)
        try:
            yield
        finally:
            await engine.dispose()

    app = FastAPI(
        title="Home Wi-Fi & Sonos Network Intelligence Platform",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.sonos_adapter = default_adapter

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

    @app.get("/api/health")
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/overview", response_model=HouseOverviewDto)
    async def get_overview(
        include_archived: bool = Query(False),
        repo: SqlAlchemyTopologyRepository = Depends(get_repo),
    ) -> HouseOverviewDto:
        return await repo.get_house_overview(include_archived=include_archived)


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

    return app


app = create_app()

