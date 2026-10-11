from __future__ import annotations

import re
import uuid
from typing import Protocol
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import (
    DeviceRole,
    Floor,
    NetworkDevice,
    Room,
    SwitchPort,
)
from app.schemas.topology import (
    FloorCreate,
    FloorMatrixItemDto,
    FloorRead,
    FloorUpdate,
    HouseOverviewDto,
    NetworkDeviceCreate,
    NetworkDeviceRead,
    NetworkDeviceUpdate,
    RoomCreate,
    RoomMatrixItemDto,
    RoomRead,
    RoomUpdate,
    SwitchPortCreate,
    SwitchPortRead,
    SwitchPortUpdate,
)


def _slugify(value: str) -> str:
    s = value.lower()
    s = (
        s.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or f"item-{uuid.uuid4().hex[:8]}"


class TopologyRepositoryPort(Protocol):
    async def list_floors(self, include_archived: bool = False) -> list[Floor]: ...
    async def create_floor(self, data: FloorCreate) -> Floor: ...
    async def update_floor(self, floor_id: str, data: FloorUpdate) -> Floor | None: ...
    async def archive_floor(self, floor_id: str) -> Floor | None: ...

    async def list_rooms(self, include_archived: bool = False) -> list[Room]: ...
    async def create_room(self, data: RoomCreate) -> Room: ...
    async def update_room(self, room_id: str, data: RoomUpdate) -> Room | None: ...
    async def archive_room(self, room_id: str) -> Room | None: ...

    async def list_switch_ports(self, include_archived: bool = False) -> list[SwitchPort]: ...
    async def create_switch_port(self, data: SwitchPortCreate) -> SwitchPort: ...
    async def update_switch_port(self, port_id: str, data: SwitchPortUpdate) -> SwitchPort | None: ...
    async def archive_switch_port(self, port_id: str) -> SwitchPort | None: ...

    async def list_devices(self, include_archived: bool = False) -> list[NetworkDevice]: ...
    async def create_device(self, data: NetworkDeviceCreate) -> NetworkDevice: ...
    async def update_device(self, device_id: str, data: NetworkDeviceUpdate) -> NetworkDevice | None: ...
    async def archive_device(self, device_id: str) -> NetworkDevice | None: ...

    async def get_house_overview(self, include_archived: bool = False) -> HouseOverviewDto: ...


class SqlAlchemyTopologyRepository:
    """Deep repository module managing Floor, Room, SwitchPort, and NetworkDevice inventory."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_floors(self, include_archived: bool = False) -> list[Floor]:
        stmt = select(Floor).order_by(Floor.level_order.asc(), Floor.name.asc())
        if not include_archived:
            stmt = stmt.where(Floor.is_archived.is_(False))
        res = await self._session.execute(stmt)
        return list(res.scalars().all())

    async def get_floor(self, floor_id: str) -> Floor | None:
        res = await self._session.execute(select(Floor).where(Floor.id == floor_id))
        return res.scalar_one_or_none()

    async def create_floor(self, data: FloorCreate) -> Floor:
        slug = data.slug or _slugify(data.name)
        floor = Floor(
            slug=slug,
            name=data.name,
            level_order=data.level_order,
            is_archived=False,
        )
        self._session.add(floor)
        await self._session.commit()
        await self._session.refresh(floor)
        return floor

    async def update_floor(self, floor_id: str, data: FloorUpdate) -> Floor | None:
        floor = await self.get_floor(floor_id)
        if not floor:
            return None
        payload = data.model_dump(exclude_unset=True)
        for k, v in payload.items():
            setattr(floor, k, v)
        await self._session.commit()
        await self._session.refresh(floor)
        return floor

    async def archive_floor(self, floor_id: str) -> Floor | None:
        floor = await self.get_floor(floor_id)
        if not floor:
            return None
        floor.is_archived = True
        await self._session.commit()
        await self._session.refresh(floor)
        return floor

    async def list_rooms(self, include_archived: bool = False) -> list[Room]:
        stmt = select(Room).order_by(Room.pos_y.desc(), Room.pos_x.asc(), Room.name.asc())
        if not include_archived:
            stmt = stmt.where(Room.is_archived.is_(False))
        res = await self._session.execute(stmt)
        return list(res.scalars().all())

    async def get_room(self, room_id: str) -> Room | None:
        res = await self._session.execute(select(Room).where(Room.id == room_id))
        return res.scalar_one_or_none()

    async def create_room(self, data: RoomCreate) -> Room:
        slug = data.slug or _slugify(data.name)
        room = Room(
            slug=slug,
            name=data.name,
            floor_id=data.floor_id,
            pos_x=data.pos_x,
            pos_y=data.pos_y,
            health_grade=data.health_grade.value,
            best_5ghz_rssi_dbm=data.best_5ghz_rssi_dbm,
            best_24ghz_rssi_dbm=data.best_24ghz_rssi_dbm,
            description=data.description,
            is_archived=False,
        )
        self._session.add(room)
        await self._session.commit()
        await self._session.refresh(room)
        return room

    async def update_room(self, room_id: str, data: RoomUpdate) -> Room | None:
        room = await self.get_room(room_id)
        if not room:
            return None
        payload = data.model_dump(exclude_unset=True)
        for k, v in payload.items():
            if hasattr(v, "value"):
                v = v.value
            setattr(room, k, v)
        await self._session.commit()
        await self._session.refresh(room)
        return room

    async def archive_room(self, room_id: str) -> Room | None:
        room = await self.get_room(room_id)
        if not room:
            return None
        room.is_archived = True
        await self._session.commit()
        await self._session.refresh(room)
        return room

    async def list_switch_ports(self, include_archived: bool = False) -> list[SwitchPort]:
        stmt = select(SwitchPort).order_by(SwitchPort.port_number.asc())
        if not include_archived:
            stmt = stmt.where(SwitchPort.is_archived.is_(False))
        res = await self._session.execute(stmt)
        return list(res.scalars().all())

    async def get_switch_port(self, port_id: str) -> SwitchPort | None:
        res = await self._session.execute(select(SwitchPort).where(SwitchPort.id == port_id))
        return res.scalar_one_or_none()

    async def create_switch_port(self, data: SwitchPortCreate) -> SwitchPort:
        port = SwitchPort(
            port_number=data.port_number,
            switch_name=data.switch_name,
            switch_ip=data.switch_ip,
            pvid=data.pvid,
            untagged_vlans=data.untagged_vlans,
            tagged_vlans=data.tagged_vlans,
            bpdu_policy=data.bpdu_policy,
            loop_detection_disabled=data.loop_detection_disabled,
            patched_room_id=data.patched_room_id,
            connected_device_label=data.connected_device_label,
            is_archived=False,
        )
        self._session.add(port)
        await self._session.commit()
        await self._session.refresh(port)
        return port

    async def update_switch_port(
        self, port_id: str, data: SwitchPortUpdate
    ) -> SwitchPort | None:
        port = await self.get_switch_port(port_id)
        if not port:
            return None
        payload = data.model_dump(exclude_unset=True)
        for k, v in payload.items():
            setattr(port, k, v)
        await self._session.commit()
        await self._session.refresh(port)
        return port

    async def archive_switch_port(self, port_id: str) -> SwitchPort | None:
        port = await self.get_switch_port(port_id)
        if not port:
            return None
        port.is_archived = True
        await self._session.commit()
        await self._session.refresh(port)
        return port

    async def list_devices(self, include_archived: bool = False) -> list[NetworkDevice]:
        stmt = select(NetworkDevice).order_by(NetworkDevice.name.asc())
        if not include_archived:
            stmt = stmt.where(NetworkDevice.is_archived.is_(False))
        res = await self._session.execute(stmt)
        return list(res.scalars().all())

    async def get_device(self, device_id: str) -> NetworkDevice | None:
        res = await self._session.execute(
            select(NetworkDevice).where(NetworkDevice.id == device_id)
        )
        return res.scalar_one_or_none()

    async def create_device(self, data: NetworkDeviceCreate) -> NetworkDevice:
        slug = data.slug or _slugify(f"{data.device_role.value}-{data.name}")
        dev = NetworkDevice(
            slug=slug,
            name=data.name,
            device_role=data.device_role.value,
            model_name=data.model_name,
            ip_address=data.ip_address,
            base_mac=data.base_mac,
            sonosnet_bssid=data.sonosnet_bssid,
            rincon_uuid=data.rincon_uuid,
            connection_mode=data.connection_mode.value if data.connection_mode else None,
            health_grade=data.health_grade.value,
            ofdm_ani_level=data.ofdm_ani_level,
            room_id=data.room_id,
            switch_port_id=data.switch_port_id,
            notes=data.notes,
            is_archived=data.is_archived,
        )
        self._session.add(dev)
        await self._session.commit()
        await self._session.refresh(dev)
        return dev

    async def update_device(
        self, device_id: str, data: NetworkDeviceUpdate
    ) -> NetworkDevice | None:
        dev = await self.get_device(device_id)
        if not dev:
            return None
        payload = data.model_dump(exclude_unset=True)
        for k, v in payload.items():
            if hasattr(v, "value"):
                v = v.value
            setattr(dev, k, v)
        await self._session.commit()
        await self._session.refresh(dev)
        return dev

    async def archive_device(self, device_id: str) -> NetworkDevice | None:
        dev = await self.get_device(device_id)
        if not dev:
            return None
        dev.is_archived = True
        await self._session.commit()
        await self._session.refresh(dev)
        return dev

    async def get_house_overview(
        self, include_archived: bool = False
    ) -> HouseOverviewDto:
        floors = await self.list_floors(include_archived=include_archived)
        rooms = await self.list_rooms(include_archived=include_archived)
        devices = await self.list_devices(include_archived=include_archived)
        ports = await self.list_switch_ports(include_archived=include_archived)

        devices_by_room: dict[str | None, list[NetworkDeviceRead]] = {}
        for d in devices:
            devices_by_room.setdefault(d.room_id, []).append(
                NetworkDeviceRead.model_validate(d)
            )

        ports_by_room: dict[str | None, list[SwitchPortRead]] = {}
        for p in ports:
            ports_by_room.setdefault(p.patched_room_id, []).append(
                SwitchPortRead.model_validate(p)
            )

        rooms_by_floor: dict[str, list[RoomMatrixItemDto]] = {}
        for r in rooms:
            room_dto = RoomMatrixItemDto(
                **RoomRead.model_validate(r).model_dump(),
                devices=devices_by_room.get(r.id, []),
                switch_ports=ports_by_room.get(r.id, []),
            )
            rooms_by_floor.setdefault(r.floor_id, []).append(room_dto)

        floor_dtos: list[FloorMatrixItemDto] = []
        for f in floors:
            floor_dtos.append(
                FloorMatrixItemDto(
                    **FloorRead.model_validate(f).model_dump(),
                    rooms=rooms_by_floor.get(f.id, []),
                )
            )

        sonos_count = sum(
            1 for d in devices if d.device_role == DeviceRole.SONOS_PLAYER.value
        )
        ap_count = sum(
            1 for d in devices if d.device_role == DeviceRole.WIFI_AP.value
        )

        return HouseOverviewDto(
            total_floors=len(floors),
            total_rooms=len(rooms),
            total_sonos_players=sonos_count,
            total_wifi_aps=ap_count,
            total_switch_ports=len(ports),
            designated_stp_root="9000.542a1b63fe6e (Wohnzimmer_Bookshelf 192.168.10.230)",
            floors=floor_dtos,
        )
