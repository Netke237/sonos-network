from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.models.entities import ConnectionMode, DeviceRole, HealthGrade


class FloorCreate(BaseModel):
    name: str
    slug: str | None = None
    level_order: int = 0


class FloorUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    level_order: int | None = None
    is_archived: bool | None = None


class FloorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    name: str
    level_order: int
    is_archived: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RoomCreate(BaseModel):
    name: str
    slug: str | None = None
    floor_id: str
    pos_x: float = 0.0
    pos_y: float = 0.0
    health_grade: HealthGrade = HealthGrade.GOOD
    best_5ghz_rssi_dbm: int | None = None
    best_24ghz_rssi_dbm: int | None = None
    description: str | None = None


class RoomUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    floor_id: str | None = None
    pos_x: float | None = None
    pos_y: float | None = None
    health_grade: HealthGrade | None = None
    best_5ghz_rssi_dbm: int | None = None
    best_24ghz_rssi_dbm: int | None = None
    description: str | None = None
    is_archived: bool | None = None


class RoomRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    name: str
    floor_id: str
    pos_x: float
    pos_y: float
    health_grade: str
    best_5ghz_rssi_dbm: int | None = None
    best_24ghz_rssi_dbm: int | None = None
    description: str | None = None
    is_archived: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SwitchPortCreate(BaseModel):
    port_number: int
    switch_name: str = "Netgear GS316EP"
    switch_ip: str = "192.168.55.155"
    pvid: int = 1
    untagged_vlans: str = "1"
    tagged_vlans: str = ""
    bpdu_policy: str = "PASS_THROUGH"
    loop_detection_disabled: bool = True
    patched_room_id: str | None = None
    connected_device_label: str | None = None


class SwitchPortUpdate(BaseModel):
    port_number: int | None = None
    switch_name: str | None = None
    switch_ip: str | None = None
    pvid: int | None = None
    untagged_vlans: str | None = None
    tagged_vlans: str | None = None
    bpdu_policy: str | None = None
    loop_detection_disabled: bool | None = None
    patched_room_id: str | None = None
    connected_device_label: str | None = None
    is_archived: bool | None = None


class SwitchPortRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    port_number: int
    switch_name: str
    switch_ip: str
    pvid: int
    untagged_vlans: str
    tagged_vlans: str
    bpdu_policy: str
    loop_detection_disabled: bool
    patched_room_id: str | None = None
    connected_device_label: str | None = None
    is_archived: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class NetworkDeviceCreate(BaseModel):
    name: str
    slug: str | None = None
    device_role: DeviceRole = DeviceRole.SONOS_PLAYER
    model_name: str
    ip_address: str | None = None
    base_mac: str | None = None
    sonosnet_bssid: str | None = None
    rincon_uuid: str | None = None
    connection_mode: ConnectionMode | None = None
    health_grade: HealthGrade = HealthGrade.GOOD
    ofdm_ani_level: int | None = None
    room_id: str | None = None
    switch_port_id: str | None = None
    notes: str | None = None
    is_archived: bool = False


class NetworkDeviceUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    device_role: DeviceRole | None = None
    model_name: str | None = None
    ip_address: str | None = None
    base_mac: str | None = None
    sonosnet_bssid: str | None = None
    rincon_uuid: str | None = None
    connection_mode: ConnectionMode | None = None
    health_grade: HealthGrade | None = None
    ofdm_ani_level: int | None = None
    room_id: str | None = None
    switch_port_id: str | None = None
    notes: str | None = None
    is_archived: bool | None = None


class NetworkDeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    name: str
    device_role: str
    model_name: str
    ip_address: str | None = None
    base_mac: str | None = None
    sonosnet_bssid: str | None = None
    rincon_uuid: str | None = None
    connection_mode: str | None = None
    health_grade: str
    ofdm_ani_level: int | None = None
    noise_floor_dbm: int | None = None
    phy_error_total: int | None = None
    phy_error_rate: float | None = None
    designated_root: str | None = None
    stp_path_cost: int | None = None
    group_id: str | None = None
    coordinator_uuid: str | None = None
    is_ghost_group: bool = False
    master_volume: int | None = None
    ping_rtt_ms: float | None = None
    ieee_channel: int | None = None
    bonded_parent_uuid: str | None = None
    room_id: str | None = None
    switch_port_id: str | None = None
    notes: str | None = None
    is_archived: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RoomMatrixItemDto(RoomRead):
    devices: list[NetworkDeviceRead] = []
    switch_ports: list[SwitchPortRead] = []


class FloorMatrixItemDto(FloorRead):
    rooms: list[RoomMatrixItemDto] = []


class HouseOverviewDto(BaseModel):
    total_floors: int
    total_rooms: int
    total_sonos_players: int
    total_wifi_aps: int
    total_switch_ports: int
    designated_stp_root: str
    ghost_group_count: int = 0
    has_ghost_groups: bool = False
    ghost_group_zones: list[str] = []
    latest_sonos_batch_id: str | None = None
    latest_sonos_captured_at: datetime | None = None
    floors: list[FloorMatrixItemDto]


class PlayerTelemetryDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rincon_uuid: str
    zone_name: str
    device_id: str | None = None
    room_id: str | None = None
    room_name: str | None = None
    ip_address: str | None = None
    base_mac: str | None = None
    sonosnet_bssid: str | None = None
    is_reachable: bool = True
    connection_mode: ConnectionMode = ConnectionMode.SONOSNET_MODE
    ieee_channel: int | None = None
    ofdm_ani_level: int | None = None
    noise_floor_dbm: int | None = None
    phy_error_total: int | None = None
    phy_error_rate: float | None = None
    designated_root: str | None = None
    stp_root_port: str | None = None
    stp_path_cost: int | None = None
    group_id: str | None = None
    coordinator_uuid: str | None = None
    has_vanished_devices: bool = False
    is_ghost_group: bool = False
    master_volume: int | None = None
    ping_rtt_ms: float | None = None
    bonded_parent_uuid: str | None = None


class SonosMeshLinkDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_rincon_uuid: str
    target_rincon_uuid: str
    source_zone_name: str | None = None
    target_zone_name: str | None = None
    source_bssid: str | None = None
    target_bssid: str | None = None
    channel: int = 6
    from_db: int
    to_db: int
    stp_state: str = "FORWARDING"


class HouseholdSonosSnapshot(BaseModel):
    batch_id: str
    captured_at: datetime
    consumer_id: str
    designated_stp_root: str
    is_root_healthy: bool
    total_players: int
    reachable_players: int
    ghost_group_count: int
    has_ghost_groups: bool
    ghost_group_zones: list[str]
    players: list[PlayerTelemetryDto]
    mesh_links: list[SonosMeshLinkDto]


class GhostFlushRequest(BaseModel):
    zone_ips: list[str] | None = None


class GhostFlushZoneResult(BaseModel):
    zone_name: str
    rincon_uuid: str
    ip_address: str
    previous_group_id: str | None = None
    new_group_id: str
    status: str


class GhostFlushResult(BaseModel):
    flushed_count: int
    flushed_zones: list[str]
    results: list[GhostFlushZoneResult]
    captured_at: datetime


class PlayerRfSample(BaseModel):
    rincon_uuid: str
    zone_name: str
    room_id: str | None = None
    ip_address: str | None = None
    ieee_channel: int | None = None
    ofdm_ani_level: int | None = None
    noise_floor_dbm: int | None = None
    phy_error_total: int | None = None
    phy_error_rate: float
    captured_at: datetime

