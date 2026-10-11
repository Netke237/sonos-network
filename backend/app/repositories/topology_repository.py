from __future__ import annotations

import re
import uuid
from typing import Protocol
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import (
    AccessPointRadio,
    BssidReading,
    ConnectionMode,
    DeviceRole,
    Floor,
    NetworkDevice,
    Room,
    SonosMeshLink,
    SonosTelemetrySnapshot,
    SwitchPort,
    WiFiRoomSurvey,
)
from app.modules.diagnostic_engine import DiagnosticEngine, DiagnosticEnginePort
from app.modules.sonos_telemetry import EXPECTED_STP_ROOT
from app.modules.topology_graph import synthesize_unified_topology_graph
from app.modules.wifi_omada import WiFiTelemetryPort, build_wifi_room_survey
from app.schemas.topology import (
    BssidReadingSchema,
    FloorCreate,
    FloorMatrixItemDto,
    FloorRead,
    FloorUpdate,
    GhostFlushResult,
    HouseDiagnosticReportSchema,
    HouseOverviewDto,
    HouseholdSonosSnapshot,
    NetworkDeviceCreate,
    NetworkDeviceRead,
    NetworkDeviceUpdate,
    PingSweepResultSchema,
    PlayerTelemetryDto,
    RoomCreate,
    RoomDiagnosticSummarySchema,
    RoomMatrixItemDto,
    RoomRead,
    RoomUpdate,
    SonosMeshLinkDto,
    SwitchPortCreate,
    SwitchPortRead,
    SwitchPortUpdate,
    TopologyGraphResponse,
    WiFiInfraSnapshot,
    WiFiRoomSurveyCreate,
    WiFiRoomSurveySchema,
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
    async def build_unified_graph(
        self,
        layer_filter: str = "ALL",
        floor_slug: str | None = None,
        room_slug: str | None = None,
        include_blocking: bool = True,
    ) -> TopologyGraphResponse: ...


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

    async def get_room_by_slug_or_id(self, room_ref: str) -> Room | None:
        res = await self._session.execute(
            select(Room).where((Room.slug == room_ref) | (Room.id == room_ref))
        )
        return res.scalar_one_or_none()

    async def sync_wifi_infrastructure(
        self, infra: WiFiInfraSnapshot
    ) -> WiFiInfraSnapshot:
        existing_res = await self._session.execute(select(AccessPointRadio))
        by_key = {r.radio_key: r for r in existing_res.scalars().all()}
        for r in infra.radios:
            row = by_key.get(r.radio_key)
            if row is None:
                row = AccessPointRadio(
                    radio_key=r.radio_key,
                    ap_device_slug=r.ap_device_slug,
                    ap_name=r.ap_name,
                    room_slug=r.room_slug,
                    band=r.band,
                    base_mac=r.base_mac,
                    bssid_suffix=r.bssid_suffix,
                    derived_bssids_csv=",".join(r.derived_bssids),
                    channel=r.channel,
                    center_channel=r.center_channel,
                    width_mhz=r.width_mhz,
                    tx_power_dbm=r.tx_power_dbm,
                    airtime_utilization_pct=r.airtime_utilization_pct,
                    is_non_dfs=r.is_non_dfs,
                    status=r.status,
                )
                self._session.add(row)
            else:
                row.channel = r.channel
                row.center_channel = r.center_channel
                row.width_mhz = r.width_mhz
                row.tx_power_dbm = r.tx_power_dbm
                row.airtime_utilization_pct = r.airtime_utilization_pct
                row.is_non_dfs = r.is_non_dfs
                row.status = r.status
        await self._session.commit()
        return infra

    async def list_room_surveys(self, room_ref: str) -> list[WiFiRoomSurveySchema] | None:
        room = await self.get_room_by_slug_or_id(room_ref)
        if not room:
            return None

        surveys_res = await self._session.execute(
            select(WiFiRoomSurvey)
            .where(WiFiRoomSurvey.room_id == room.id)
            .order_by(WiFiRoomSurvey.captured_at.desc())
        )
        surveys = list(surveys_res.scalars().all())
        if not surveys:
            return []

        survey_ids = [s.id for s in surveys]
        readings_res = await self._session.execute(
            select(BssidReading).where(BssidReading.survey_id.in_(survey_ids))
        )
        readings_by_survey: dict[str, list[BssidReadingSchema]] = {}
        for br in readings_res.scalars().all():
            readings_by_survey.setdefault(br.survey_id, []).append(
                BssidReadingSchema(
                    id=br.id,
                    bssid=br.bssid,
                    ssid=br.ssid,
                    band=br.band,
                    channel=br.channel,
                    center_channel=br.center_channel,
                    width_mhz=br.width_mhz,
                    rssi_dbm=br.rssi_dbm,
                    classification=br.classification,
                    ap_device_slug=br.ap_device_slug,
                    ap_name=br.ap_name,
                    is_connected=br.is_connected,
                )
            )
        for s_list in readings_by_survey.values():
            s_list.sort(key=lambda item: item.rssi_dbm, reverse=True)

        return [
            WiFiRoomSurveySchema(
                id=s.id,
                survey_slug=s.survey_slug,
                room_id=s.room_id,
                room_slug=s.room_slug,
                room_name=s.room_name,
                label=s.label,
                trigger_mode=s.trigger_mode,
                captured_at=s.captured_at,
                connected_bssid=s.connected_bssid,
                connected_ssid=s.connected_ssid,
                link_speed_mbps=s.link_speed_mbps,
                frequency_mhz=s.frequency_mhz,
                best_5ghz_dbm=s.best_5ghz_dbm,
                best_24ghz_dbm=s.best_24ghz_dbm,
                best_ap_slug=s.best_ap_slug,
                best_ap_name=s.best_ap_name,
                rogue_count=s.rogue_count,
                neighbor_count=s.neighbor_count,
                grade_5ghz=s.grade_5ghz,
                grade_24ghz=s.grade_24ghz,
                wifi_health_grade=s.wifi_health_grade,
                notes=s.notes,
                readings=readings_by_survey.get(s.id, []),
            )
            for s in surveys
        ]

    async def create_room_survey(
        self,
        room_ref: str,
        payload: WiFiRoomSurveyCreate,
        wifi_adapter: WiFiTelemetryPort,
    ) -> WiFiRoomSurveySchema | None:
        room = await self.get_room_by_slug_or_id(room_ref)
        if not room:
            return None

        if payload.readings is not None and len(payload.readings) > 0:
            survey_slug = f"{room.slug}-survey-{uuid.uuid4().hex[:8]}"
            built = build_wifi_room_survey(
                room_slug=room.slug,
                room_name=room.name,
                survey_slug=survey_slug,
                label=payload.label or "Manual Room Wi-Fi Survey",
                trigger_mode=payload.trigger_mode,
                connected_bssid=payload.connected_bssid,
                connected_ssid=payload.connected_ssid,
                link_speed_mbps=payload.link_speed_mbps,
                frequency_mhz=payload.frequency_mhz,
                notes=payload.notes,
                readings=payload.readings,
                room_id=room.id,
            )
        else:
            built = await wifi_adapter.capture_room_wifi_scan(
                room_slug=room.slug,
                trigger_mode=payload.trigger_mode,
                label=payload.label,
                connected_bssid=payload.connected_bssid,
                link_speed_mbps=payload.link_speed_mbps,
                readings=None,
            )
            built.room_id = room.id
            built.room_name = room.name
            if payload.notes:
                built.notes = payload.notes

        survey_row = WiFiRoomSurvey(
            survey_slug=built.survey_slug,
            room_id=room.id,
            room_slug=room.slug,
            room_name=room.name,
            label=built.label,
            trigger_mode=built.trigger_mode,
            captured_at=built.captured_at,
            connected_bssid=built.connected_bssid,
            connected_ssid=built.connected_ssid,
            link_speed_mbps=built.link_speed_mbps,
            frequency_mhz=built.frequency_mhz,
            best_5ghz_dbm=built.best_5ghz_dbm,
            best_24ghz_dbm=built.best_24ghz_dbm,
            best_ap_slug=built.best_ap_slug,
            best_ap_name=built.best_ap_name,
            rogue_count=built.rogue_count,
            neighbor_count=built.neighbor_count,
            grade_5ghz=built.grade_5ghz,
            grade_24ghz=built.grade_24ghz,
            wifi_health_grade=built.wifi_health_grade,
            notes=built.notes,
        )
        self._session.add(survey_row)
        await self._session.flush()

        built.id = survey_row.id
        for idx, r_item in enumerate(built.readings, start=1):
            br_row = BssidReading(
                reading_key=f"{built.survey_slug}:{idx}:{r_item.bssid}",
                survey_id=survey_row.id,
                room_id=room.id,
                bssid=r_item.bssid,
                ssid=r_item.ssid,
                band=r_item.band,
                channel=r_item.channel,
                center_channel=r_item.center_channel,
                width_mhz=r_item.width_mhz,
                rssi_dbm=r_item.rssi_dbm,
                classification=r_item.classification,
                ap_device_slug=r_item.ap_device_slug,
                ap_name=r_item.ap_name,
                is_connected=r_item.is_connected,
            )
            self._session.add(br_row)

        if built.best_5ghz_dbm is not None:
            room.best_5ghz_rssi_dbm = built.best_5ghz_dbm
        if built.best_24ghz_dbm is not None:
            room.best_24ghz_rssi_dbm = built.best_24ghz_dbm

        await self._session.commit()
        return built

    async def _fetch_latest_survey_schemas_by_room(
        self,
    ) -> dict[str, WiFiRoomSurveySchema]:
        all_surveys_res = await self._session.execute(
            select(WiFiRoomSurvey).order_by(WiFiRoomSurvey.captured_at.desc())
        )
        latest_survey_by_room: dict[str, WiFiRoomSurvey] = {}
        for s in all_surveys_res.scalars().all():
            if s.room_id not in latest_survey_by_room:
                latest_survey_by_room[s.room_id] = s

        if not latest_survey_by_room:
            return {}

        survey_ids = [s.id for s in latest_survey_by_room.values()]
        readings_res = await self._session.execute(
            select(BssidReading).where(BssidReading.survey_id.in_(survey_ids))
        )
        readings_by_survey: dict[str, list[BssidReadingSchema]] = {}
        for br in readings_res.scalars().all():
            readings_by_survey.setdefault(br.survey_id, []).append(
                BssidReadingSchema(
                    id=br.id,
                    bssid=br.bssid,
                    ssid=br.ssid,
                    band=br.band,
                    channel=br.channel,
                    center_channel=br.center_channel,
                    width_mhz=br.width_mhz,
                    rssi_dbm=br.rssi_dbm,
                    classification=br.classification,
                    ap_device_slug=br.ap_device_slug,
                    ap_name=br.ap_name,
                    is_connected=br.is_connected,
                )
            )
        for s_list in readings_by_survey.values():
            s_list.sort(key=lambda item: item.rssi_dbm, reverse=True)

        result: dict[str, WiFiRoomSurveySchema] = {}
        for room_id, s in latest_survey_by_room.items():
            result[room_id] = WiFiRoomSurveySchema(
                id=s.id,
                survey_slug=s.survey_slug,
                room_id=s.room_id,
                room_slug=s.room_slug,
                room_name=s.room_name,
                label=s.label,
                trigger_mode=s.trigger_mode,
                captured_at=s.captured_at,
                connected_bssid=s.connected_bssid,
                connected_ssid=s.connected_ssid,
                link_speed_mbps=s.link_speed_mbps,
                frequency_mhz=s.frequency_mhz,
                best_5ghz_dbm=s.best_5ghz_dbm,
                best_24ghz_dbm=s.best_24ghz_dbm,
                best_ap_slug=s.best_ap_slug,
                best_ap_name=s.best_ap_name,
                rogue_count=s.rogue_count,
                neighbor_count=s.neighbor_count,
                grade_5ghz=s.grade_5ghz,
                grade_24ghz=s.grade_24ghz,
                wifi_health_grade=s.wifi_health_grade,
                notes=s.notes,
                readings=readings_by_survey.get(s.id, []),
            )
        return result

    async def apply_ping_sweep(self, sweep_result: PingSweepResultSchema) -> None:
        latest_stmt = (
            select(SonosTelemetrySnapshot.batch_id)
            .order_by(SonosTelemetrySnapshot.captured_at.desc())
            .limit(1)
        )
        latest_res = await self._session.execute(latest_stmt)
        batch_id = latest_res.scalar_one_or_none()
        if not batch_id:
            return

        by_uuid = {r.rincon_uuid: r for r in sweep_result.results}
        by_ip = {r.ip_address: r for r in sweep_result.results if r.ip_address}

        snaps_stmt = select(SonosTelemetrySnapshot).where(
            SonosTelemetrySnapshot.batch_id == batch_id
        )
        snaps_res = await self._session.execute(snaps_stmt)
        for row in snaps_res.scalars().all():
            item = by_uuid.get(row.rincon_uuid) or (
                by_ip.get(row.ip_address) if row.ip_address else None
            )
            if item is not None:
                row.ping_rtt_ms = item.ping_rtt_ms
                row.is_reachable = item.is_reachable
        await self._session.commit()

    async def evaluate_house_diagnostics(
        self,
        diagnostic_engine: DiagnosticEnginePort | None = None,
        include_archived: bool = False,
    ) -> HouseDiagnosticReportSchema:
        engine = diagnostic_engine or DiagnosticEngine()
        floors = await self.list_floors(include_archived=include_archived)
        rooms = await self.list_rooms(include_archived=include_archived)
        devices = await self.list_devices(include_archived=include_archived)
        ports = await self.list_switch_ports(include_archived=include_archived)
        latest_sonos = await self.get_sonos_telemetry()
        latest_surveys = await self._fetch_latest_survey_schemas_by_room()

        telem_by_uuid: dict[str, PlayerTelemetryDto] = {}
        if latest_sonos:
            telem_by_uuid = {p.rincon_uuid: p for p in latest_sonos.players}

        players_by_room: dict[str, list[PlayerTelemetryDto]] = {}
        for d in devices:
            if d.device_role != DeviceRole.SONOS_PLAYER.value or not d.room_id:
                continue
            if d.rincon_uuid and d.rincon_uuid in telem_by_uuid:
                p_dto = telem_by_uuid[d.rincon_uuid].model_copy(
                    update={"connection_mode": d.connection_mode}
                )
            else:
                p_dto = PlayerTelemetryDto(
                    rincon_uuid=d.rincon_uuid or d.slug,
                    zone_name=d.name,
                    ip_address=d.ip_address,
                    base_mac=d.mac_address,
                    bssid=d.bssid,
                    connection_mode=d.connection_mode,
                )
            players_by_room.setdefault(d.room_id, []).append(p_dto)

        ports_by_room: dict[str | None, list[SwitchPortRead]] = {}
        for p in ports:
            ports_by_room.setdefault(p.patched_room_id, []).append(
                SwitchPortRead.model_validate(p)
            )

        floors_by_id = {f.id: (f.slug, f.name) for f in floors}
        rooms_context = []
        for r in rooms:
            f_slug, f_name = floors_by_id.get(r.floor_id, (None, None))
            rooms_context.append(
                {
                    "room_id": r.id,
                    "room_slug": r.slug,
                    "room_name": r.name,
                    "floor_slug": f_slug,
                    "floor_name": f_name,
                    "survey": latest_surveys.get(r.id),
                    "players": players_by_room.get(r.id, []),
                    "switch_ports": ports_by_room.get(r.id, []),
                    "fallback_5ghz_dbm": r.best_5ghz_rssi_dbm,
                    "fallback_24ghz_dbm": r.best_24ghz_rssi_dbm,
                }
            )

        return engine.evaluate_house(
            rooms_context=rooms_context,
            mesh_links=latest_sonos.mesh_links if latest_sonos else [],
            designated_stp_root=(
                latest_sonos.designated_stp_root if latest_sonos else None
            ),
        )

    async def evaluate_room_diagnostics(
        self,
        room_ref: str,
        diagnostic_engine: DiagnosticEnginePort | None = None,
    ) -> RoomDiagnosticSummarySchema | None:
        room = await self.get_room_by_slug_or_id(room_ref)
        if not room:
            return None
        house_report = await self.evaluate_house_diagnostics(
            diagnostic_engine=diagnostic_engine,
            include_archived=room.is_archived,
        )
        for r_summary in house_report.rooms:
            if r_summary.room_id == room.id or r_summary.room_slug == room.slug:
                return r_summary
        return None

    async def get_house_overview(
        self,
        include_archived: bool = False,
        diagnostic_engine: DiagnosticEnginePort | None = None,
    ) -> HouseOverviewDto:
        floors = await self.list_floors(include_archived=include_archived)
        rooms = await self.list_rooms(include_archived=include_archived)
        devices = await self.list_devices(include_archived=include_archived)
        ports = await self.list_switch_ports(include_archived=include_archived)
        latest_sonos = await self.get_sonos_telemetry()
        latest_survey_by_room = await self._fetch_latest_survey_schemas_by_room()

        telem_by_uuid: dict[str, PlayerTelemetryDto] = {}
        if latest_sonos:
            telem_by_uuid = {p.rincon_uuid: p for p in latest_sonos.players}

        devices_by_room: dict[str | None, list[NetworkDeviceRead]] = {}
        players_by_room: dict[str, list[PlayerTelemetryDto]] = {}
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

            if d.device_role == DeviceRole.SONOS_PLAYER.value and d.room_id:
                if d.rincon_uuid and d.rincon_uuid in telem_by_uuid:
                    p_dto = telem_by_uuid[d.rincon_uuid].model_copy(
                        update={"connection_mode": d.connection_mode}
                    )
                else:
                    p_dto = PlayerTelemetryDto(
                        rincon_uuid=d.rincon_uuid or d.slug,
                        zone_name=d.name,
                        ip_address=d.ip_address,
                        base_mac=d.mac_address,
                        bssid=d.bssid,
                        connection_mode=d.connection_mode,
                    )
                players_by_room.setdefault(d.room_id, []).append(p_dto)

        ports_by_room: dict[str | None, list[SwitchPortRead]] = {}
        for p in ports:
            ports_by_room.setdefault(p.patched_room_id, []).append(
                SwitchPortRead.model_validate(p)
            )

        engine = diagnostic_engine or DiagnosticEngine()
        floors_by_id = {f.id: (f.slug, f.name) for f in floors}
        rooms_context = []
        for r in rooms:
            f_slug, f_name = floors_by_id.get(r.floor_id, (None, None))
            rooms_context.append(
                {
                    "room_id": r.id,
                    "room_slug": r.slug,
                    "room_name": r.name,
                    "floor_slug": f_slug,
                    "floor_name": f_name,
                    "survey": latest_survey_by_room.get(r.id),
                    "players": players_by_room.get(r.id, []),
                    "switch_ports": ports_by_room.get(r.id, []),
                    "fallback_5ghz_dbm": r.best_5ghz_rssi_dbm,
                    "fallback_24ghz_dbm": r.best_24ghz_rssi_dbm,
                }
            )

        house_diag = engine.evaluate_house(
            rooms_context=rooms_context,
            mesh_links=latest_sonos.mesh_links if latest_sonos else [],
            designated_stp_root=(
                latest_sonos.designated_stp_root if latest_sonos else None
            ),
        )
        diag_by_room_id = {rs.room_id: rs for rs in house_diag.rooms}

        rooms_by_floor: dict[str, list[RoomMatrixItemDto]] = {}
        for r in rooms:
            latest_s = latest_survey_by_room.get(r.id)
            room_diag = diag_by_room_id.get(r.id)
            best_5g = (
                latest_s.best_5ghz_dbm
                if latest_s and latest_s.best_5ghz_dbm is not None
                else r.best_5ghz_rssi_dbm
            )
            best_24g = (
                latest_s.best_24ghz_dbm
                if latest_s and latest_s.best_24ghz_dbm is not None
                else r.best_24ghz_rssi_dbm
            )
            base_room_dict = RoomRead.model_validate(r).model_dump()
            base_room_dict["best_5ghz_rssi_dbm"] = best_5g
            base_room_dict["best_24ghz_rssi_dbm"] = best_24g
            if room_diag is not None:
                base_room_dict["health_grade"] = room_diag.health_grade

            room_dto = RoomMatrixItemDto(
                **base_room_dict,
                best_5ghz_dbm=best_5g,
                best_24ghz_dbm=best_24g,
                best_ap_name=latest_s.best_ap_name if latest_s else "Galerie EAP650",
                link_speed_mbps=latest_s.link_speed_mbps if latest_s else 1201,
                rogue_count=latest_s.rogue_count if latest_s else 0,
                neighbor_count=latest_s.neighbor_count if latest_s else 0,
                wifi_health_grade=(
                    latest_s.wifi_health_grade if latest_s else r.health_grade
                ),
                sonos_health_grade=(
                    room_diag.sonos_pillar.health_grade if room_diag else "EXCELLENT"
                ),
                wired_health_grade=(
                    room_diag.wired_pillar.health_grade if room_diag else "GOOD"
                ),
                active_diagnostics_count=(
                    room_diag.active_diagnostics_count if room_diag else 0
                ),
                top_diagnostic_title=(
                    room_diag.top_diagnostic_title if room_diag else None
                ),
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
            active_diagnostics_count=house_diag.total_diagnostics_count,
            critical_diagnostics_count=house_diag.critical_diagnostics_count,
            latest_sonos_batch_id=latest_sonos.batch_id if latest_sonos else None,
            latest_sonos_captured_at=latest_sonos.captured_at if latest_sonos else None,
            floors=floor_dtos,
        )

    async def build_unified_graph(
        self,
        layer_filter: str = "ALL",
        floor_slug: str | None = None,
        room_slug: str | None = None,
        include_blocking: bool = True,
    ) -> TopologyGraphResponse:
        latest_sonos = await self.get_sonos_telemetry()
        return await synthesize_unified_topology_graph(
            session=self._session,
            latest_sonos=latest_sonos,
            layer_filter=layer_filter,
            floor_slug=floor_slug,
            room_slug=room_slug,
            include_blocking=include_blocking,
        )




