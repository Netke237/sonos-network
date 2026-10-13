export type HealthGrade = "EXCELLENT" | "GOOD" | "MARGINAL" | "CRITICAL";

export type DeviceRole =
  | "SONOS_PLAYER"
  | "WIFI_AP"
  | "SWITCH"
  | "ROUTER"
  | "CLIENT_DEVICE"
  | "EMI_SOURCE";

export type ConnectionMode =
  | "ETHERNET_ROOT"
  | "ETHERNET_NODE"
  | "SONOSNET_MODE"
  | "STATION_MODE"
  | "HT_SATELLITE";

export interface Floor {
  id: string;
  slug: string;
  name: string;
  level_order: number;
  is_archived: boolean;
}

export interface SwitchPort {
  id: string;
  port_number: number;
  switch_name: string;
  switch_ip: string;
  pvid: number;
  untagged_vlans: string;
  tagged_vlans: string;
  bpdu_policy: string;
  loop_detection_disabled: boolean;
  patched_room_id?: string | null;
  connected_device_label?: string | null;
  is_archived: boolean;
}

export interface NetworkDevice {
  id: string;
  slug: string;
  name: string;
  device_role: DeviceRole;
  model_name: string;
  ip_address?: string | null;
  base_mac?: string | null;
  sonosnet_bssid?: string | null;
  rincon_uuid?: string | null;
  connection_mode?: ConnectionMode | null;
  health_grade: HealthGrade;
  ofdm_ani_level?: number | null;
  noise_floor_dbm?: number | null;
  phy_error_total?: number | null;
  phy_error_rate?: number | null;
  designated_root?: string | null;
  stp_path_cost?: number | null;
  group_id?: string | null;
  coordinator_uuid?: string | null;
  is_ghost_group?: boolean;
  master_volume?: number | null;
  ping_rtt_ms?: number | null;
  ieee_channel?: number | null;
  bonded_parent_uuid?: string | null;
  room_id?: string | null;
  switch_port_id?: string | null;
  notes?: string | null;
  is_archived: boolean;
}

export interface Room {
  id: string;
  slug: string;
  name: string;
  floor_id: string;
  pos_x: number;
  pos_y: number;
  health_grade: HealthGrade;
  best_5ghz_rssi_dbm?: number | null;
  best_24ghz_rssi_dbm?: number | null;
  description?: string | null;
  is_archived: boolean;
}

export type BssidClassification =
  | "OWN_MANAGED_AP"
  | "SONOSNET_MESH"
  | "ROGUE_OWN_RADIO"
  | "NEIGHBOR_WIFI";

export interface BssidReading {
  id?: string | null;
  bssid: string;
  ssid?: string | null;
  band: string;
  channel: number;
  center_channel: number;
  width_mhz: number;
  rssi_dbm: number;
  classification: BssidClassification;
  ap_device_slug?: string | null;
  ap_name?: string | null;
  is_connected?: boolean;
}

export interface WiFiRoomSurvey {
  id?: string | null;
  survey_slug: string;
  room_id?: string | null;
  room_slug: string;
  room_name: string;
  label: string;
  trigger_mode: string;
  captured_at: string;
  connected_bssid?: string | null;
  connected_ssid?: string | null;
  link_speed_mbps?: number | null;
  frequency_mhz?: number | null;
  best_5ghz_dbm?: number | null;
  best_24ghz_dbm?: number | null;
  best_ap_slug?: string | null;
  best_ap_name?: string | null;
  rogue_count: number;
  neighbor_count: number;
  grade_5ghz: HealthGrade;
  grade_24ghz: HealthGrade;
  wifi_health_grade: HealthGrade;
  notes?: string | null;
  readings: BssidReading[];
}

export interface RoomMatrixItem extends Room {
  best_5ghz_dbm?: number | null;
  best_24ghz_dbm?: number | null;
  best_ap_name?: string | null;
  link_speed_mbps?: number | null;
  rogue_count?: number;
  neighbor_count?: number;
  wifi_health_grade?: HealthGrade;
  sonos_health_grade?: HealthGrade;
  wired_health_grade?: HealthGrade;
  active_diagnostics_count?: number;
  top_diagnostic_title?: string | null;
  floor_slug?: string | null;
  floor_name?: string | null;
  devices: NetworkDevice[];
  switch_ports: SwitchPort[];
}


