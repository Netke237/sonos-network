import type {
  ConnectionMode,
  DaemonCollectResult,
  DaemonStatus,
  DeviceRole,
  GhostFlushResult,
  HealthGrade,
  HouseDiagnosticReport,
  HouseholdSonosSnapshot,
  HouseOverview,
  NetworkDevice,
  PingSweepResult,
  Room,
  RoomDiagnosticSummary,
  RoomHistoryResponse,
  SurveyComparisonDelta,
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

export async function fetchHouseDiagnostics(): Promise<HouseDiagnosticReport> {
  const resp = await fetch(`${API_BASE}/api/diagnostics`);
  if (!resp.ok) {
    throw new Error(`Failed to load diagnostics: ${resp.status}`);
  }
  return resp.json();
}

export async function fetchRoomDiagnostics(
  roomSlug: string
): Promise<RoomDiagnosticSummary> {
  const resp = await fetch(`${API_BASE}/api/rooms/${roomSlug}/diagnostics`);
  if (!resp.ok) {
    throw new Error(`Failed to load room diagnostics: ${resp.status}`);
  }
  return resp.json();
}

export async function runPingSweep(): Promise<PingSweepResult> {
  const resp = await fetch(`${API_BASE}/api/actions/ping-sweep`, {
    method: "POST",
  });
  if (!resp.ok) {
    throw new Error(`Failed to run ping sweep: ${resp.status}`);
  }
  return resp.json();
}

export async function fetchSurveyDelta(
  roomSlug: string,
  baselineSlug?: string,
  targetSlug?: string
): Promise<SurveyComparisonDelta> {
  const params = new URLSearchParams();
  if (baselineSlug) params.set("baseline_slug", baselineSlug);
  if (targetSlug) params.set("target_slug", targetSlug);
  const qs = params.toString() ? `?${params.toString()}` : "";
  const resp = await fetch(
    `${API_BASE}/api/rooms/${roomSlug}/surveys/delta${qs}`
  );
  if (!resp.ok) {
    throw new Error(`Failed to load survey delta: ${resp.status}`);
  }
  return resp.json();
}

export async function fetchRoomHistory(
  roomSlug: string,
  range = "24h"
): Promise<RoomHistoryResponse> {
  const resp = await fetch(
    `${API_BASE}/api/rooms/${roomSlug}/history?range=${encodeURIComponent(range)}`
  );
  if (!resp.ok) {
    throw new Error(`Failed to load history for ${roomSlug}: ${resp.status}`);
  }
  return resp.json();
}

export async function fetchDaemonStatus(): Promise<DaemonStatus> {
  const resp = await fetch(`${API_BASE}/api/daemon/status`);
  if (!resp.ok) {
    throw new Error(`Failed to load daemon status: ${resp.status}`);
  }
  return resp.json();
}

export async function triggerDaemonCollect(): Promise<DaemonCollectResult> {
  const resp = await fetch(`${API_BASE}/api/daemon/collect-now`, {
    method: "POST",
  });
  if (!resp.ok) {
    throw new Error(`Failed to trigger daemon collection: ${resp.status}`);
  }
  return resp.json();
}


