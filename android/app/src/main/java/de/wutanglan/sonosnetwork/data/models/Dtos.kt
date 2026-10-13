package de.wutanglan.sonosnetwork.data.models

import kotlinx.serialization.Serializable

@Serializable
data class BssidReadingInputDto(
    val bssid: String,
    val ssid: String? = null,
    val band: String, // "2.4GHz" or "5GHz"
    val channel: Int,
    val center_channel: Int? = null,
    val width_mhz: Int = 20,
    val rssi_dbm: Int
)

@Serializable
data class RoomSurveyInputDto(
    val label: String? = null,
    val trigger_mode: String = "MANUAL_SURVEY",
    val captured_at: String? = null,
    val connected_bssid: String? = null,
    val connected_ssid: String? = null,
    val link_speed_mbps: Int? = null,
    val frequency_mhz: Int? = null,
    val notes: String? = null,
    val readings: List<BssidReadingInputDto>? = null
)

@Serializable
data class BssidReadingDto(
    val id: String? = null,
    val bssid: String,
    val ssid: String? = null,
    val band: String,
    val channel: Int,
    val center_channel: Int? = null,
    val width_mhz: Int = 20,
    val rssi_dbm: Int,
    val classification: String = "NEIGHBOR_WIFI",
    val ap_device_slug: String? = null,
    val ap_name: String? = null,
    val is_connected: Boolean = false
)

@Serializable
data class WiFiRoomSurveyDto(
    val id: String? = null,
    val survey_slug: String,
    val room_id: String? = null,
    val room_slug: String,
    val room_name: String,
    val label: String,
    val trigger_mode: String,
    val captured_at: String,
    val connected_bssid: String? = null,
    val connected_ssid: String? = null,
    val link_speed_mbps: Int? = null,
    val frequency_mhz: Int? = null,
    val best_5ghz_dbm: Int? = null,
    val best_24ghz_dbm: Int? = null,
    val best_ap_slug: String? = null,
    val best_ap_name: String? = null,
    val rogue_count: Int = 0,
    val neighbor_count: Int = 0,
    val grade_5ghz: String = "GOOD",
    val grade_24ghz: String = "GOOD",
    val wifi_health_grade: String = "GOOD",
    val notes: String? = null,
    val readings: List<BssidReadingDto> = emptyList()
)

@Serializable
data class NetworkDeviceDto(
    val id: String,
    val slug: String,
    val name: String,
    val device_role: String,
    val connection_mode: String? = null,
    val health_grade: String = "GOOD",
    val base_mac: String? = null,
    val sonosnet_bssid: String? = null,
    val rincon_uuid: String? = null,
    val ip_address: String? = null,
    val model_name: String = "",
    val room_id: String? = null,
    val is_archived: Boolean = false
)

@Serializable
data class SwitchPortDto(
    val id: String,
    val port_number: Int,
    val switch_name: String = "Netgear GS316EP",
    val switch_ip: String = "192.168.55.155",
    val pvid: Int = 1,
    val untagged_vlans: String = "1",
    val tagged_vlans: String = "",
    val bpdu_policy: String = "PASS_THROUGH",
    val loop_detection_disabled: Boolean = true,
    val patched_room_id: String? = null,
    val connected_device_label: String? = null,
    val is_archived: Boolean = false
)

@Serializable
data class RoomMatrixItemDto(
    val id: String,
    val slug: String,
    val name: String,
    val floor_id: String,
    val pos_x: Float = 0f,
    val pos_y: Float = 0f,
    val health_grade: String = "GOOD",
    val best_5ghz_rssi_dbm: Int? = null,
    val best_24ghz_rssi_dbm: Int? = null,
    val description: String? = null,
    val best_5ghz_dbm: Int? = null,
    val best_24ghz_dbm: Int? = null,
    val best_ap_name: String? = null,
    val link_speed_mbps: Int? = null,
    val rogue_count: Int = 0,
    val neighbor_count: Int = 0,
    val wifi_health_grade: String = "GOOD",
    val sonos_health_grade: String = "GOOD",
    val wired_health_grade: String = "GOOD",
    val active_diagnostics_count: Int = 0,
    val top_diagnostic_title: String? = null,
    val devices: List<NetworkDeviceDto> = emptyList(),
    val switch_ports: List<SwitchPortDto> = emptyList()
)