export interface FloorMatrixItem extends Floor {
  rooms: RoomMatrixItem[];
}

export interface HouseOverview {
  total_floors: number;
  total_rooms: number;
  total_sonos_players: number;
  total_wifi_aps: number;
  total_switch_ports: number;
  designated_stp_root: string;
  ghost_group_count?: number;
  has_ghost_groups?: boolean;
  ghost_group_zones?: string[];
  active_diagnostics_count?: number;
  critical_diagnostics_count?: number;
  latest_sonos_batch_id?: string | null;
  latest_sonos_captured_at?: string | null;
  floors: FloorMatrixItem[];
}

export interface GhostFlushZoneResult {
  zone_name: string;
  rincon_uuid: string;
  ip_address: string;
  previous_group_id?: string | null;
  new_group_id: string;
  status: string;
}

export interface GhostFlushResult {
  flushed_count: number;
  flushed_zones: string[];
  results: GhostFlushZoneResult[];
  captured_at: string;
}

export interface HouseholdSonosSnapshot {
  batch_id: string;
  captured_at: string;
  consumer_id: string;
  designated_stp_root: string;
  is_root_healthy: boolean;
  total_players: number;
  reachable_players: number;
  ghost_group_count: number;
  has_ghost_groups: boolean;
  ghost_group_zones: string[];
  players: unknown[];
  mesh_links: unknown[];
}

export type EdgeLayer = "WIRED_LAN" | "WIFI_INFRA" | "SONOS_MESH";

export type TopologyLayerFilter =
  | "ALL"
  | "WIFI_VLAN"
  | "SONOS_STP"
  | "WIRED_LAN"
  | "WIFI_INFRA"
  | "SONOS_MESH";

export interface TopologyNode {
  id: string;
  device_id?: string | null;
  slug: string;
  name: string;
  device_role: DeviceRole;
  model_name: string;
  ip_address?: string | null;
  base_mac?: string | null;
  rincon_uuid?: string | null;
  room_id?: string | null;
  room_slug?: string | null;
  room_name?: string | null;
  floor_id?: string | null;
  floor_slug?: string | null;
  floor_name?: string | null;
  connection_mode?: ConnectionMode | null;
  health_grade: HealthGrade;
  ofdm_ani_level?: number | null;
  noise_floor_dbm?: number | null;
  phy_error_rate?: number | null;
  stp_path_cost?: number | null;
  designated_root?: string | null;
  is_stp_root?: boolean;
  is_ghost_group?: boolean;
  rssi_dbm?: number | null;
  ap_channels?: string | null;
  switch_port_number?: number | null;
  x: number;
  y: number;
  pos_x: number;
  pos_y: number;
}

export interface DeviceConnectionEdge {
  id: string;
  layer: EdgeLayer;
  source: string;
  source_id: string;
  source_slug: string;
  source_name: string;
  target: string;
  target_id: string;
  target_slug: string;
  target_name: string;
  label: string;
  is_forwarding: boolean;
  line_style: "solid" | "dashed" | string;
  stp_state?: string | null;
  band?: string | null;
  channel?: number | null;
  from_db?: number | null;
  to_db?: number | null;
  rssi_dbm?: number | null;
  link_speed_mbps?: number | null;
  port_number?: number | null;
  vlan_label?: string | null;
  health_grade: HealthGrade;
}

export interface TopologyGraphResponse {
  layer_filter: string;
  floor_slug?: string | null;
  room_slug?: string | null;
  include_blocking: boolean;
  designated_stp_root: string;
  total_nodes: number;
  total_edges: number;
  nodes: TopologyNode[];
  edges: DeviceConnectionEdge[];
}

export interface SolutionProposal {
  id: string;
  rank: number;
  rule_code: string;
  title: string;
  description: string;
  action_type: "ONE_CLICK" | "GUIDED_PHYSICAL" | string;
  one_click_action?: string | null;
  requires_sonosnet_disable_guard: boolean;
  stp_guard_warning?: string | null;
  target_room_slug?: string | null;
  target_device_name?: string | null;
}

