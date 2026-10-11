from __future__ import annotations

from datetime import datetime
from typing import Any
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
    best_5ghz_dbm: int | None = None
    best_24ghz_dbm: int | None = None
    best_ap_name: str | None = None
    link_speed_mbps: int | None = None
    rogue_count: int = 0
    neighbor_count: int = 0
    wifi_health_grade: str = "GOOD"
    sonos_health_grade: str = "GOOD"
    wired_health_grade: str = "GOOD"
    active_diagnostics_count: int = 0
    top_diagnostic_title: str | None = None
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
    active_diagnostics_count: int = 0
    critical_diagnostics_count: int = 0
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


class BssidClassificationResult(BaseModel):
    classification: str
    ap_device_slug: str | None = None
    ap_name: str | None = None
    radio_band: str | None = None


class AccessPointRadioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str | None = None
    radio_key: str
    ap_device_slug: str
    ap_name: str
    room_slug: str | None = None
    band: str
    base_mac: str
    bssid_suffix: str
    derived_bssids: list[str] = []
    channel: int
    center_channel: int
    width_mhz: int
    tx_power_dbm: int | None = None
    airtime_utilization_pct: float | None = None
    is_non_dfs: bool = True
    status: str = "CONNECTED"


class OmadaClientAssociationDto(BaseModel):
    client_name: str
    mac_address: str
    ip_address: str | None = None
    room_slug: str | None = None
    ap_device_slug: str
    ap_name: str
    connected_bssid: str
    ssid: str
    band: str
    channel: int
    rssi_dbm: int
    link_speed_mbps: int


class WiFiInfraSnapshot(BaseModel):
    captured_at: datetime
    omada_controller_url: str
    omada_reachable: bool
    controller_status: str
    degraded_reason: str | None = None
    radios: list[AccessPointRadioRead]
    clients: list[OmadaClientAssociationDto] = []


class BssidReadingInput(BaseModel):
    bssid: str
    ssid: str | None = None
    band: str
    channel: int
    center_channel: int | None = None
    width_mhz: int = 20
    rssi_dbm: int


class BssidReadingSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str | None = None
    bssid: str
    ssid: str | None = None
    band: str
    channel: int
    center_channel: int
    width_mhz: int
    rssi_dbm: int
    classification: str
    ap_device_slug: str | None = None
    ap_name: str | None = None
    is_connected: bool = False


class WiFiRoomSurveyCreate(BaseModel):
    label: str | None = None
    trigger_mode: str = "MANUAL_SURVEY"
    connected_bssid: str | None = None
    connected_ssid: str | None = None
    link_speed_mbps: int | None = None
    frequency_mhz: int | None = None
    notes: str | None = None
    readings: list[BssidReadingInput] | None = None


class WiFiRoomSurveySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str | None = None
    survey_slug: str
    room_id: str | None = None
    room_slug: str
    room_name: str
    label: str
    trigger_mode: str
    captured_at: datetime
    connected_bssid: str | None = None
    connected_ssid: str | None = None
    link_speed_mbps: int | None = None
    frequency_mhz: int | None = None
    best_5ghz_dbm: int | None = None
    best_24ghz_dbm: int | None = None
    best_ap_slug: str | None = None
    best_ap_name: str | None = None
    rogue_count: int = 0
    neighbor_count: int = 0
    grade_5ghz: str
    grade_24ghz: str
    wifi_health_grade: str
    notes: str | None = None
    readings: list[BssidReadingSchema] = []


class TopologyNodeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    device_id: str | None = None
    slug: str
    name: str
    device_role: str
    model_name: str
    ip_address: str | None = None
    base_mac: str | None = None
    rincon_uuid: str | None = None
    room_id: str | None = None
    room_slug: str | None = None
    room_name: str | None = None
    floor_id: str | None = None
    floor_slug: str | None = None
    floor_name: str | None = None
    connection_mode: str | None = None
    health_grade: str = "GOOD"
    ofdm_ani_level: int | None = None
    noise_floor_dbm: int | None = None
    phy_error_rate: float | None = None
    stp_path_cost: int | None = None
    designated_root: str | None = None
    is_stp_root: bool = False
    is_ghost_group: bool = False
    rssi_dbm: int | None = None
    ap_channels: str | None = None
    switch_port_number: int | None = None
    x: float = 0.0
    y: float = 0.0
    pos_x: float = 0.0
    pos_y: float = 0.0


class DeviceConnectionEdgeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    layer: str
    source: str
    source_id: str
    source_slug: str
    source_name: str
    target: str
    target_id: str
    target_slug: str
    target_name: str
    label: str
    is_forwarding: bool = True
    line_style: str = "solid"
    stp_state: str | None = None
    band: str | None = None
    channel: int | None = None
    from_db: int | None = None
    to_db: int | None = None
    rssi_dbm: int | None = None
    link_speed_mbps: int | None = None
    port_number: int | None = None
    vlan_label: str | None = None
    health_grade: str = "GOOD"


class TopologyGraphResponse(BaseModel):
    layer_filter: str = "ALL"
    floor_slug: str | None = None
    room_slug: str | None = None
    include_blocking: bool = True
    designated_stp_root: str
    total_nodes: int
    total_edges: int
    nodes: list[TopologyNodeSchema]
    edges: list[DeviceConnectionEdgeSchema]


TopologyGraphDto = TopologyGraphResponse


class SolutionProposalSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    rank: int
    rule_code: str
    title: str
    description: str
    action_type: str = "GUIDED_PHYSICAL"
    one_click_action: str | None = None
    requires_sonosnet_disable_guard: bool = False
    stp_guard_warning: str | None = None
    target_room_slug: str | None = None
    target_device_name: str | None = None


class RoomDiagnosticSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    room_slug: str
    room_name: str
    layer: str
    severity: str
    rule_code: str
    title: str
    summary: str
    evidence: dict[str, Any] = {}
    affected_devices: list[str] = []
    solution_proposals: list[SolutionProposalSchema] = []


class WiFiPillarSummarySchema(BaseModel):
    health_grade: str
    best_5ghz_dbm: int | None = None
    best_24ghz_dbm: int | None = None
    grade_5ghz: str = "GOOD"
    grade_24ghz: str = "GOOD"
    covering_ap_slug: str | None = None
    covering_ap_name: str | None = None
    connected_bssid: str | None = None
    connected_ssid: str | None = None
    link_speed_mbps: int | None = None
    channel_summary: str = ""
    summary_note: str = ""
    rogue_count: int = 0
    rogue_ssids: list[str] = []
    neighbor_count: int = 0
    co_channel_neighbors: list[str] = []
    has_channel_6_high_power_wifi: bool = False


class PlayerDiagnosticItemSchema(BaseModel):
    rincon_uuid: str
    zone_name: str
    ip_address: str | None = None
    connection_mode: str
    rf_grade: str
    link_grade: str
    overall_grade: str
    ofdm_ani_level: int | None = None
    noise_floor_dbm: int | None = None
    phy_error_rate: float | None = None
    stp_path_cost: int | None = None
    designated_root: str | None = None
    is_root_healthy: bool = True
    active_forwarding_snr_db: int | None = None
    active_forwarding_peer: str | None = None
    blocked_links_ignored: int = 0
    is_ghost_group: bool = False
    ping_rtt_ms: float | None = None
    grading_rationale: str = ""


class SonosPillarSummarySchema(BaseModel):
    health_grade: str
    player_count: int = 0
    total_players: int = 0
    reachable_count: int = 0
    designated_stp_root: str
    is_stp_root_healthy: bool = True
    worst_ofdm_ani_level: int | None = None
    max_phy_error_rate: float | None = None
    max_stp_path_cost: int | None = None
    has_ghost_group: bool = False
    summary_note: str = ""
    players: list[PlayerDiagnosticItemSchema] = []


class WiredPillarSummarySchema(BaseModel):
    health_grade: str
    has_vlan10_wall_jack: bool = False
    available_ports: list[SwitchPortRead] = []
    port_numbers: list[int] = []
    vlan_summary: str = ""
    stp_root_guard_required: bool = False
    stp_root_guard_note: str = ""
    stp_guard_note: str = ""


class RoomDiagnosticSummarySchema(BaseModel):
    room_id: str
    room_slug: str
    room_name: str
    floor_slug: str | None = None
    floor_name: str | None = None
    health_grade: str
    active_diagnostics_count: int = 0
    critical_count: int = 0
    marginal_count: int = 0
    top_diagnostic_title: str | None = None
    wifi_pillar: WiFiPillarSummarySchema
    sonos_pillar: SonosPillarSummarySchema
    wired_pillar: WiredPillarSummarySchema
    diagnostics: list[RoomDiagnosticSchema] = []
    solution_proposals: list[SolutionProposalSchema] = []


class HouseDiagnosticReportSchema(BaseModel):
    evaluated_at: datetime
    overall_health_grade: str
    designated_stp_root: str
    is_stp_root_healthy: bool = True
    sonosnet_wireless_player_count: int = 0
    total_diagnostics_count: int = 0
    critical_diagnostics_count: int = 0
    marginal_diagnostics_count: int = 0
    house_diagnostics: list[RoomDiagnosticSchema] = []
    rooms: list[RoomDiagnosticSummarySchema] = []