@Serializable
data class FloorMatrixItemDto(
    val id: String,
    val slug: String,
    val name: String,
    val level_order: Int = 0,
    val is_archived: Boolean = false,
    val rooms: List<RoomMatrixItemDto> = emptyList()
)

@Serializable
data class HouseOverviewDto(
    val total_floors: Int,
    val total_rooms: Int,
    val total_sonos_players: Int,
    val total_wifi_aps: Int,
    val total_switch_ports: Int,
    val designated_stp_root: String,
    val ghost_group_count: Int = 0,
    val has_ghost_groups: Boolean = false,
    val ghost_group_zones: List<String> = emptyList(),
    val active_diagnostics_count: Int = 0,
    val critical_diagnostics_count: Int = 0,
    val latest_sonos_batch_id: String? = null,
    val latest_sonos_captured_at: String? = null,
    val floors: List<FloorMatrixItemDto> = emptyList()
)

@Serializable
data class TopologyNodeDto(
    val id: String,
    val device_id: String? = null,
    val slug: String,
    val name: String,
    val device_role: String,
    val model_name: String,
    val ip_address: String? = null,
    val base_mac: String? = null,
    val rincon_uuid: String? = null,
    val room_id: String? = null,
    val room_slug: String? = null,
    val room_name: String? = null,
    val floor_id: String? = null,
    val floor_slug: String? = null,
    val floor_name: String? = null,
    val connection_mode: String? = null,
    val health_grade: String = "GOOD",
    val ofdm_ani_level: Int? = null,
    val noise_floor_dbm: Int? = null,
    val phy_error_rate: Double? = null,
    val stp_path_cost: Int? = null,
    val designated_root: String? = null,
    val is_stp_root: Boolean = false,
    val is_ghost_group: Boolean = false,
    val rssi_dbm: Int? = null,
    val ap_channels: String? = null,
    val switch_port_number: Int? = null,
    val x: Float = 0f,
    val y: Float = 0f,
    val pos_x: Float = 0f,
    val pos_y: Float = 0f
)

@Serializable
data class DeviceConnectionEdgeDto(
    val id: String,
    val layer: String,
    val source: String,
    val source_id: String,
    val source_slug: String,
    val source_name: String,
    val target: String,
    val target_id: String,
    val target_slug: String,
    val target_name: String,
    val label: String,
    val is_forwarding: Boolean = true,
    val line_style: String = "solid",
    val stp_state: String? = null,
    val band: String? = null,
    val channel: Int? = null,
    val from_db: Int? = null,
    val to_db: Int? = null,
    val rssi_dbm: Int? = null,
    val link_speed_mbps: Int? = null,
    val port_number: Int? = null,
    val vlan_label: String? = null,
    val health_grade: String = "GOOD"
)

@Serializable
data class TopologyGraphDto(
    val layer_filter: String = "ALL",
    val floor_slug: String? = null,
    val room_slug: String? = null,
    val include_blocking: Boolean = true,
    val designated_stp_root: String,
    val total_nodes: Int,
    val total_edges: Int,
    val nodes: List<TopologyNodeDto> = emptyList(),
    val edges: List<DeviceConnectionEdgeDto> = emptyList()
)

@Serializable
data class SolutionProposalDto(
    val id: String,
    val rank: Int,
    val rule_code: String,
    val title: String,
    val description: String,
    val action_type: String = "GUIDED_PHYSICAL",
    val one_click_action: String? = null,
    val requires_sonosnet_disable_guard: Boolean = false,
    val stp_guard_warning: String? = null,
    val target_room_slug: String? = null,
    val target_device_name: String? = null
)

@Serializable
data class RoomDiagnosticDto(
    val id: String,
    val room_slug: String,
    val room_name: String,
    val layer: String,
    val severity: String,
    val rule_code: String,
    val title: String,
    val summary: String,
    val affected_devices: List<String> = emptyList(),
    val solution_proposals: List<SolutionProposalDto> = emptyList()
)