export interface RoomDiagnostic {
  id: string;
  room_slug: string;
  room_name: string;
  layer: "WIFI" | "SONOS" | "WIRED_VLAN" | string;
  severity: HealthGrade;
  rule_code: string;
  title: string;
  summary: string;
  evidence: Record<string, unknown>;
  affected_devices: string[];
  solution_proposals: SolutionProposal[];
}

export interface WiFiPillarSummary {
  health_grade: HealthGrade;
  best_5ghz_dbm?: number | null;
  best_24ghz_dbm?: number | null;
  covering_ap_name?: string | null;
  covering_ap_slug?: string | null;
  link_speed_mbps?: number | null;
  channel_summary?: string;
  summary_note?: string;
  rogue_count: number;
  neighbor_count: number;
  co_channel_neighbors: string[];
  has_channel_6_high_power_wifi: boolean;
}

export interface PlayerDiagnosticItem {
  rincon_uuid: string;
  zone_name: string;
  ip_address?: string | null;
  connection_mode: ConnectionMode | string;
  ofdm_ani_level?: number | null;
  noise_floor_dbm?: number | null;
  phy_error_rate?: number | null;
  designated_root?: string | null;
  stp_path_cost?: number | null;
  active_forwarding_snr_db?: number | null;
  ping_rtt_ms?: number | null;
  group_id?: string | null;
  is_ghost_group: boolean;
  rf_grade: HealthGrade;
  link_grade: HealthGrade;
  overall_grade: HealthGrade;
  grading_rationale: string;
}

export interface SonosPillarSummary {
  health_grade: HealthGrade;
  player_count?: number;
  total_players?: number;
  sonosnet_player_count?: number;
  station_mode_player_count?: number;
  ht_satellite_player_count?: number;
  wired_player_count?: number;
  designated_stp_root: string;
  is_stp_root_healthy: boolean;
  max_phy_error_rate?: number | null;
  max_stp_path_cost?: number | null;
  ghost_group_zones?: string[];
  players: PlayerDiagnosticItem[];
  summary_note?: string;
}

export interface WiredPillarSummary {
  health_grade: HealthGrade;
  has_vlan10_wall_jack: boolean;
  port_numbers: number[];
  pvid_list?: number[];
  bpdu_policy?: string;
  stp_root_guard_required: boolean;
  stp_root_guard_note?: string;
  stp_guard_note?: string;
}

export interface RoomDiagnosticSummary {
  room_id: string;
  room_slug: string;
  room_name: string;
  floor_slug?: string | null;
  floor_name?: string | null;
  health_grade: HealthGrade;
  active_diagnostics_count: number;
  critical_count: number;
  marginal_count: number;
  top_diagnostic_title?: string | null;
  wifi_pillar: WiFiPillarSummary;
  sonos_pillar: SonosPillarSummary;
  wired_pillar: WiredPillarSummary;
  diagnostics: RoomDiagnostic[];
  solution_proposals: SolutionProposal[];
}

export interface HouseDiagnosticReport {
  evaluated_at: string;
  overall_health_grade: HealthGrade;
  designated_stp_root: string;
  is_stp_root_healthy: boolean;
  sonosnet_wireless_player_count: number;
  total_diagnostics_count: number;
  critical_diagnostics_count: number;
  marginal_diagnostics_count: number;
  house_diagnostics: RoomDiagnostic[];
  rooms: RoomDiagnosticSummary[];
}

export interface PingSweepItem {
  rincon_uuid: string;
  zone_name: string;
  room_slug?: string | null;
  ip_address?: string | null;
  is_reachable: boolean;
  ping_rtt_ms: number;
  jitter_ms: number;
  dpc_ducking_risk: boolean;
}

export interface PingSweepResult {
  swept_at: string;
  total_probed: number;
  reachable_count: number;
  max_rtt_ms: number;
  avg_rtt_ms: number;
  dpc_risk_zones: string[];
  results: PingSweepItem[];
}

export interface BssidDeltaItem {
  bssid: string;
  ssid?: string | null;
  band: string;
  channel: number;
  classification: string;
  baseline_rssi_dbm?: number | null;
  target_rssi_dbm?: number | null;
  delta_rssi_dbm?: number | null;
  is_new: boolean;
  is_vanished: boolean;
}

