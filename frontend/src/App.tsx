import React, { useEffect, useState } from "react";
import {
  archiveDevice,
  archiveRoom,
  createDevice,
  createRoom,
  createSwitchPort,
  fetchHouseOverview,
  flushGhostGroups,
  pollLiveSonosNow,
} from "./api/topologyApi";
import type {
  ConnectionMode,
  DeviceRole,
  FloorMatrixItem,
  HealthGrade,
  HouseOverview,
  RoomMatrixItem,
} from "./types/topology";

const GRADE_COLORS: Record<HealthGrade, { bg: string; text: string; border: string }> = {
  EXCELLENT: { bg: "#064e3b", text: "#6ee7b7", border: "#059669" },
  GOOD: { bg: "#14532d", text: "#86efac", border: "#16a34a" },
  MARGINAL: { bg: "#713f12", text: "#fde047", border: "#ca8a04" },
  CRITICAL: { bg: "#7f1d1d", text: "#fca5a5", border: "#dc2626" },
};

export default function App() {
  const [overview, setOverview] = useState<HouseOverview | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [includeArchived, setIncludeArchived] = useState<boolean>(false);
  const [crudOpen, setCrudOpen] = useState<boolean>(false);
  const [selectedRoom, setSelectedRoom] = useState<RoomMatrixItem | null>(null);
  const [actionBanner, setActionBanner] = useState<string | null>(null);

  // Room Form State
  const [roomName, setRoomName] = useState<string>("");
  const [roomFloorId, setRoomFloorId] = useState<string>("");
  const [roomPosX, setRoomPosX] = useState<number>(200);
  const [roomPosY, setRoomPosY] = useState<number>(200);
  const [roomGrade, setRoomGrade] = useState<HealthGrade>("GOOD");

  // Device Form State
  const [devName, setDevName] = useState<string>("");
  const [devRole, setDevRole] = useState<DeviceRole>("SONOS_PLAYER");
  const [devModel, setDevModel] = useState<string>("SYMFONISK Bookshelf");
  const [devIp, setDevIp] = useState<string>("");
  const [devMode, setDevMode] = useState<ConnectionMode>("SONOSNET_MODE");
  const [devRoomId, setDevRoomId] = useState<string>("");

  // SwitchPort Form State
  const [portNumber, setPortNumber] = useState<number>(9);
  const [portPvid, setPortPvid] = useState<number>(10);
  const [portLabel, setPortLabel] = useState<string>("");

  const loadData = async (showArchived = includeArchived) => {
    try {
      setLoading(true);
      const data = await fetchHouseOverview(showArchived);
      setOverview(data);
      if (data.floors.length > 0 && !roomFloorId) {
        setRoomFloorId(data.floors[0].id);
        const firstRoom = data.floors[0].rooms[0];
        if (firstRoom && !devRoomId) {
          setDevRoomId(firstRoom.id);
        }
      }
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load house overview");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadData(includeArchived);
  }, [includeArchived]);

  const handlePollSonosNow = async () => {
    try {
      const snap = await pollLiveSonosNow();
      setActionBanner(
        `Polled ${snap.reachable_players}/${snap.total_players} Sonos players (${snap.batch_id})`
      );
      await loadData(includeArchived);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to poll Sonos");
    }
  };

  const handleFlushGhostGroups = async () => {
    try {
      const res = await flushGhostGroups();
      setActionBanner(
        `Flushed ${res.flushed_count} Ghost Group(s): ${
          res.flushed_zones.join(", ") || "All zones clean"
        }`
      );
      await loadData(includeArchived);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to flush ghost groups");
    }
  };

  const handleCreateRoom = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!roomName.trim()) return;
    await createRoom({
      name: roomName.trim(),
      floor_id: roomFloorId || overview?.floors[0]?.id || "",
      pos_x: Number(roomPosX),
      pos_y: Number(roomPosY),
      health_grade: roomGrade,
    });
    setRoomName("");
    await loadData(includeArchived);
  };

  const handleCreateDevice = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!devName.trim()) return;
    await createDevice({
      name: devName.trim(),
      device_role: devRole,
      model_name: devModel,
      ip_address: devIp || undefined,
      connection_mode: devRole === "SONOS_PLAYER" ? devMode : undefined,
      health_grade: "GOOD",
      room_id: devRoomId || undefined,
    });
    setDevName("");
    setDevIp("");
    await loadData(includeArchived);
  };

  const handleCreatePort = async (e: React.FormEvent) => {
    e.preventDefault();
    await createSwitchPort({
      port_number: Number(portNumber),
      pvid: Number(portPvid),
      untagged_vlans: String(portPvid),
      tagged_vlans: "",
      patched_room_id: devRoomId || undefined,
      connected_device_label: portLabel || undefined,
    });
    setPortLabel("");
    await loadData(includeArchived);
  };

  const handleArchiveRoom = async (roomId: string) => {
    await archiveRoom(roomId);
    await loadData(includeArchived);
  };

  const handleArchiveDevice = async (deviceId: string) => {
    await archiveDevice(deviceId);
    await loadData(includeArchived);
  };

  const sortedFloors: FloorMatrixItem[] = overview
    ? [...overview.floors].sort((a, b) => b.level_order - a.level_order)
    : [];

  const allRooms: RoomMatrixItem[] = sortedFloors.flatMap((f) => f.rooms);

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "#0f172a",
        color: "#f8fafc",
        fontFamily: "system-ui, -apple-system, sans-serif",
        padding: "24px",
      }}
    >
      {/* Top Header */}
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderBottom: "1px solid #334155",
          paddingBottom: "16px",
          marginBottom: "24px",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <div>
          <h1 style={{ margin: 0, fontSize: "1.5rem", fontWeight: 700 }}>
            Home Wi-Fi &amp; Sonos Network Intelligence Platform
          </h1>
          <p style={{ margin: "4px 0 0", color: "#94a3b8", fontSize: "0.9rem" }}>
            Designated STP Root:{" "}
            <strong style={{ color: "#38bdf8" }}>
              {overview?.designated_stp_root ?? "9000.542a1b63fe6e"}
            </strong>
          </p>
        </div>

        <div style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              fontSize: "0.85rem",
              color: "#cbd5e1",
              cursor: "pointer",
            }}
          >
            <input
              type="checkbox"
              checked={includeArchived}
              onChange={(e) => setIncludeArchived(e.target.checked)}
            />
            Show Archived
          </label>
          <button
            type="button"
            onClick={() => void handlePollSonosNow()}
            style={{
              backgroundColor: "#0d9488",
              color: "#ffffff",
              border: "none",
              borderRadius: "6px",
              padding: "8px 14px",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Poll Live Sonos Now
          </button>
          <button
            type="button"
            onClick={() => void handleFlushGhostGroups()}
            style={{
              backgroundColor: "#dc2626",
              color: "#ffffff",
              border: "none",
              borderRadius: "6px",
              padding: "8px 14px",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Flush Ghost Groups
          </button>
          <button
            type="button"
            onClick={() => setCrudOpen((prev) => !prev)}
            style={{
              backgroundColor: "#2563eb",
              color: "#ffffff",
              border: "none",
              borderRadius: "6px",
              padding: "8px 14px",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Manage Inventory / Add Room / Device
          </button>
        </div>
      </header>

      {/* Ghost Group & Action Status Banner */}
      {(overview?.has_ghost_groups || actionBanner) && (
        <div
          role="status"
          style={{
            backgroundColor: overview?.has_ghost_groups ? "#7f1d1d" : "#064e3b",
            border: `1px solid ${overview?.has_ghost_groups ? "#ef4444" : "#10b981"}`,
            color: "#f8fafc",
            borderRadius: "8px",
            padding: "10px 16px",
            marginBottom: "20px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "8px",
          }}
        >
          <div>
            {overview?.has_ghost_groups && (
              <span style={{ marginRight: "12px", fontWeight: 700, color: "#fca5a5" }}>
                Active Ghost Group Detected ({overview.ghost_group_count}):{" "}
                {overview.ghost_group_zones?.join(", ")}
              </span>
            )}
            {actionBanner && <span>{actionBanner}</span>}
          </div>
        </div>
      )}


      {/* Summary KPI Strip */}
      {overview && (
        <section
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            gap: "12px",
            marginBottom: "24px",
          }}
        >
          <div style={{ background: "#1e293b", padding: "12px 16px", borderRadius: "8px" }}>
            <div style={{ color: "#94a3b8", fontSize: "0.75rem" }}>FLOORS</div>
            <div style={{ fontSize: "1.4rem", fontWeight: 700 }}>{overview.total_floors}</div>
          </div>
          <div style={{ background: "#1e293b", padding: "12px 16px", borderRadius: "8px" }}>
            <div style={{ color: "#94a3b8", fontSize: "0.75rem" }}>PHYSICAL ROOMS</div>
            <div style={{ fontSize: "1.4rem", fontWeight: 700 }}>{overview.total_rooms}</div>
          </div>
          <div style={{ background: "#1e293b", padding: "12px 16px", borderRadius: "8px" }}>
            <div style={{ color: "#94a3b8", fontSize: "0.75rem" }}>SONOS PLAYERS</div>
            <div style={{ fontSize: "1.4rem", fontWeight: 700 }}>
              {overview.total_sonos_players}
            </div>
          </div>
          <div style={{ background: "#1e293b", padding: "12px 16px", borderRadius: "8px" }}>
            <div style={{ color: "#94a3b8", fontSize: "0.75rem" }}>MANAGED WIFI APS</div>
            <div style={{ fontSize: "1.4rem", fontWeight: 700 }}>{overview.total_wifi_aps}</div>
          </div>
          <div style={{ background: "#1e293b", padding: "12px 16px", borderRadius: "8px" }}>
            <div style={{ color: "#94a3b8", fontSize: "0.75rem" }}>GS316EP SWITCH PORTS</div>
            <div style={{ fontSize: "1.4rem", fontWeight: 700 }}>
              {overview.total_switch_ports}
            </div>
          </div>
        </section>
      )}

      {/* CRUD Drawer / Modal */}
      {crudOpen && (
        <section
          aria-label="Room and Device CRUD Manager"
          style={{
            backgroundColor: "#1e293b",
            border: "1px solid #475569",
            borderRadius: "10px",
            padding: "20px",
            marginBottom: "24px",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "20px",
          }}
        >
          {/* Add Room Form */}
          <form onSubmit={handleCreateRoom}>
            <h3 style={{ marginTop: 0, fontSize: "1rem", color: "#38bdf8" }}>
              Add Physical Room
            </h3>
            <div style={{ marginBottom: "10px" }}>
              <label style={{ display: "block", fontSize: "0.8rem", marginBottom: "4px" }}>
                Room Name
                <input
                  type="text"
                  value={roomName}
                  onChange={(e) => setRoomName(e.target.value)}
                  placeholder="e.g. Terrasse"
                  style={{
                    width: "100%",
                    padding: "6px",
                    marginTop: "4px",
                    borderRadius: "4px",
                    border: "1px solid #475569",
                    background: "#0f172a",
                    color: "#f8fafc",
                  }}
                />
              </label>
            </div>
            <div style={{ marginBottom: "10px" }}>
              <label style={{ display: "block", fontSize: "0.8rem", marginBottom: "4px" }}>
                Floor
                <select
                  value={roomFloorId}
                  onChange={(e) => setRoomFloorId(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "6px",
                    marginTop: "4px",
                    borderRadius: "4px",
                    border: "1px solid #475569",
                    background: "#0f172a",
                    color: "#f8fafc",
                  }}
                >
                  {sortedFloors.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div style={{ display: "flex", gap: "8px", marginBottom: "10px" }}>
              <label style={{ flex: 1, fontSize: "0.8rem" }}>
                Pos X
                <input
                  type="number"
                  value={roomPosX}
                  onChange={(e) => setRoomPosX(Number(e.target.value))}
                  style={{
                    width: "100%",
                    padding: "6px",
                    marginTop: "4px",
                    background: "#0f172a",
                    color: "#f8fafc",
                    border: "1px solid #475569",
                  }}
                />
              </label>
              <label style={{ flex: 1, fontSize: "0.8rem" }}>
                Pos Y
                <input
                  type="number"
                  value={roomPosY}
                  onChange={(e) => setRoomPosY(Number(e.target.value))}
                  style={{
                    width: "100%",
                    padding: "6px",
                    marginTop: "4px",
                    background: "#0f172a",
                    color: "#f8fafc",
                    border: "1px solid #475569",
                  }}
                />
              </label>
            </div>
            <div style={{ marginBottom: "10px" }}>
              <label style={{ display: "block", fontSize: "0.8rem" }}>
                Initial Health Grade
                <select
                  value={roomGrade}
                  onChange={(e) => setRoomGrade(e.target.value as HealthGrade)}
                  style={{
                    width: "100%",
                    padding: "6px",
                    marginTop: "4px",
                    background: "#0f172a",
                    color: "#f8fafc",
                    border: "1px solid #475569",
                  }}
                >
                  <option value="EXCELLENT">EXCELLENT</option>
                  <option value="GOOD">GOOD</option>
                  <option value="MARGINAL">MARGINAL</option>
                  <option value="CRITICAL">CRITICAL</option>
                </select>
              </label>
            </div>
            <button
              type="submit"
              style={{
                backgroundColor: "#059669",
                color: "#fff",
                border: "none",
                borderRadius: "4px",
                padding: "8px 12px",
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              Save Room
            </button>
          </form>

          {/* Add NetworkDevice Form */}
          <form onSubmit={handleCreateDevice}>
            <h3 style={{ marginTop: 0, fontSize: "1rem", color: "#38bdf8" }}>
              Add NetworkDevice
            </h3>
            <div style={{ marginBottom: "10px" }}>
              <label style={{ display: "block", fontSize: "0.8rem" }}>
                Device Name
                <input
                  type="text"
                  value={devName}
                  onChange={(e) => setDevName(e.target.value)}
                  placeholder="e.g. Terrasse Move"
                  style={{
                    width: "100%",
                    padding: "6px",
                    marginTop: "4px",
                    background: "#0f172a",
                    color: "#f8fafc",
                    border: "1px solid #475569",
                  }}
                />
              </label>
            </div>
            <div style={{ marginBottom: "10px" }}>
              <label style={{ display: "block", fontSize: "0.8rem" }}>
                Device Role
                <select
                  value={devRole}
                  onChange={(e) => setDevRole(e.target.value as DeviceRole)}
                  style={{
                    width: "100%",
                    padding: "6px",
                    marginTop: "4px",
                    background: "#0f172a",
                    color: "#f8fafc",
                    border: "1px solid #475569",
                  }}
                >
                  <option value="SONOS_PLAYER">SONOS_PLAYER</option>
                  <option value="WIFI_AP">WIFI_AP</option>
                  <option value="SWITCH">SWITCH</option>
                  <option value="ROUTER">ROUTER</option>
                  <option value="CLIENT_DEVICE">CLIENT_DEVICE</option>
                  <option value="EMI_SOURCE">EMI_SOURCE</option>
                </select>
              </label>
            </div>
            <div style={{ display: "flex", gap: "8px", marginBottom: "10px" }}>
              <label style={{ flex: 1, fontSize: "0.8rem" }}>
                Model
                <input
                  type="text"
                  value={devModel}
                  onChange={(e) => setDevModel(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "6px",
                    marginTop: "4px",
                    background: "#0f172a",
                    color: "#f8fafc",
                    border: "1px solid #475569",
                  }}
                />
              </label>
              <label style={{ flex: 1, fontSize: "0.8rem" }}>
                IP Address
                <input
                  type="text"
                  value={devIp}
                  onChange={(e) => setDevIp(e.target.value)}
                  placeholder="192.168.10.x"
                  style={{
                    width: "100%",
                    padding: "6px",
                    marginTop: "4px",
                    background: "#0f172a",
                    color: "#f8fafc",
                    border: "1px solid #475569",
                  }}
                />
              </label>
            </div>
            <div style={{ display: "flex", gap: "8px", marginBottom: "10px" }}>
              <label style={{ flex: 1, fontSize: "0.8rem" }}>
                Connection Mode
                <select
                  value={devMode}
                  onChange={(e) => setDevMode(e.target.value as ConnectionMode)}
                  style={{
                    width: "100%",
                    padding: "6px",
                    marginTop: "4px",
                    background: "#0f172a",
                    color: "#f8fafc",
                    border: "1px solid #475569",
                  }}
                >
                  <option value="SONOSNET_MODE">SONOSNET_MODE</option>
                  <option value="STATION_MODE">STATION_MODE</option>
                  <option value="ETHERNET_ROOT">ETHERNET_ROOT</option>
                  <option value="ETHERNET_NODE">ETHERNET_NODE</option>
                  <option value="HT_SATELLITE">HT_SATELLITE</option>
                </select>
              </label>
              <label style={{ flex: 1, fontSize: "0.8rem" }}>
                Assigned Room
                <select
                  value={devRoomId}
                  onChange={(e) => setDevRoomId(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "6px",
                    marginTop: "4px",
                    background: "#0f172a",
                    color: "#f8fafc",
                    border: "1px solid #475569",
                  }}
                >
                  {allRooms.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <button
              type="submit"
              style={{
                backgroundColor: "#059669",
                color: "#fff",
                border: "none",
                borderRadius: "4px",
                padding: "8px 12px",
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              Save Device
            </button>
          </form>

          {/* Add SwitchPort Form */}
          <form onSubmit={handleCreatePort}>
            <h3 style={{ marginTop: 0, fontSize: "1rem", color: "#38bdf8" }}>
              Add SwitchPort Mapping
            </h3>
            <div style={{ display: "flex", gap: "8px", marginBottom: "10px" }}>
              <label style={{ flex: 1, fontSize: "0.8rem" }}>
                Port # (1-16)
                <input
                  type="number"
                  value={portNumber}
                  onChange={(e) => setPortNumber(Number(e.target.value))}
                  style={{
                    width: "100%",
                    padding: "6px",
                    marginTop: "4px",
                    background: "#0f172a",
                    color: "#f8fafc",
                    border: "1px solid #475569",
                  }}
                />
              </label>
              <label style={{ flex: 1, fontSize: "0.8rem" }}>
                PVID VLAN
                <input
                  type="number"
                  value={portPvid}
                  onChange={(e) => setPortPvid(Number(e.target.value))}
                  style={{
                    width: "100%",
                    padding: "6px",
                    marginTop: "4px",
                    background: "#0f172a",
                    color: "#f8fafc",
                    border: "1px solid #475569",
                  }}
                />
              </label>
            </div>
            <div style={{ marginBottom: "10px" }}>
              <label style={{ display: "block", fontSize: "0.8rem" }}>
                Wall Jack / Endpoint Label
                <input
                  type="text"
                  value={portLabel}
                  onChange={(e) => setPortLabel(e.target.value)}
                  placeholder="e.g. Guest Room Wall Jack"
                  style={{
                    width: "100%",
                    padding: "6px",
                    marginTop: "4px",
                    background: "#0f172a",
                    color: "#f8fafc",
                    border: "1px solid #475569",
                  }}
                />
              </label>
            </div>
            <button
              type="submit"
              style={{
                backgroundColor: "#059669",
                color: "#fff",
                border: "none",
                borderRadius: "4px",
                padding: "8px 12px",
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              Save SwitchPort
            </button>
          </form>
        </section>
      )}

      {loading && <p>Loading house topology...</p>}
      {error && <p style={{ color: "#f87171" }}>Error: {error}</p>}

      {/* Floor-by-Floor Room Matrix */}
      <main style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        {sortedFloors.map((floor) => (
          <section
            key={floor.id}
            style={{
              backgroundColor: "#1e293b",
              borderRadius: "12px",
              padding: "20px",
              border: "1px solid #334155",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "16px",
              }}
            >
              <h2 style={{ margin: 0, fontSize: "1.2rem", color: "#e2e8f0" }}>
                {floor.name}
              </h2>
              <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>
                Level {floor.level_order} · {floor.rooms.length} Rooms
              </span>
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(310px, 1fr))",
                gap: "16px",
              }}
            >
              {floor.rooms.map((room) => {
                const gradeStyle =
                  GRADE_COLORS[room.health_grade] ?? GRADE_COLORS.GOOD;
                return (
                  <article
                    key={room.id}
                    onClick={() => setSelectedRoom(room)}
                    style={{
                      backgroundColor: "#0f172a",
                      border: `1px solid ${gradeStyle.border}`,
                      borderRadius: "10px",
                      padding: "16px",
                      cursor: "pointer",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: "8px",
                      }}
                    >
                      <h3 style={{ margin: 0, fontSize: "1.05rem" }}>{room.name}</h3>
                      <span
                        style={{
                          backgroundColor: gradeStyle.bg,
                          color: gradeStyle.text,
                          padding: "2px 8px",
                          borderRadius: "999px",
                          fontSize: "0.72rem",
                          fontWeight: 700,
                        }}
                      >
                        {room.health_grade}
                      </span>
                    </div>

                    {/* Wi-Fi RSSI & Coordinates Row */}
                    <div
                      style={{
                        display: "flex",
                        gap: "10px",
                        fontSize: "0.78rem",
                        color: "#94a3b8",
                        marginBottom: "10px",
                        flexWrap: "wrap",
                      }}
                    >
                      <span>
                        5 GHz:{" "}
                        <strong style={{ color: "#e2e8f0" }}>
                          {room.best_5ghz_rssi_dbm != null
                            ? `${room.best_5ghz_rssi_dbm} dBm`
                            : "N/A"}
                        </strong>
                      </span>
                      <span>
                        2.4 GHz:{" "}
                        <strong style={{ color: "#e2e8f0" }}>
                          {room.best_24ghz_rssi_dbm != null
                            ? `${room.best_24ghz_rssi_dbm} dBm`
                            : "N/A"}
                        </strong>
                      </span>
                      <span>
                        ({room.pos_x}, {room.pos_y})
                      </span>
                    </div>

                    {/* SwitchPorts in Room */}
                    {room.switch_ports.length > 0 && (
                      <div style={{ marginBottom: "10px" }}>
                        {room.switch_ports.map((sp) => (
                          <div
                            key={sp.id}
                            style={{
                              fontSize: "0.75rem",
                              backgroundColor: "#1e293b",
                              color: "#38bdf8",
                              padding: "4px 8px",
                              borderRadius: "4px",
                              marginBottom: "4px",
                            }}
                          >
                            Switch Port {sp.port_number} (PVID {sp.pvid}) ·{" "}
                            {sp.connected_device_label}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Devices in Room */}
                    <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                      {room.devices.map((dev) => {
                        const isSonos = dev.device_role === "SONOS_PLAYER";
                        return (
                          <div
                            key={dev.id}
                            style={{
                              backgroundColor: "#1e293b",
                              border: dev.is_ghost_group
                                ? "1px solid #ef4444"
                                : "1px solid transparent",
                              borderRadius: "6px",
                              padding: "8px 10px",
                              fontSize: "0.8rem",
                              display: "flex",
                              justifyContent: "space-between",
                              alignItems: "center",
                              gap: "8px",
                            }}
                          >
                            <div style={{ flex: 1 }}>
                              <div
                                style={{
                                  display: "flex",
                                  alignItems: "center",
                                  gap: "6px",
                                  flexWrap: "wrap",
                                  fontWeight: 600,
                                  color: "#f1f5f9",
                                }}
                              >
                                <span>{dev.name}</span>
                                {dev.is_archived && (
                                  <span style={{ color: "#f87171" }}>(Archived)</span>
                                )}
                                {isSonos && dev.is_ghost_group && (
                                  <span
                                    style={{
                                      backgroundColor: "#7f1d1d",
                                      color: "#fca5a5",
                                      padding: "1px 6px",
                                      borderRadius: "999px",
                                      fontSize: "0.66rem",
                                      fontWeight: 700,
                                    }}
                                  >
                                    GHOST GROUP
                                  </span>
                                )}
                              </div>
                              <div style={{ fontSize: "0.72rem", color: "#94a3b8" }}>
                                {dev.model_name} · {dev.ip_address ?? "Bonded"} ·{" "}
                                {dev.connection_mode ?? dev.device_role}
                              </div>
                              {isSonos && (
                                <div
                                  style={{
                                    fontSize: "0.7rem",
                                    color: "#cbd5e1",
                                    marginTop: "3px",
                                    display: "flex",
                                    gap: "8px",
                                    flexWrap: "wrap",
                                  }}
                                >
                                  <span>
                                    {dev.ofdm_ani_level != null
                                      ? `ANI ${dev.ofdm_ani_level}`
                                      : "ANI N/A"}
                                  </span>
                                  <span>
                                    {dev.noise_floor_dbm != null
                                      ? `${dev.noise_floor_dbm} dBm`
                                      : "Noise N/A"}
                                  </span>
                                  <span>
                                    {dev.phy_error_rate != null
                                      ? `${dev.phy_error_rate.toFixed(1)} err/s`
                                      : "0.0 err/s"}
                                  </span>
                                  {dev.stp_path_cost != null && (
                                    <span>{`STP Cost ${dev.stp_path_cost}`}</span>
                                  )}
                                  {dev.master_volume != null && (
                                    <span>{`Vol ${dev.master_volume}%`}</span>
                                  )}
                                </div>
                              )}
                            </div>
                            <button
                              type="button"
                              title="Archive Device"
                              onClick={(e) => {
                                e.stopPropagation();
                                void handleArchiveDevice(dev.id);
                              }}
                              style={{
                                background: "transparent",
                                border: "1px solid #475569",
                                color: "#cbd5e1",
                                borderRadius: "4px",
                                padding: "2px 6px",
                                fontSize: "0.7rem",
                                cursor: "pointer",
                              }}
                            >
                              Archive
                            </button>
                          </div>
                        );
                      })}
                    </div>

                    <div
                      style={{
                        marginTop: "10px",
                        display: "flex",
                        justifyContent: "flex-end",
                      }}
                    >
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          void handleArchiveRoom(room.id);
                        }}
                        style={{
                          background: "transparent",
                          border: "none",
                          color: "#64748b",
                          fontSize: "0.72rem",
                          cursor: "pointer",
                        }}
                      >
                        Archive Room
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          </section>
        ))}
      </main>

      {/* Selected Room Quick Drawer */}
      {selectedRoom && (
        <aside
          style={{
            marginTop: "24px",
            backgroundColor: "#1e293b",
            border: "1px solid #38bdf8",
            borderRadius: "10px",
            padding: "16px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <h3 style={{ margin: 0 }}>Room Deep-Dive: {selectedRoom.name}</h3>
            <button
              type="button"
              onClick={() => setSelectedRoom(null)}
              style={{
                background: "transparent",
                border: "none",
                color: "#94a3b8",
                cursor: "pointer",
              }}
            >
              Close
            </button>
          </div>
          <p style={{ color: "#cbd5e1", fontSize: "0.85rem" }}>
            {selectedRoom.description}
          </p>
        </aside>
      )}
    </div>
  );
}