HouseDiagnosticReport = HouseDiagnosticReportSchema


class PingSweepItemSchema(BaseModel):
    rincon_uuid: str
    zone_name: str
    room_slug: str | None = None
    ip_address: str | None = None
    is_reachable: bool = True
    ping_rtt_ms: float
    jitter_ms: float = 0.0
    dpc_ducking_risk: bool = False


class PingSweepResultSchema(BaseModel):
    swept_at: datetime
    total_probed: int
    reachable_count: int
    max_rtt_ms: float
    avg_rtt_ms: float
    dpc_risk_zones: list[str] = []
    results: list[PingSweepItemSchema] = []


class BssidDeltaItemSchema(BaseModel):
    bssid: str
    ssid: str | None = None
    band: str
    channel: int
    classification: str
    baseline_rssi_dbm: int | None = None
    target_rssi_dbm: int | None = None
    delta_rssi_dbm: int | None = None
    is_new: bool = False
    is_vanished: bool = False


class SurveyComparisonDeltaSchema(BaseModel):
    room_id: str
    room_slug: str
    room_name: str
    baseline_survey_id: str
    baseline_survey_slug: str
    baseline_label: str
    baseline_captured_at: datetime
    target_survey_id: str
    target_survey_slug: str
    target_label: str
    target_captured_at: datetime
    # Wi-Fi Deltas
    baseline_5ghz_dbm: int | None = None
    target_5ghz_dbm: int | None = None
    delta_5ghz_dbm: int | None = None
    baseline_24ghz_dbm: int | None = None
    target_24ghz_dbm: int | None = None
    delta_24ghz_dbm: int | None = None
    baseline_link_speed_mbps: int | None = None
    target_link_speed_mbps: int | None = None
    delta_link_speed_mbps: int | None = None
    baseline_best_ap_name: str | None = None
    target_best_ap_name: str | None = None
    baseline_wifi_health_grade: str
    target_wifi_health_grade: str
    wifi_improved: bool = False
    # Sonos Deltas
    baseline_ofdm_ani_level: int | None = None
    target_ofdm_ani_level: int | None = None
    delta_ofdm_ani_level: int | None = None
    baseline_phy_error_rate: float | None = None
    target_phy_error_rate: float | None = None
    delta_phy_error_rate: float | None = None
    baseline_stp_path_cost: int | None = None
    target_stp_path_cost: int | None = None
    delta_stp_path_cost: int | None = None
    baseline_ping_rtt_ms: float | None = None
    target_ping_rtt_ms: float | None = None
    delta_ping_rtt_ms: float | None = None
    sonos_improved: bool = False
    # Summary
    overall_improved: bool = False
    summary_narrative: str = ""
    bssid_deltas: list[BssidDeltaItemSchema] = []


class PlayerHistorySampleSchema(BaseModel):
    rincon_uuid: str
    zone_name: str
    connection_mode: str
    ofdm_ani_level: int | None = None
    noise_floor_dbm: int | None = None
    phy_error_rate: float | None = None
    ping_rtt_ms: float | None = None
    stp_path_cost: int | None = None


class RoomHistoryPointSchema(BaseModel):
    timestamp: datetime
    batch_id: str | None = None
    consumer_id: str | None = None
    peak_ofdm_ani_level: int | None = None
    total_phy_error_rate: float | None = None
    avg_ping_rtt_ms: float | None = None
    best_5ghz_dbm: int | None = None
    best_24ghz_dbm: int | None = None
    link_speed_mbps: int | None = None
    worst_stp_path_cost: int | None = None
    health_grade: str = "GOOD"
    players: list[PlayerHistorySampleSchema] = []


class RoomHistoryResponseSchema(BaseModel):
    room_id: str
    room_slug: str
    room_name: str
    time_range: str
    total_samples: int
    peak_ani: int | None = None
    avg_phy_error_rate: float | None = None
    avg_ping_rtt_ms: float | None = None
    summary: str
    samples: list[RoomHistoryPointSchema] = []


class DaemonStatusSchema(BaseModel):
    is_running: bool
    interval_sec: float
    retention_days: int
    last_cycle_at: datetime | None = None
    total_cycles: int = 0
    last_error: str | None = None


class DaemonCollectResultSchema(BaseModel):
    status: str
    batch_id: str
    total_players: int
    pruned_count: int
    executed_at: datetime