@Serializable
data class WiFiPillarSummaryDto(
    val health_grade: String = "GOOD",
    val best_5ghz_dbm: Int? = null,
    val best_24ghz_dbm: Int? = null,
    val grade_5ghz: String = "GOOD",
    val grade_24ghz: String = "GOOD",
    val covering_ap_slug: String? = null,
    val covering_ap_name: String? = null,
    val connected_bssid: String? = null,
    val connected_ssid: String? = null,
    val link_speed_mbps: Int? = null,
    val channel_summary: String = "",
    val summary_note: String = "",
    val rogue_count: Int = 0,
    val rogue_ssids: List<String> = emptyList(),
    val neighbor_count: Int = 0,
    val co_channel_neighbors: List<String> = emptyList(),
    val has_channel_6_high_power_wifi: Boolean = false
)

@Serializable
data class PlayerDiagnosticItemDto(
    val rincon_uuid: String,
    val zone_name: String,
    val ip_address: String? = null,
    val connection_mode: String = "SONOSNET_MODE",
    val rf_grade: String = "GOOD",
    val link_grade: String = "GOOD",
    val overall_grade: String = "GOOD",
    val ofdm_ani_level: Int? = null,
    val noise_floor_dbm: Int? = null,
    val phy_error_rate: Double? = null,
    val stp_path_cost: Int? = null,
    val designated_root: String? = null,
    val is_root_healthy: Boolean = true,
    val active_forwarding_snr_db: Int? = null,
    val active_forwarding_peer: String? = null,
    val blocked_links_ignored: Int = 0,
    val is_ghost_group: Boolean = false,
    val ping_rtt_ms: Double? = null,
    val grading_rationale: String = ""
)

@Serializable
data class SonosPillarSummaryDto(
    val health_grade: String = "GOOD",
    val player_count: Int = 0,
    val total_players: Int = 0,
    val reachable_count: Int = 0,
    val designated_stp_root: String = "",
    val is_stp_root_healthy: Boolean = true,
    val worst_ofdm_ani_level: Int? = null,
    val max_phy_error_rate: Double? = null,
    val max_stp_path_cost: Int? = null,
    val has_ghost_group: Boolean = false,
    val summary_note: String = "",
    val players: List<PlayerDiagnosticItemDto> = emptyList()
)

@Serializable
data class WiredPillarSummaryDto(
    val health_grade: String = "GOOD",
    val has_vlan10_wall_jack: Boolean = false,
    val available_ports: List<SwitchPortDto> = emptyList(),
    val port_numbers: List<Int> = emptyList(),
    val vlan_summary: String = "",
    val stp_root_guard_required: Boolean = false,
    val stp_root_guard_note: String = "",
    val stp_guard_note: String = ""
)

@Serializable
data class RoomDiagnosticSummaryDto(
    val room_id: String,
    val room_slug: String,
    val room_name: String,
    val floor_slug: String? = null,
    val floor_name: String? = null,
    val health_grade: String = "GOOD",
    val active_diagnostics_count: Int = 0,
    val critical_count: Int = 0,
    val marginal_count: Int = 0,
    val top_diagnostic_title: String? = null,
    val wifi_pillar: WiFiPillarSummaryDto = WiFiPillarSummaryDto(),
    val sonos_pillar: SonosPillarSummaryDto = SonosPillarSummaryDto(),
    val wired_pillar: WiredPillarSummaryDto = WiredPillarSummaryDto(),
    val diagnostics: List<RoomDiagnosticDto> = emptyList(),
    val solution_proposals: List<SolutionProposalDto> = emptyList()
)

@Serializable
data class HouseDiagnosticReportDto(
    val evaluated_at: String,
    val overall_health_grade: String = "GOOD",
    val designated_stp_root: String = "",
    val is_stp_root_healthy: Boolean = true,
    val sonosnet_wireless_player_count: Int = 0,
    val total_diagnostics_count: Int = 0,
    val critical_diagnostics_count: Int = 0,
    val marginal_diagnostics_count: Int = 0,
    val house_diagnostics: List<RoomDiagnosticDto> = emptyList(),
    val rooms: List<RoomDiagnosticSummaryDto> = emptyList()
)

