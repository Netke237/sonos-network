from __future__ import annotations

import re
import uuid
from typing import Protocol
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import (
    ConnectionMode,
    DeviceRole,
    Floor,
    NetworkDevice,
    Room,
    SonosMeshLink,
    SonosTelemetrySnapshot,
    SwitchPort,
)
from app.modules.sonos_telemetry import EXPECTED_STP_ROOT
from app.schemas.topology import (
    FloorCreate,
    FloorMatrixItemDto,
    FloorRead,
    FloorUpdate,
    GhostFlushResult,
    HouseOverviewDto,
    HouseholdSonosSnapshot,
    NetworkDeviceCreate,
    NetworkDeviceRead,
    NetworkDeviceUpdate,
    PlayerTelemetryDto,
    RoomCreate,
    RoomMatrixItemDto,
    RoomRead,
    RoomUpdate,
    SonosMeshLinkDto,
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

    async def save_sonos_snapshot(
        self, snapshot: HouseholdSonosSnapshot
    ) -> HouseholdSonosSnapshot:
        devices = await self.list_devices(include_archived=True)
        rooms = await self.list_rooms(include_archived=True)
        devs_by_uuid = {
            d.rincon_uuid: d for d in devices if d.rincon_uuid is not None
        }
        rooms_by_id = {r.id: r for r in rooms}

        for p in snapshot.players:
            dev = devs_by_uuid.get(p.rincon_uuid)
            room_id = dev.room_id if dev else p.room_id
            room = rooms_by_id.get(room_id) if room_id else None
            p.device_id = dev.id if dev else None
            p.room_id = room_id
            p.room_name = room.name if room else p.room_name

            if dev and p.ip_address and not dev.ip_address:
                dev.ip_address = p.ip_address

            row = SonosTelemetrySnapshot(
                batch_id=snapshot.batch_id,
                captured_at=snapshot.captured_at,
                consumer_id=snapshot.consumer_id,
                device_id=dev.id if dev else None,
                room_id=room_id,
                rincon_uuid=p.rincon_uuid,
                zone_name=p.zone_name,
                ip_address=p.ip_address,
                base_mac=p.base_mac,
                sonosnet_bssid=p.sonosnet_bssid,
                is_reachable=p.is_reachable,
                connection_mode=(
                    p.connection_mode.value
                    if hasattr(p.connection_mode, "value")
                    else str(p.connection_mode)
                ),
                ieee_channel=p.ieee_channel,
                ofdm_ani_level=p.ofdm_ani_level,
                noise_floor_dbm=p.noise_floor_dbm,
                phy_error_total=p.phy_error_total,
                phy_error_rate=p.phy_error_rate,
                designated_root=p.designated_root,
                stp_root_port=p.stp_root_port,
                stp_path_cost=p.stp_path_cost,
                group_id=p.group_id,
                coordinator_uuid=p.coordinator_uuid,
                has_vanished_devices=p.has_vanished_devices,
                is_ghost_group=p.is_ghost_group,
                master_volume=p.master_volume,
                ping_rtt_ms=p.ping_rtt_ms,
                bonded_parent_uuid=p.bonded_parent_uuid,
            )
            self._session.add(row)

        for link in snapshot.mesh_links:
            self._session.add(
                SonosMeshLink(
                    batch_id=snapshot.batch_id,
                    captured_at=snapshot.captured_at,
                    source_rincon_uuid=link.source_rincon_uuid,
                    target_rincon_uuid=link.target_rincon_uuid,
                    source_bssid=link.source_bssid,
                    target_bssid=link.target_bssid,
                    channel=link.channel,
                    from_db=link.from_db,
                    to_db=link.to_db,
                    stp_state=link.stp_state,
                )
            )

        await self._session.commit()
        return snapshot

    async def get_sonos_telemetry(
        self, batch_id: str | None = None
    ) -> HouseholdSonosSnapshot | None:
        if batch_id is None:
            latest_stmt = (
                select(SonosTelemetrySnapshot.batch_id)
                .order_by(SonosTelemetrySnapshot.captured_at.desc())
                .limit(1)
            )
            latest_res = await self._session.execute(latest_stmt)
            batch_id = latest_res.scalar_one_or_none()
            if not batch_id:
                return None

        snaps_stmt = (
            select(SonosTelemetrySnapshot)
            .where(SonosTelemetrySnapshot.batch_id == batch_id)
            .order_by(SonosTelemetrySnapshot.zone_name.asc())
        )
        snaps_res = await self._session.execute(snaps_stmt)
        rows = list(snaps_res.scalars().all())
        if not rows:
            return None

        links_stmt = select(SonosMeshLink).where(SonosMeshLink.batch_id == batch_id)
        links_res = await self._session.execute(links_stmt)
        link_rows = list(links_res.scalars().all())

        rooms = await self.list_rooms(include_archived=True)
        rooms_by_id = {r.id: r.name for r in rooms}
        zone_by_uuid = {r.rincon_uuid: r.zone_name for r in rows}

        players: list[PlayerTelemetryDto] = []
        ghost_zones: list[str] = []
        for r in rows:
            if r.is_ghost_group:
                ghost_zones.append(r.zone_name)
            players.append(
                PlayerTelemetryDto(
                    rincon_uuid=r.rincon_uuid,
                    zone_name=r.zone_name,
                    device_id=r.device_id,
                    room_id=r.room_id,
                    room_name=rooms_by_id.get(r.room_id) if r.room_id else None,
                    ip_address=r.ip_address,
                    base_mac=r.base_mac,
                    sonosnet_bssid=r.sonosnet_bssid,
                    is_reachable=r.is_reachable,
                    connection_mode=ConnectionMode(r.connection_mode),
                    ieee_channel=r.ieee_channel,
                    ofdm_ani_level=r.ofdm_ani_level,
                    noise_floor_dbm=r.noise_floor_dbm,
                    phy_error_total=r.phy_error_total,
                    phy_error_rate=r.phy_error_rate,
                    designated_root=r.designated_root,
                    stp_root_port=r.stp_root_port,
                    stp_path_cost=r.stp_path_cost,
                    group_id=r.group_id,
                    coordinator_uuid=r.coordinator_uuid,
                    has_vanished_devices=r.has_vanished_devices,
                    is_ghost_group=r.is_ghost_group,
                    master_volume=r.master_volume,
                    ping_rtt_ms=r.ping_rtt_ms,
                    bonded_parent_uuid=r.bonded_parent_uuid,
                )
            )

        mesh_links: list[SonosMeshLinkDto] = [
            SonosMeshLinkDto(
                source_rincon_uuid=l.source_rincon_uuid,
                target_rincon_uuid=l.target_rincon_uuid,
                source_zone_name=zone_by_uuid.get(l.source_rincon_uuid),
                target_zone_name=zone_by_uuid.get(l.target_rincon_uuid),
                source_bssid=l.source_bssid,
                target_bssid=l.target_bssid,
                channel=l.channel,
                from_db=l.from_db,
                to_db=l.to_db,
                stp_state=l.stp_state,
            )
            for l in link_rows
        ]

        first = rows[0]
        root_row = next(
            (r for r in rows if r.stp_path_cost == 0 and r.designated_root),
            first,
        )
        root_id = root_row.designated_root or EXPECTED_STP_ROOT
        if root_id == EXPECTED_STP_ROOT:
            root_label = f"{root_id} (Wohnzimmer_Bookshelf 192.168.10.230)"
        elif root_id == "9000.5caafd595eea":
            root_label = f"{root_id} (Keller 192.168.10.217 - Historical Basement Root)"
        else:
            root_label = f"{root_id} ({root_row.zone_name})"

        return HouseholdSonosSnapshot(
            batch_id=batch_id,
            captured_at=first.captured_at,
            consumer_id=first.consumer_id,
            designated_stp_root=root_label,
            is_root_healthy=(root_id == EXPECTED_STP_ROOT),
            total_players=len(players),
            reachable_players=sum(1 for p in players if p.is_reachable),
            ghost_group_count=len(ghost_zones),
            has_ghost_groups=len(ghost_zones) > 0,
            ghost_group_zones=ghost_zones,
            players=players,
            mesh_links=mesh_links,
        )

    async def apply_ghost_flush(self, flush_result: GhostFlushResult) -> None:
        latest_stmt = (
            select(SonosTelemetrySnapshot.batch_id)
            .order_by(SonosTelemetrySnapshot.captured_at.desc())
            .limit(1)
        )
        latest_res = await self._session.execute(latest_stmt)
        batch_id = latest_res.scalar_one_or_none()
        if not batch_id:
            return

        new_gid_by_uuid = {
            r.rincon_uuid: r.new_group_id
            for r in flush_result.results
            if r.status == "SANITIZED"
        }
        snaps_stmt = select(SonosTelemetrySnapshot).where(
            SonosTelemetrySnapshot.batch_id == batch_id
        )
        snaps_res = await self._session.execute(snaps_stmt)
        for row in snaps_res.scalars().all():
            if row.rincon_uuid in new_gid_by_uuid:
                row.group_id = new_gid_by_uuid[row.rincon_uuid]
                row.coordinator_uuid = row.bonded_parent_uuid or row.rincon_uuid
                row.has_vanished_devices = False
                row.is_ghost_group = False
            elif row.is_ghost_group:
                coord = row.bonded_parent_uuid or row.rincon_uuid
                row.group_id = f"{coord}:1"
                row.coordinator_uuid = coord
                row.has_vanished_devices = False
                row.is_ghost_group = False
        await self._session.commit()

    async def get_house_overview(
        self, include_archived: bool = False
    ) -> HouseOverviewDto:
        floors = await self.list_floors(include_archived=include_archived)
        rooms = await self.list_rooms(include_archived=include_archived)
        devices = await self.list_devices(include_archived=include_archived)
        ports = await self.list_switch_ports(include_archived=include_archived)
        latest_sonos = await self.get_sonos_telemetry()

        telem_by_uuid: dict[str, PlayerTelemetryDto] = {}
        if latest_sonos:
            telem_by_uuid = {p.rincon_uuid: p for p in latest_sonos.players}

        devices_by_room: dict[str | None, list[NetworkDeviceRead]] = {}
        for d in devices:
            dev_dto = NetworkDeviceRead.model_validate(d)
            if d.rincon_uuid and d.rincon_uuid in telem_by_uuid:
                t = telem_by_uuid[d.rincon_uuid]
                dev_dto.ofdm_ani_level = t.ofdm_ani_level
                dev_dto.noise_floor_dbm = t.noise_floor_dbm
                dev_dto.phy_error_total = t.phy_error_total
                dev_dto.phy_error_rate = t.phy_error_rate
                dev_dto.designated_root = t.designated_root
                dev_dto.stp_path_cost = t.stp_path_cost
                dev_dto.group_id = t.group_id
                dev_dto.coordinator_uuid = t.coordinator_uuid
                dev_dto.is_ghost_group = t.is_ghost_group
                dev_dto.master_volume = t.master_volume
                dev_dto.ping_rtt_ms = t.ping_rtt_ms
                dev_dto.ieee_channel = t.ieee_channel
                dev_dto.bonded_parent_uuid = t.bonded_parent_uuid
                if t.ip_address and not dev_dto.ip_address:
                    dev_dto.ip_address = t.ip_address
            devices_by_room.setdefault(d.room_id, []).append(dev_dto)

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
            designated_stp_root=(
                latest_sonos.designated_stp_root
                if latest_sonos
                else "9000.542a1b63fe6e (Wohnzimmer_Bookshelf 192.168.10.230)"
            ),
            ghost_group_count=latest_sonos.ghost_group_count if latest_sonos else 0,
            has_ghost_groups=latest_sonos.has_ghost_groups if latest_sonos else False,
            ghost_group_zones=latest_sonos.ghost_group_zones if latest_sonos else [],
            latest_sonos_batch_id=latest_sonos.batch_id if latest_sonos else None,
            latest_sonos_captured_at=latest_sonos.captured_at if latest_sonos else None,
            floors=floor_dtos,
        )

