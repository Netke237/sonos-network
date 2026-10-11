from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class DeviceRole(str, Enum):
    SONOS_PLAYER = "SONOS_PLAYER"
    WIFI_AP = "WIFI_AP"
    SWITCH = "SWITCH"
    ROUTER = "ROUTER"
    CLIENT_DEVICE = "CLIENT_DEVICE"
    EMI_SOURCE = "EMI_SOURCE"


class ConnectionMode(str, Enum):
    ETHERNET_ROOT = "ETHERNET_ROOT"
    ETHERNET_NODE = "ETHERNET_NODE"
    SONOSNET_MODE = "SONOSNET_MODE"
    STATION_MODE = "STATION_MODE"
    HT_SATELLITE = "HT_SATELLITE"


class HealthGrade(str, Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    MARGINAL = "MARGINAL"
    CRITICAL = "CRITICAL"


class StpPortState(str, Enum):
    FORWARDING = "FORWARDING"
    BLOCKING = "BLOCKING"
    DISABLED = "DISABLED"


class Floor(Base):
    __tablename__ = "floors"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_new_uuid)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    level_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_new_uuid)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    floor_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("floors.id"), index=True, nullable=False
    )
    pos_x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    pos_y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    health_grade: Mapped[str] = mapped_column(
        String(32), nullable=False, default=HealthGrade.GOOD.value
    )
    best_5ghz_rssi_dbm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    best_24ghz_rssi_dbm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class SwitchPort(Base):
    __tablename__ = "switch_ports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_new_uuid)
    port_number: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    switch_name: Mapped[str] = mapped_column(
        String(120), nullable=False, default="Netgear GS316EP"
    )
    switch_ip: Mapped[str] = mapped_column(
        String(64), nullable=False, default="192.168.55.155"
    )
    pvid: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    untagged_vlans: Mapped[str] = mapped_column(String(64), nullable=False, default="1")
    tagged_vlans: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    bpdu_policy: Mapped[str] = mapped_column(
        String(64), nullable=False, default="PASS_THROUGH"
    )
    loop_detection_disabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    patched_room_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("rooms.id"), index=True, nullable=True
    )
    connected_device_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class NetworkDevice(Base):
    __tablename__ = "network_devices"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_new_uuid)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    device_role: Mapped[str] = mapped_column(
        String(32), nullable=False, default=DeviceRole.SONOS_PLAYER.value
    )
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    base_mac: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sonosnet_bssid: Mapped[str | None] = mapped_column(String(32), nullable=True)
    rincon_uuid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    connection_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    health_grade: Mapped[str] = mapped_column(
        String(32), nullable=False, default=HealthGrade.GOOD.value
    )
    ofdm_ani_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    room_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("rooms.id"), index=True, nullable=True
    )
    switch_port_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("switch_ports.id"), index=True, nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class SonosTelemetrySnapshot(Base):
    __tablename__ = "sonos_telemetry_snapshots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_new_uuid)
    snapshot_key: Mapped[str | None] = mapped_column(
        String(160), unique=True, index=True, nullable=True
    )
    batch_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, default=_utcnow
    )
    consumer_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default="on-demand"
    )
    device_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("network_devices.id"), index=True, nullable=True
    )
    room_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("rooms.id"), index=True, nullable=True
    )
    rincon_uuid: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    zone_name: Mapped[str] = mapped_column(String(120), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    base_mac: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sonosnet_bssid: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_reachable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    connection_mode: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ConnectionMode.SONOSNET_MODE.value
    )
    ieee_channel: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ofdm_ani_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    noise_floor_dbm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    phy_error_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    phy_error_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    designated_root: Mapped[str | None] = mapped_column(String(64), nullable=True)
    stp_root_port: Mapped[str | None] = mapped_column(String(64), nullable=True)
    stp_path_cost: Mapped[int | None] = mapped_column(Integer, nullable=True)
    group_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    coordinator_uuid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    has_vanished_devices: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    is_ghost_group: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    master_volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ping_rtt_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    bonded_parent_uuid: Mapped[str | None] = mapped_column(String(64), nullable=True)


class SonosMeshLink(Base):
    __tablename__ = "sonos_mesh_links"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_new_uuid)
    link_key: Mapped[str | None] = mapped_column(
        String(160), unique=True, index=True, nullable=True
    )
    batch_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, default=_utcnow
    )
    source_rincon_uuid: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    target_rincon_uuid: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_bssid: Mapped[str | None] = mapped_column(String(32), nullable=True)
    target_bssid: Mapped[str | None] = mapped_column(String(32), nullable=True)
    channel: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    from_db: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    to_db: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stp_state: Mapped[str] = mapped_column(
        String(32), nullable=False, default=StpPortState.FORWARDING.value
    )

