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


