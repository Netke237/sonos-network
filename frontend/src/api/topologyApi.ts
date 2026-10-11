import type {
  ConnectionMode,
  DeviceRole,
  GhostFlushResult,
  HealthGrade,
  HouseholdSonosSnapshot,
  HouseOverview,
  NetworkDevice,
  Room,
  SwitchPort,
  TopologyGraphResponse,
  WiFiRoomSurvey,
} from "../types/topology";


const API_BASE =
  (import.meta as unknown as { env?: Record<string, string> }).env
    ?.VITE_API_BASE_URL ?? "http://192.168.55.60:8000";

export async function fetchHouseOverview(
  includeArchived = false
): Promise<HouseOverview> {
  const query = includeArchived ? "?include_archived=true" : "";
  const resp = await fetch(`${API_BASE}/api/overview${query}`);
  if (!resp.ok) {
    throw new Error(`Failed to load overview: ${resp.status}`);
  }
  return resp.json();
}

export async function fetchTopologyGraph(params?: {
  layer?: string;
  floor_slug?: string | null;
  room_slug?: string | null;
  include_blocking?: boolean;
}): Promise<TopologyGraphResponse> {
  const search = new URLSearchParams();
  if (params?.layer) {
    search.set("layer", params.layer);
  }
  if (params?.floor_slug) {
    search.set("floor_slug", params.floor_slug);
  }
  if (params?.room_slug) {
    search.set("room_slug", params.room_slug);
  }
  if (params?.include_blocking !== undefined) {
    search.set("include_blocking", String(params.include_blocking));
  }
  const qs = search.toString() ? `?${search.toString()}` : "";
  const resp = await fetch(`${API_BASE}/api/topology${qs}`);
  if (!resp.ok) {
    throw new Error(`Failed to load topology graph: ${resp.status}`);
  }
  return resp.json();
}

export async function pollLiveSonosNow(): Promise<HouseholdSonosSnapshot> {
  const resp = await fetch(`${API_BASE}/api/actions/poll-now`, {
    method: "POST",
  });
  if (!resp.ok) {
    throw new Error(`Failed to poll Sonos telemetry: ${resp.status}`);
  }
  return resp.json();
}

export async function flushGhostGroups(
  zoneIps?: string[]
): Promise<GhostFlushResult> {
  const resp = await fetch(`${API_BASE}/api/actions/flush-ghost-groups`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(zoneIps ? { zone_ips: zoneIps } : {}),
  });
  if (!resp.ok) {
    throw new Error(`Failed to flush ghost groups: ${resp.status}`);
  }
  return resp.json();
}

export async function createRoom(payload: {
  name: string;
  floor_id: string;
  pos_x: number;
  pos_y: number;
  health_grade: HealthGrade;
  description?: string;
}): Promise<Room> {
  const resp = await fetch(`${API_BASE}/api/rooms`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    throw new Error(`Failed to create room: ${resp.status}`);
  }
  return resp.json();
}

export async function updateRoom(
  roomId: string,
  payload: Partial<{
    name: string;
    floor_id: string;
    pos_x: number;
    pos_y: number;
    health_grade: HealthGrade;
    description: string;
  }>
): Promise<Room> {
  const resp = await fetch(`${API_BASE}/api/rooms/${roomId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    throw new Error(`Failed to update room: ${resp.status}`);
  }
  return resp.json();
}

export async function archiveRoom(roomId: string): Promise<Room> {
  const resp = await fetch(`${API_BASE}/api/rooms/${roomId}`, {
    method: "DELETE",
  });
  if (!resp.ok) {
    throw new Error(`Failed to archive room: ${resp.status}`);
  }
  return resp.json();
}

export async function createDevice(payload: {
  name: string;
  device_role: DeviceRole;
  model_name: string;
  ip_address?: string;
  connection_mode?: ConnectionMode;
  health_grade: HealthGrade;
  room_id?: string;
}): Promise<NetworkDevice> {
  const resp = await fetch(`${API_BASE}/api/devices`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    throw new Error(`Failed to create device: ${resp.status}`);
  }
  return resp.json();
}

export async function archiveDevice(deviceId: string): Promise<NetworkDevice> {
  const resp = await fetch(`${API_BASE}/api/devices/${deviceId}`, {
    method: "DELETE",
  });
  if (!resp.ok) {
    throw new Error(`Failed to archive device: ${resp.status}`);
  }
  return resp.json();
}

export async function createSwitchPort(payload: {
  port_number: number;
  pvid: number;
  untagged_vlans: string;
  tagged_vlans: string;
  patched_room_id?: string;
  connected_device_label?: string;
}): Promise<SwitchPort> {
  const resp = await fetch(`${API_BASE}/api/switch-ports`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    throw new Error(`Failed to create switch port: ${resp.status}`);
  }
  return resp.json();
}

export async function fetchRoomSurveys(
  roomSlug: string
): Promise<WiFiRoomSurvey[]> {
  const resp = await fetch(`${API_BASE}/api/rooms/${roomSlug}/surveys`);
  if (!resp.ok) {
    throw new Error(`Failed to fetch surveys for ${roomSlug}: ${resp.status}`);
  }
  return resp.json();
}

export async function createRoomSurvey(
  roomSlug: string,
  payload: {
    label?: string;
    trigger_mode?: string;
    connected_bssid?: string;
    link_speed_mbps?: number;
    readings?: Array<{
      bssid: string;
      ssid?: string;
      band: string;
      channel: number;
      center_channel?: number;
      width_mhz?: number;
      rssi_dbm: number;
    }>;
  }
): Promise<WiFiRoomSurvey> {
  const resp = await fetch(`${API_BASE}/api/rooms/${roomSlug}/surveys`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    throw new Error(`Failed to create survey for ${roomSlug}: ${resp.status}`);
  }
  return resp.json();
}