export interface SurveyComparisonDelta {
  room_id: string;
  room_slug: string;
  room_name: string;
  baseline_survey_id: string;
  baseline_survey_slug: string;
  baseline_label: string;
  baseline_captured_at: string;
  target_survey_id: string;
  target_survey_slug: string;
  target_label: string;
  target_captured_at: string;
  baseline_5ghz_dbm?: number | null;
  target_5ghz_dbm?: number | null;
  delta_5ghz_dbm?: number | null;
  baseline_24ghz_dbm?: number | null;
  target_24ghz_dbm?: number | null;
  delta_24ghz_dbm?: number | null;
  baseline_link_speed_mbps?: number | null;
  target_link_speed_mbps?: number | null;
  delta_link_speed_mbps?: number | null;
  baseline_best_ap_name?: string | null;
  target_best_ap_name?: string | null;
  baseline_wifi_health_grade: HealthGrade | string;
  target_wifi_health_grade: HealthGrade | string;
  wifi_improved: boolean;
  baseline_ofdm_ani_level?: number | null;
  target_ofdm_ani_level?: number | null;
  delta_ofdm_ani_level?: number | null;
  baseline_phy_error_rate?: number | null;
  target_phy_error_rate?: number | null;
  delta_phy_error_rate?: number | null;
  baseline_stp_path_cost?: number | null;
  target_stp_path_cost?: number | null;
  delta_stp_path_cost?: number | null;
  baseline_ping_rtt_ms?: number | null;
  target_ping_rtt_ms?: number | null;
  delta_ping_rtt_ms?: number | null;
  sonos_improved: boolean;
  overall_improved: boolean;
  summary_narrative: string;
  bssid_deltas: BssidDeltaItem[];
}

export interface LiveRfSample {
  rincon_uuid: string;
  zone_name: string;
  room_id?: string | null;
  ip_address?: string | null;
  ieee_channel?: number | null;
  ofdm_ani_level?: number | null;
  noise_floor_dbm?: number | null;
  phy_error_total?: number | null;
  phy_error_rate: number;
  captured_at?: string;
}

export interface LiveRfFrame {
  timestamp: string;
  consumer_id: string;
  room_slug: string;
  samples: LiveRfSample[];
}

export interface PlayerHistorySample {
  rincon_uuid: string;
  zone_name: string;
  connection_mode: string;
  ofdm_ani_level?: number | null;
  noise_floor_dbm?: number | null;
  phy_error_rate?: number | null;
  ping_rtt_ms?: number | null;
  stp_path_cost?: number | null;
}

export interface RoomHistoryPoint {
  timestamp: string;
  batch_id?: string | null;
  consumer_id?: string | null;
  peak_ofdm_ani_level?: number | null;
  total_phy_error_rate?: number | null;
  avg_ping_rtt_ms?: number | null;
  best_5ghz_dbm?: number | null;
  best_24ghz_dbm?: number | null;
  link_speed_mbps?: number | null;
  worst_stp_path_cost?: number | null;
  health_grade: string;
  players: PlayerHistorySample[];
}

export interface RoomHistoryRollupBucket {
  bucket_key: string;
  bucket_label: string;
  granularity: string;
  start_date: string;
  end_date: string;
  sample_count: number;
  avg_ofdm_ani_level?: number | null;
  peak_ofdm_ani_level?: number | null;
  avg_phy_error_rate?: number | null;
  peak_phy_error_rate?: number | null;
  avg_ping_rtt_ms?: number | null;
  worst_stp_path_cost?: number | null;
  health_grade: string;
}

export interface RoomHistoryResponse {
  room_id: string;
  room_slug: string;
  room_name: string;
  time_range: string;
  granularity: string;
  total_samples: number;
  peak_ani?: number | null;
  avg_phy_error_rate?: number | null;
  avg_ping_rtt_ms?: number | null;
  summary: string;
  samples: RoomHistoryPoint[];
  rollup_buckets: RoomHistoryRollupBucket[];
}

export interface DaemonStatus {
  is_running: boolean;
  interval_sec: number;
  retention_days: number;
  last_cycle_at?: string | null;
  total_cycles: number;
  last_error?: string | null;
}

export interface DaemonCollectResult {
  status: string;
  batch_id: string;
  total_players: number;
  pruned_count: number;
  executed_at: string;
}