@Serializable
data class GhostFlushZoneResultDto(
    val zone_name: String,
    val rincon_uuid: String,
    val ip_address: String,
    val previous_group_id: String? = null,
    val new_group_id: String,
    val status: String
)

@Serializable
data class GhostFlushResultDto(
    val flushed_count: Int,
    val flushed_zones: List<String> = emptyList(),
    val results: List<GhostFlushZoneResultDto> = emptyList(),
    val captured_at: String
)

@Serializable
data class PlayerTelemetryDto(
    val rincon_uuid: String,
    val zone_name: String,
    val device_id: String? = null,
    val room_id: String? = null,
    val room_name: String? = null,
    val ip_address: String? = null,
    val base_mac: String? = null,
    val sonosnet_bssid: String? = null,
    val is_reachable: Boolean = true,
    val connection_mode: String = "SONOSNET_MODE",
    val ieee_channel: Int? = null,
    val ofdm_ani_level: Int? = null,
    val noise_floor_dbm: Int? = null,
    val phy_error_total: Int? = null,
    val phy_error_rate: Double? = null,
    val designated_root: String? = null,
    val stp_root_port: String? = null,
    val stp_path_cost: Int? = null,
    val group_id: String? = null,
    val coordinator_uuid: String? = null,
    val has_vanished_devices: Boolean = false,
    val is_ghost_group: Boolean = false,
    val master_volume: Int? = null,
    val ping_rtt_ms: Double? = null,
    val bonded_parent_uuid: String? = null
)

@Serializable
data class SonosMeshLinkDto(
    val source_rincon_uuid: String,
    val target_rincon_uuid: String,
    val source_zone_name: String? = null,
    val target_zone_name: String? = null,
    val source_bssid: String? = null,
    val target_bssid: String? = null,
    val channel: Int = 6,
    val from_db: Int,
    val to_db: Int,
    val stp_state: String = "FORWARDING"
)

@Serializable
data class HouseholdSonosSnapshotDto(
    val batch_id: String,
    val captured_at: String,
    val consumer_id: String,
    val designated_stp_root: String,
    val is_root_healthy: Boolean,
    val total_players: Int,
    val reachable_players: Int,
    val ghost_group_count: Int,
    val has_ghost_groups: Boolean,
    val ghost_group_zones: List<String> = emptyList(),
    val players: List<PlayerTelemetryDto> = emptyList(),
    val mesh_links: List<SonosMeshLinkDto> = emptyList()
)

@Serializable
data class PingSweepItemDto(
    val rincon_uuid: String,
    val zone_name: String,
    val room_slug: String? = null,
    val ip_address: String? = null,
    val is_reachable: Boolean = true,
    val ping_rtt_ms: Double,
    val jitter_ms: Double = 0.0,
    val dpc_ducking_risk: Boolean = false
)

@Serializable
data class PingSweepResultDto(
    val swept_at: String,
    val total_probed: Int,
    val reachable_count: Int,
    val max_rtt_ms: Double,
    val avg_rtt_ms: Double,
    val dpc_risk_zones: List<String> = emptyList(),
    val results: List<PingSweepItemDto> = emptyList()
)

@Serializable
data class LiveRfSampleDto(
    val rincon_uuid: String,
    val zone_name: String,
    val room_id: String? = null,
    val ip_address: String? = null,
    val ieee_channel: Int? = null,
    val ofdm_ani_level: Int? = null,
    val noise_floor_dbm: Int? = null,
    val phy_error_total: Int? = null,
    val phy_error_rate: Double,
    val captured_at: String
)

@Serializable
data class LiveRfFrameDto(
    val room_slug: String,
    val interval_sec: Double,
    val consumer_id: String,
    val captured_at: String,
    val samples: List<LiveRfSampleDto> = emptyList()
)
