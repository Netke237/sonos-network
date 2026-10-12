import React, { useEffect, useState } from "react";
import {
  archiveDevice,
  archiveRoom,
  createDevice,
  createRoom,
  createRoomSurvey,
  createSwitchPort,
  fetchDaemonStatus,
  fetchHouseOverview,
  fetchRoomDiagnostics,
  fetchRoomHistory,
  fetchRoomSurveys,
  fetchSurveyDelta,
  flushGhostGroups,
  pollLiveSonosNow,
  runPingSweep,
  triggerDaemonCollect,
} from "./api/topologyApi";
import { TopologyGraphView } from "./components/TopologyGraphView";
import { AniCleanlinessMeter } from "./components/AniCleanlinessMeter";
import { LiveWaveformOscilloscope } from "./components/LiveWaveformOscilloscope";
import { PlainLanguageAdvisorModal } from "./components/PlainLanguageAdvisorModal";
import type {
  BssidClassification,
  ConnectionMode,
  DaemonStatus,
  DeviceRole,
  FloorMatrixItem,
  HealthGrade,
  HouseOverview,
  LiveRfSample,
  RoomDiagnosticSummary,
  RoomHistoryResponse,
  RoomMatrixItem,
  SolutionProposal,
  SurveyComparisonDelta,
  WiFiRoomSurvey,
} from "./types/topology";

const GRADE_COLORS: Record<HealthGrade, { bg: string; text: string; border: string }> = {
  EXCELLENT: { bg: "#064e3b", text: "#6ee7b7", border: "#059669" },
  GOOD: { bg: "#14532d", text: "#86efac", border: "#16a34a" },
  MARGINAL: { bg: "#713f12", text: "#fde047", border: "#ca8a04" },
  CRITICAL: { bg: "#7f1d1d", text: "#fca5a5", border: "#dc2626" },
};

const BSSID_CLASS_COLORS: Record<
  BssidClassification,
  { bg: string; text: string; border: string }
> = {
  OWN_MANAGED_AP: { bg: "#064e3b", text: "#6ee7b7", border: "#10b981" },
  SONOSNET_MESH: { bg: "#1e3a8a", text: "#93c5fd", border: "#3b82f6" },
  ROGUE_OWN_RADIO: { bg: "#7f1d1d", text: "#fca5a5", border: "#ef4444" },
  NEIGHBOR_WIFI: { bg: "#334155", text: "#cbd5e1", border: "#64748b" },
};

export default function App() {
  const [overview, setOverview] = useState<HouseOverview | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [includeArchived, setIncludeArchived] = useState<boolean>(false);
  const [crudOpen, setCrudOpen] = useState<boolean>(false);
  const [activeViewTab, setActiveViewTab] = useState<"MATRIX" | "GRAPH" | "LIVE_RF">("MATRIX");
  const [selectedRoom, setSelectedRoom] = useState<RoomMatrixItem | null>(null);
  const [roomSurveys, setRoomSurveys] = useState<WiFiRoomSurvey[]>([]);
  const [selectedDiagnosticRoom, setSelectedDiagnosticRoom] = useState<RoomMatrixItem | null>(null);
  const [roomDiagnostics, setRoomDiagnostics] = useState<RoomDiagnosticSummary | null>(null);
  const [advisorRoom, setAdvisorRoom] = useState<RoomMatrixItem | null>(null);
  const [loadingDiagnostics, setLoadingDiagnostics] = useState<boolean>(false);
  const [actionBanner, setActionBanner] = useState<string | null>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [busyMessage, setBusyMessage] = useState<string | null>(null);

  // T6 Survey Delta State
  const [deltaOpen, setDeltaOpen] = useState<boolean>(false);
  const [surveyDelta, setSurveyDelta] = useState<SurveyComparisonDelta | null>(null);
  const [baselineSurveySlug, setBaselineSurveySlug] = useState<string>("");
  const [targetSurveySlug, setTargetSurveySlug] = useState<string>("");

  // T6 Live RF Console State
  const [liveRfSamples, setLiveRfSamples] = useState<LiveRfSample[]>([]);
  const [liveRfConnected, setLiveRfConnected] = useState<boolean>(false);
  const [liveRfPaused, setLiveRfPaused] = useState<boolean>(false);
  const [liveRfRoomFilter, setLiveRfRoomFilter] = useState<string>("all");

  // T7 Historical Trends & Daemon State
  const [selectedHistoryRoom, setSelectedHistoryRoom] = useState<RoomMatrixItem | null>(null);
  const [roomHistory, setRoomHistory] = useState<RoomHistoryResponse | null>(null);
  const [historyRange, setHistoryRange] = useState<"1h" | "24h" | "7d">("24h");
  const [loadingHistory, setLoadingHistory] = useState<boolean>(false);
  const [daemonStatus, setDaemonStatus] = useState<DaemonStatus | null>(null);

  // Room Survey Form State
  const [surveyLabel, setSurveyLabel] = useState<string>("");
  const [surveyApName, setSurveyApName] = useState<string>("Galerie EAP650");
  const [surveyLinkSpeed, setSurveyLinkSpeed] = useState<number>(1201);
  const [surveyBssid, setSurveyBssid] = useState<string>("76:4C:BC:76:7C:41");
  const [surveySsid, setSurveySsid] = useState<string>("WuTangLan-Family");
  const [surveyBand, setSurveyBand] = useState<"2.4GHz" | "5GHz">("5GHz");
  const [surveyChannel, setSurveyChannel] = useState<number>(44);
  const [surveyWidth, setSurveyWidth] = useState<number>(80);
  const [surveyRssi, setSurveyRssi] = useState<number>(-49);

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

  useEffect(() => {
    void fetchDaemonStatus().then(setDaemonStatus).catch(() => {});
  }, []);

  const handleOpenRoomHistory = async (
    room: RoomMatrixItem,
    range: "1h" | "24h" | "7d" = "24h"
  ) => {
    setSelectedHistoryRoom(room);
    setHistoryRange(range);
    setBusyAction(`history-${room.id}`);
    setBusyMessage(`Loading historical telemetry trends for ${room.name}...`);
    try {
      setLoadingHistory(true);
      const hist = await fetchRoomHistory(room.slug, range);
      setRoomHistory(hist);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load room history");
    } finally {
      setLoadingHistory(false);
      setBusyAction(null);
      setBusyMessage(null);
    }
  };

  const handleChangeHistoryRange = async (range: "1h" | "24h" | "7d") => {
    setHistoryRange(range);
    if (selectedHistoryRoom) {
      setBusyAction(`history-range-${range}`);
      setBusyMessage(
        `Loading historical telemetry for ${selectedHistoryRoom.name} (${range})...`
      );
      try {
        setLoadingHistory(true);
        const hist = await fetchRoomHistory(selectedHistoryRoom.slug, range);
        setRoomHistory(hist);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load room history");
      } finally {
        setLoadingHistory(false);
        setBusyAction(null);
        setBusyMessage(null);
      }
    }
  };

  const handleTriggerDaemonCollect = async () => {
    setBusyAction("daemon-cycle");
    setBusyMessage("Executing 24/7 background telemetry cycle across all players...");
    try {
      const res = await triggerDaemonCollect();
      setActionBanner(
        `24/7 Telemetry Cycle Executed: Snapshot ${res.batch_id} (${res.total_players} players, ${res.pruned_count} pruned)`
      );
      await loadData();
      if (selectedHistoryRoom) {
        await handleOpenRoomHistory(selectedHistoryRoom, historyRange);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to trigger daemon collection"
      );
    } finally {
      setBusyAction(null);
      setBusyMessage(null);
    }
  };

  useEffect(() => {
    if (activeViewTab !== "LIVE_RF" || liveRfPaused) return;
    const apiBase =
      (import.meta as unknown as { env?: Record<string, string> }).env
        ?.VITE_API_BASE_URL ?? "http://192.168.55.60:8001";
    const wsBase = apiBase.replace(/^http/, "ws");
    const wsUrl = `${wsBase}/api/ws/live-rf?room_slug=${liveRfRoomFilter}&interval_sec=1.5`;

    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket(wsUrl);
      ws.onopen = () => setLiveRfConnected(true);
      ws.onclose = () => setLiveRfConnected(false);
      ws.onerror = () => setLiveRfConnected(false);
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.samples && Array.isArray(data.samples)) {
            setLiveRfSamples(data.samples);
          }
        } catch {
          // ignore
        }
      };
    } catch {
      // ignore
    }
    return () => {
      if (ws) ws.close();
    };
  }, [activeViewTab, liveRfPaused, liveRfRoomFilter]);

  const handleLoadSurveyDelta = async (
    baseSlug?: string,
    targetSlug?: string
  ) => {
    if (!selectedRoom) return;
    setBusyAction("compare-delta");
    setBusyMessage(`Comparing survey deltas for ${selectedRoom.name}...`);
    try {
      const d = await fetchSurveyDelta(
        selectedRoom.slug,
        baseSlug || undefined,
        targetSlug || undefined
      );
      setSurveyDelta(d);
      setDeltaOpen(true);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load survey delta"
      );
    } finally {
      setBusyAction(null);
      setBusyMessage(null);
    }
  };

  const handleOpenRoomSurveys = async (room: RoomMatrixItem) => {
    setSelectedRoom(room);
    setBusyAction(`inspect-${room.id}`);
    setBusyMessage(`Loading Wi-Fi RF spectrum & survey scans for ${room.name}...`);
    try {
      const surveys = await fetchRoomSurveys(room.slug);
      setRoomSurveys(Array.isArray(surveys) ? surveys : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load room Wi-Fi surveys");
    } finally {
      setBusyAction(null);
      setBusyMessage(null);
    }
  };

  const handleCreateRoomSurvey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRoom) return;
    setBusyAction("submit-survey");
    setBusyMessage(`Saving Wi-Fi survey for ${selectedRoom.name}...`);
    try {
      const labelToUse = surveyLabel.trim() || "Manual Room Survey";
      await createRoomSurvey(selectedRoom.slug, {
        label: labelToUse,
        link_speed_mbps: Number(surveyLinkSpeed) || undefined,
        readings: [
          {
            bssid: surveyBssid,
            ssid: surveySsid,
            band: surveyBand,
            channel: Number(surveyChannel),
            width_mhz: Number(surveyWidth),
            rssi_dbm: Number(surveyRssi),
          },
        ],
      });
      setSurveyLabel("");
      const updatedSurveys = await fetchRoomSurveys(selectedRoom.slug);
      setRoomSurveys(Array.isArray(updatedSurveys) ? updatedSurveys : []);
      await loadData(includeArchived);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create survey");
    } finally {
      setBusyAction(null);
      setBusyMessage(null);
    }
  };

  const handlePollSonosNow = async () => {
    setBusyAction("poll-sonos");
    setBusyMessage("Polling live Sonos telemetry from 14 players via UPnP & Atheros drivers...");
    try {
      const snap = await pollLiveSonosNow();
      setActionBanner(
        `Polled ${snap.reachable_players}/${snap.total_players} Sonos players (${snap.batch_id})`
      );
      await loadData(includeArchived);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to poll Sonos");
    } finally {
      setBusyAction(null);
      setBusyMessage(null);
    }
  };

  const handleFlushGhostGroups = async () => {
    setBusyAction("flush-ghost");
    setBusyMessage("Flushing Ghost Groups across all zones...");
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
    } finally {
      setBusyAction(null);
      setBusyMessage(null);
    }
  };

  const handleOpenRoomDiagnostics = async (room: RoomMatrixItem) => {
    setSelectedDiagnosticRoom(room);
    setLoadingDiagnostics(true);
    setBusyAction(`diag-${room.id}`);
    setBusyMessage(`Running 3-Pillar analysis (Sonos, Wi-Fi, Switch VLAN) for ${room.name}...`);
    try {
      const diag = await fetchRoomDiagnostics(room.slug);
      setRoomDiagnostics(diag);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load room diagnostics"
      );
    } finally {
      setLoadingDiagnostics(false);
      setBusyAction(null);
      setBusyMessage(null);
    }
  };

  const handleExecuteProposal = async (proposal: SolutionProposal) => {
    setBusyAction(`prop-${proposal.rank}`);
    setBusyMessage(`Executing solution proposal: ${proposal.title}...`);
    try {
      if (proposal.one_click_action === "FLUSH_GHOST_GROUPS") {
        const res = await flushGhostGroups();
        setActionBanner(
          `Flushed ghost groups on ${res.flushed_count} zones: ${
            res.flushed_zones.join(", ") || "All zones clean"
          }`
        );
        await loadData(includeArchived);
        if (selectedDiagnosticRoom) {
          const diag = await fetchRoomDiagnostics(selectedDiagnosticRoom.slug);
          setRoomDiagnostics(diag);
        }
      } else if (proposal.one_click_action === "RUN_PING_JITTER_SWEEP") {
        const res = await runPingSweep();
        setActionBanner(
          `Ping sweep completed for ${res.reachable_count}/${res.total_probed} players (Avg: ${res.avg_rtt_ms.toFixed(
            1
          )} ms, Max: ${res.max_rtt_ms.toFixed(1)} ms)`
        );
        await loadData(includeArchived);
        if (selectedDiagnosticRoom) {
          const diag = await fetchRoomDiagnostics(selectedDiagnosticRoom.slug);
          setRoomDiagnostics(diag);
        }
      } else if (proposal.one_click_action === "POLL_NOW") {
        const res = await pollLiveSonosNow();
        setActionBanner(
          `Polled live Sonos snapshot: ${res.reachable_players}/${res.total_players} players reachable`
        );
        await loadData(includeArchived);
        if (selectedDiagnosticRoom) {
          const diag = await fetchRoomDiagnostics(selectedDiagnosticRoom.slug);
          setRoomDiagnostics(diag);
        }
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to execute proposal action"
      );
    } finally {
      setBusyAction(null);
      setBusyMessage(null);
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
      {/* CSS Animation Keyframes for Sand Clock and Pulse */}
      <style>{`
        @keyframes sonosSpin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @keyframes sonosPulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.85; transform: scale(0.98); }
        }
      `}</style>

      {/* Floating Global Sand Clock Activity Banner */}
      {busyMessage && (
        <aside
          aria-label="Action Progress Notification"
          role="status"
          style={{
            position: "fixed",
            top: "20px",
            right: "24px",
            zIndex: 99999,
            backgroundColor: "#091426",
            border: "2px solid #38bdf8",
            boxShadow:
              "0 20px 25px -5px rgba(0, 0, 0, 0.7), 0 0 20px rgba(56, 189, 248, 0.5)",
            borderRadius: "10px",
            padding: "12px 20px",
            color: "#f8fafc",
            display: "flex",
            alignItems: "center",
            gap: "12px",
            fontWeight: 600,
            fontSize: "0.92rem",
            maxWidth: "480px",
            animation: "sonosPulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
          }}
        >
          <span
            style={{
              fontSize: "1.3rem",
              display: "inline-block",
              animation: "sonosSpin 1.8s linear infinite",
            }}
          >
            ⏳
          </span>
          <div style={{ display: "flex", flexDirection: "column" }}>
            <span
              style={{
                fontSize: "0.75rem",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                color: "#38bdf8",
                fontWeight: 700,
              }}
            >
              Action in Progress
            </span>
            <span>{busyMessage}</span>
          </div>
        </aside>
      )}

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
            disabled={Boolean(busyAction)}
            onClick={() => void handlePollSonosNow()}
            style={{
              backgroundColor: "#0d9488",
              color: "#ffffff",
              border: "none",
              borderRadius: "6px",
              padding: "8px 14px",
              fontWeight: 600,
              cursor: busyAction ? "not-allowed" : "pointer",
              opacity: busyAction ? 0.65 : 1,
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            {busyAction === "poll-sonos" && (
              <span
                style={{
                  display: "inline-block",
                  animation: "sonosSpin 1.5s linear infinite",
                }}
              >
                ⏳
              </span>
            )}
            Poll Live Sonos Now{busyAction === "poll-sonos" ? " (Polling...)" : ""}
          </button>
          <button
            type="button"
            disabled={Boolean(busyAction)}
            onClick={() => void handleFlushGhostGroups()}
            style={{
              backgroundColor: "#dc2626",
              color: "#ffffff",
              border: "none",
              borderRadius: "6px",
              padding: "8px 14px",
              fontWeight: 600,
              cursor: busyAction ? "not-allowed" : "pointer",
              opacity: busyAction ? 0.65 : 1,
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            {busyAction === "flush-ghost" && (
              <span
                style={{
                  display: "inline-block",
                  animation: "sonosSpin 1.5s linear infinite",
                }}
              >
                ⏳
              </span>
            )}
            Flush Ghost Groups{busyAction === "flush-ghost" ? " (Flushing...)" : ""}
          </button>
          <button
            type="button"
            disabled={Boolean(busyAction)}
            onClick={() => void handleTriggerDaemonCollect()}
            style={{
              backgroundColor: "#0284c7",
              color: "#ffffff",
              border: "none",
              borderRadius: "6px",
              padding: "8px 14px",
              fontWeight: 600,
              cursor: busyAction ? "not-allowed" : "pointer",
              opacity: busyAction ? 0.65 : 1,
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            {busyAction === "daemon-cycle" && (
              <span
                style={{
                  display: "inline-block",
                  animation: "sonosSpin 1.5s linear infinite",
                }}
              >
                ⏳
              </span>
            )}
            Run 24/7 Daemon Cycle{busyAction === "daemon-cycle" ? " (Running...)" : ""}
          </button>
          <span
            role="status"
            style={{
              backgroundColor: "#064e3b",
              border: "1px solid #10b981",
              color: "#6ee7b7",
              padding: "6px 10px",
              borderRadius: "6px",
              fontSize: "0.78rem",
              fontWeight: 700,
            }}
          >
            24/7 Daemon: {daemonStatus?.interval_sec ? `${daemonStatus.interval_sec}s` : "60s"}
          </span>
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

      {/* Top-Level Dual Representation View Tabs */}
      <nav
        aria-label="Primary View Navigation"
        style={{
          display: "flex",
          gap: "10px",
          marginBottom: "20px",
          flexWrap: "wrap",
        }}
      >
        <button
          type="button"
          onClick={() => setActiveViewTab("MATRIX")}
          style={{
            backgroundColor: activeViewTab === "MATRIX" ? "#0284c7" : "#1e293b",
            color: "#f8fafc",
            border: "1px solid #38bdf8",
            borderRadius: "8px",
            padding: "8px 16px",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          Floor &amp; Room Coverage Matrix
        </button>
        <button
          type="button"
          onClick={() => setActiveViewTab("GRAPH")}
          style={{
            backgroundColor: activeViewTab === "GRAPH" ? "#0284c7" : "#1e293b",
            color: "#f8fafc",
            border: "1px solid #38bdf8",
            borderRadius: "8px",
            padding: "8px 16px",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          Interactive Network Topology Graph
        </button>
        <button
          type="button"
          onClick={() => setActiveViewTab("LIVE_RF")}
          style={{
            backgroundColor: activeViewTab === "LIVE_RF" ? "#0284c7" : "#1e293b",
            color: "#f8fafc",
            border: "1px solid #38bdf8",
            borderRadius: "8px",
            padding: "8px 16px",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          Live RF &amp; EMI Isolation Console
        </button>
      </nav>

      {loading && <p>Loading house topology...</p>}
      {error && <p style={{ color: "#f87171" }}>Error: {error}</p>}

      {activeViewTab === "LIVE_RF" ? (
        <section
          role="region"
          aria-label="Live RF and EMI Isolation Console"
          style={{
            backgroundColor: "#1e293b",
            borderRadius: "12px",
            padding: "20px",
            border: "1px solid #38bdf8",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "16px",
              flexWrap: "wrap",
              gap: "10px",
            }}
          >
            <div>
              <h2 style={{ margin: 0, fontSize: "1.3rem", color: "#f8fafc" }}>
                Live RF &amp; EMI Isolation Console
              </h2>
              <p
                style={{
                  margin: "4px 0 0",
                  color: "#94a3b8",
                  fontSize: "0.85rem",
                }}
              >
                High-frequency (1.5–2s) live OFDM ANI and PHY Error Velocity stream for sequential EMI source isolation.
              </p>
            </div>
            <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
              <button
                type="button"
                onClick={() => setLiveRfPaused(!liveRfPaused)}
                style={{
                  backgroundColor: liveRfPaused ? "#059669" : "#d97706",
                  color: "#fff",
                  border: "none",
                  borderRadius: "6px",
                  padding: "6px 14px",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                {liveRfPaused ? "Resume Live Stream" : "Pause Stream"}
              </button>
            </div>
          </div>

          {/* Real-time Oscilloscope & Sequential EMI Procedure */}
          <LiveWaveformOscilloscope
            samples={liveRfSamples}
            isConnected={liveRfConnected}
            isPaused={liveRfPaused}
            onTogglePause={() => setLiveRfPaused(!liveRfPaused)}
            roomFilter={liveRfRoomFilter}
            onRoomFilterChange={(r) => setLiveRfRoomFilter(r)}
          />

          {/* EMI Isolation Guidance Box */}
          <div
            style={{
              backgroundColor: "#1e1b4b",
              border: "1px solid #6366f1",
              borderRadius: "8px",
              padding: "12px 16px",
              marginBottom: "20px",
              color: "#e0e7ff",
              fontSize: "0.85rem",
            }}
          >
            <strong>Sequential EMI Isolation Procedure: </strong>
            Unplug USB-C dock or power bricks while watching PHY error rate drop to 0.0 err/s
          </div>

          {/* Live Table */}
          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                fontSize: "0.82rem",
              }}
            >
              <thead>
                <tr
                  style={{
                    borderBottom: "1px solid #475569",
                    color: "#94a3b8",
                    textAlign: "left",
                  }}
                >
                  <th style={{ padding: "8px" }}>Zone Name</th>
                  <th style={{ padding: "8px" }}>IP Address</th>
                  <th style={{ padding: "8px" }}>Channel</th>
                  <th style={{ padding: "8px" }}>OFDM ANI Level</th>
                  <th style={{ padding: "8px" }}>Noise Floor</th>
                  <th style={{ padding: "8px" }}>PHY Error Rate</th>
                  <th style={{ padding: "8px" }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {liveRfSamples.map((s) => {
                  const hasSpike =
                    (s.ofdm_ani_level != null && s.ofdm_ani_level >= 7) ||
                    s.phy_error_rate > 100;
                  return (
                    <tr
                      key={s.rincon_uuid}
                      style={{
                        borderBottom: "1px solid #334155",
                        backgroundColor: hasSpike ? "#450a0a" : "transparent",
                      }}
                    >
                      <td
                        style={{
                          padding: "10px 8px",
                          fontWeight: 600,
                          color: "#f8fafc",
                        }}
                      >
                        {s.zone_name}
                      </td>
                      <td style={{ padding: "10px 8px", color: "#94a3b8" }}>
                        {s.ip_address ?? "N/A"}
                      </td>
                      <td style={{ padding: "10px 8px", color: "#cbd5e1" }}>
                        Ch {s.ieee_channel ?? 6}
                      </td>
                      <td style={{ padding: "10px 8px" }}>
                        <AniCleanlinessMeter aniLevel={s.ofdm_ani_level} compact={true} />
                      </td>
                      <td style={{ padding: "10px 8px", color: "#cbd5e1" }}>
                        {s.noise_floor_dbm != null
                          ? `${s.noise_floor_dbm} dBm`
                          : "N/A"}
                      </td>
                      <td
                        style={{
                          padding: "10px 8px",
                          fontWeight: 700,
                          color:
                            s.phy_error_rate > 100
                              ? "#ef4444"
                              : s.phy_error_rate > 20
                              ? "#f59e0b"
                              : "#10b981",
                        }}
                      >
                        {`${s.phy_error_rate.toFixed(1)} err/s`}
                      </td>
                      <td style={{ padding: "10px 8px" }}>
                        {hasSpike ? (
                          <span style={{ color: "#ef4444", fontWeight: 700 }}>
                            Severe EMI Spike
                          </span>
                        ) : (
                          <span style={{ color: "#10b981" }}>Clean</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      ) : activeViewTab === "GRAPH" ? (
        <TopologyGraphView
          floors={sortedFloors}
          onInspectRoomSlug={(roomSlug) => {
            const targetRoom = allRooms.find((r) => r.slug === roomSlug);
            if (targetRoom) {
              void handleOpenRoomSurveys(targetRoom);
            }
          }}
          onExplainRoomSlug={(roomSlug) => {
            const targetRoom = allRooms.find((r) => r.slug === roomSlug);
            if (targetRoom) {
              setAdvisorRoom(targetRoom);
            }
          }}
        />
      ) : (
        /* Floor-by-Floor Room Matrix */
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
                const wifiGradeStyle =
                  GRADE_COLORS[room.wifi_health_grade ?? room.health_grade] ??
                  GRADE_COLORS.GOOD;
                return (
                  <article
                    key={room.id}
                    style={{
                      backgroundColor: "#0f172a",
                      border: `1px solid ${gradeStyle.border}`,
                      borderRadius: "10px",
                      padding: "16px",
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

                    {room.top_diagnostic_title && (
                      <div
                        role="button"
                        tabIndex={0}
                        onClick={(e) => {
                          e.stopPropagation();
                          setAdvisorRoom(room);
                        }}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" || e.key === " ") {
                            e.preventDefault();
                            setAdvisorRoom(room);
                          }
                        }}
                        style={{
                          backgroundColor: "#451a03",
                          color: "#fde047",
                          border: "1px solid #ca8a04",
                          borderRadius: "6px",
                          padding: "6px 10px",
                          fontSize: "0.72rem",
                          marginBottom: "8px",
                          fontWeight: 500,
                          cursor: "pointer",
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          gap: "8px",
                        }}
                        title="Click to view plain-language root cause and recommended actions"
                      >
                        <span>⚠️ {room.top_diagnostic_title}</span>
                        <span
                          style={{
                            backgroundColor: "#ca8a04",
                            color: "#000000",
                            padding: "2px 6px",
                            borderRadius: "4px",
                            fontSize: "0.68rem",
                            fontWeight: 700,
                            flexShrink: 0,
                          }}
                        >
                          Explain &amp; Fix ➔
                        </span>
                      </div>
                    )}

                    {/* Wi-Fi RSSI & Coordinates Row */}
                    <div
                      style={{
                        display: "flex",
                        gap: "10px",
                        fontSize: "0.78rem",
                        color: "#94a3b8",
                        marginBottom: "6px",
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

                    {/* T3 Room Wi-Fi Coverage Summary Row */}
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        gap: "8px",
                        flexWrap: "wrap",
                        backgroundColor: "#1e293b",
                        padding: "6px 10px",
                        borderRadius: "6px",
                        marginBottom: "10px",
                        fontSize: "0.75rem",
                      }}
                    >
                      <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
                        <span style={{ color: "#38bdf8", fontWeight: 600 }}>
                          {room.best_ap_name ?? "Galerie EAP650"}
                        </span>
                        {room.link_speed_mbps != null && (
                          <span style={{ color: "#cbd5e1" }}>
                            {`${room.link_speed_mbps} Mbps`}
                          </span>
                        )}
                        {room.wifi_health_grade && (
                          <span
                            style={{
                              backgroundColor: wifiGradeStyle.bg,
                              color: wifiGradeStyle.text,
                              padding: "1px 6px",
                              borderRadius: "999px",
                              fontSize: "0.68rem",
                              fontWeight: 700,
                            }}
                          >
                            Wi-Fi {room.wifi_health_grade}
                          </span>
                        )}
                      </div>
                      <button
                        type="button"
                        disabled={Boolean(busyAction)}
                        onClick={(e) => {
                          e.stopPropagation();
                          void handleOpenRoomSurveys(room);
                        }}
                        style={{
                          backgroundColor: "#0284c7",
                          color: "#ffffff",
                          border: "none",
                          borderRadius: "4px",
                          padding: "3px 8px",
                          fontSize: "0.7rem",
                          fontWeight: 600,
                          cursor: busyAction ? "not-allowed" : "pointer",
                          opacity: busyAction ? 0.65 : 1,
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "4px",
                        }}
                      >
                        {busyAction === `inspect-${room.id}` && (
                          <span
                            style={{
                              display: "inline-block",
                              animation: "sonosSpin 1.5s linear infinite",
                            }}
                          >
                            ⏳
                          </span>
                        )}
                        Inspect Room Wi-Fi{busyAction === `inspect-${room.id}` ? " (Inspecting...)" : ""}
                      </button>
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
                                  <AniCleanlinessMeter
                                    aniLevel={dev.ofdm_ani_level}
                                    compact={true}
                                    showExplanation={false}
                                  />
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
                        justifyContent: "space-between",
                        alignItems: "center",
                        gap: "6px",
                        flexWrap: "wrap",
                      }}
                    >
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setAdvisorRoom(room);
                        }}
                        style={{
                          backgroundColor: "#ca8a04",
                          color: "#000000",
                          border: "none",
                          borderRadius: "4px",
                          padding: "4px 8px",
                          fontSize: "0.72rem",
                          fontWeight: 700,
                          cursor: "pointer",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "4px",
                        }}
                      >
                        💡 Explain &amp; Fix
                      </button>
                      <button
                        type="button"
                        disabled={Boolean(busyAction)}
                        onClick={(e) => {
                          e.stopPropagation();
                          void handleOpenRoomDiagnostics(room);
                        }}
                        style={{
                          backgroundColor: "#7c3aed",
                          color: "#ffffff",
                          border: "none",
                          borderRadius: "4px",
                          padding: "4px 8px",
                          fontSize: "0.72rem",
                          fontWeight: 600,
                          cursor: busyAction ? "not-allowed" : "pointer",
                          opacity: busyAction ? 0.65 : 1,
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "4px",
                        }}
                      >
                        {busyAction === `diag-${room.id}` && (
                          <span
                            style={{
                              display: "inline-block",
                              animation: "sonosSpin 1.5s linear infinite",
                            }}
                          >
                            ⏳
                          </span>
                        )}
                        Diagnose Room / 3-Pillar Analysis{busyAction === `diag-${room.id}` ? " (Analyzing...)" : ""}
                      </button>
                      <button
                        type="button"
                        disabled={Boolean(busyAction)}
                        onClick={(e) => {
                          e.stopPropagation();
                          void handleOpenRoomHistory(room);
                        }}
                        style={{
                          backgroundColor: "#0284c7",
                          color: "#ffffff",
                          border: "none",
                          borderRadius: "4px",
                          padding: "4px 8px",
                          fontSize: "0.72rem",
                          fontWeight: 600,
                          cursor: busyAction ? "not-allowed" : "pointer",
                          opacity: busyAction ? 0.65 : 1,
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "4px",
                        }}
                      >
                        {busyAction === `history-${room.id}` && (
                          <span
                            style={{
                              display: "inline-block",
                              animation: "sonosSpin 1.5s linear infinite",
                            }}
                          >
                            ⏳
                          </span>
                        )}
                        Historical Trends{busyAction === `history-${room.id}` ? " (Loading...)" : ""}
                      </button>
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
      )}

      {/* Room 3-Pillar Diagnostic Drawer */}
      {selectedDiagnosticRoom && (
        <section
          role="region"
          aria-label="Room 3-Pillar Diagnostic Drawer"
          style={{
            marginTop: "24px",
            backgroundColor: "#1e293b",
            border: "1px solid #a855f7",
            borderRadius: "10px",
            padding: "20px",
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
            <div>
              <h3 style={{ margin: 0, fontSize: "1.2rem", color: "#f8fafc" }}>
                Room 3-Pillar Diagnostic Drawer: {selectedDiagnosticRoom.name}
              </h3>
              <p
                style={{
                  margin: "4px 0 0",
                  color: "#94a3b8",
                  fontSize: "0.82rem",
                }}
              >
                {selectedDiagnosticRoom.description}
              </p>
            </div>
            <button
              type="button"
              onClick={() => {
                setSelectedDiagnosticRoom(null);
                setRoomDiagnostics(null);
              }}
              style={{
                background: "transparent",
                border: "none",
                color: "#94a3b8",
                fontSize: "1rem",
                cursor: "pointer",
              }}
            >
              Close
            </button>
          </div>

          {loadingDiagnostics && <p>Loading 3-pillar diagnostics...</p>}

          {roomDiagnostics && (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "20px",
              }}
            >
              {/* 3 Pillars Grid */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns:
                    "repeat(auto-fit, minmax(280px, 1fr))",
                  gap: "16px",
                }}
              >
                {/* Pillar 1 — Wi-Fi Situation */}
                <div
                  style={{
                    backgroundColor: "#0f172a",
                    borderRadius: "8px",
                    padding: "16px",
                    border: "1px solid #334155",
                  }}
                >
                  <h4
                    style={{
                      margin: "0 0 10px",
                      color: "#38bdf8",
                      fontSize: "0.95rem",
                    }}
                  >
                    Pillar 1 — Wi-Fi Situation
                  </h4>
                  <div
                    style={{
                      fontSize: "0.8rem",
                      color: "#cbd5e1",
                      display: "flex",
                      flexDirection: "column",
                      gap: "6px",
                    }}
                  >
                    <div>
                      Health Grade:{" "}
                      <strong
                        style={{
                          color:
                            GRADE_COLORS[
                              roomDiagnostics.wifi_pillar.health_grade
                            ]?.text ?? "#fff",
                        }}
                      >
                        {roomDiagnostics.wifi_pillar.health_grade}
                      </strong>
                    </div>
                    <div>
                      5 GHz:{" "}
                      <strong>
                        {roomDiagnostics.wifi_pillar.best_5ghz_dbm != null
                          ? `${roomDiagnostics.wifi_pillar.best_5ghz_dbm} dBm`
                          : "N/A"}
                      </strong>
                    </div>
                    <div>
                      2.4 GHz:{" "}
                      <strong>
                        {roomDiagnostics.wifi_pillar.best_24ghz_dbm != null
                          ? `${roomDiagnostics.wifi_pillar.best_24ghz_dbm} dBm`
                          : "N/A"}
                      </strong>
                    </div>
                    <div>
                      Covering AP:{" "}
                      <strong>
                        {roomDiagnostics.wifi_pillar.covering_ap_name ?? "None"}
                      </strong>
                    </div>
                    {roomDiagnostics.wifi_pillar.link_speed_mbps != null && (
                      <div>
                        Link Speed:{" "}
                        <strong>
                          {roomDiagnostics.wifi_pillar.link_speed_mbps} Mbps
                        </strong>
                      </div>
                    )}
                    <div
                      style={{
                        marginTop: "4px",
                        color: "#94a3b8",
                        fontStyle: "italic",
                      }}
                    >
                      {roomDiagnostics.wifi_pillar.summary_note ||
                        roomDiagnostics.wifi_pillar.channel_summary ||
                        ""}
                    </div>
                  </div>
                </div>

                {/* Pillar 2 — Sonos Situation */}
                <div
                  style={{
                    backgroundColor: "#0f172a",
                    borderRadius: "8px",
                    padding: "16px",
                    border: "1px solid #334155",
                  }}
                >
                  <h4
                    style={{
                      margin: "0 0 10px",
                      color: "#a855f7",
                      fontSize: "0.95rem",
                    }}
                  >
                    Pillar 2 — Sonos Situation
                  </h4>
                  <div
                    style={{
                      fontSize: "0.8rem",
                      color: "#cbd5e1",
                      display: "flex",
                      flexDirection: "column",
                      gap: "6px",
                    }}
                  >
                    <div>
                      Health Grade:{" "}
                      <strong
                        style={{
                          color:
                            GRADE_COLORS[
                              roomDiagnostics.sonos_pillar.health_grade
                            ]?.text ?? "#fff",
                        }}
                      >
                        {roomDiagnostics.sonos_pillar.health_grade}
                      </strong>
                    </div>
                    <div>
                      Players:{" "}
                      <strong>
                        {roomDiagnostics.sonos_pillar.total_players ??
                          roomDiagnostics.sonos_pillar.player_count ??
                          0}
                      </strong>
                    </div>
                    <div>
                      STP Root:{" "}
                      <strong>
                        {roomDiagnostics.sonos_pillar.designated_stp_root}
                      </strong>
                    </div>
                    {roomDiagnostics.sonos_pillar.summary_note && (
                      <div
                        style={{
                          marginTop: "4px",
                          color: "#94a3b8",
                          fontStyle: "italic",
                        }}
                      >
                        {roomDiagnostics.sonos_pillar.summary_note}
                      </div>
                    )}
                    {roomDiagnostics.sonos_pillar.players.map((p) => (
                      <div
                        key={p.rincon_uuid}
                        style={{
                          marginTop: "8px",
                          borderTop: "1px solid #1e293b",
                          paddingTop: "6px",
                        }}
                      >
                        <div style={{ fontWeight: 600, color: "#f8fafc" }}>
                          {p.zone_name} ({p.connection_mode}) · {p.overall_grade}
                        </div>
                        <div
                          style={{
                            fontSize: "0.75rem",
                            color: "#38bdf8",
                            marginTop: "2px",
                          }}
                        >
                          {p.grading_rationale}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Pillar 3 — Wired / Switch VLAN Situation */}
                <div
                  style={{
                    backgroundColor: "#0f172a",
                    borderRadius: "8px",
                    padding: "16px",
                    border: "1px solid #334155",
                  }}
                >
                  <h4
                    style={{
                      margin: "0 0 10px",
                      color: "#10b981",
                      fontSize: "0.95rem",
                    }}
                  >
                    Pillar 3 — Wired / Switch VLAN Situation
                  </h4>
                  <div
                    style={{
                      fontSize: "0.8rem",
                      color: "#cbd5e1",
                      display: "flex",
                      flexDirection: "column",
                      gap: "6px",
                    }}
                  >
                    <div>
                      Health Grade:{" "}
                      <strong
                        style={{
                          color:
                            GRADE_COLORS[
                              roomDiagnostics.wired_pillar.health_grade
                            ]?.text ?? "#fff",
                        }}
                      >
                        {roomDiagnostics.wired_pillar.health_grade}
                      </strong>
                    </div>
                    <div>
                      VLAN 10 Wall Jack:{" "}
                      <strong>
                        {roomDiagnostics.wired_pillar.has_vlan10_wall_jack
                          ? "Available"
                          : "None"}
                      </strong>
                    </div>
                    {roomDiagnostics.wired_pillar.port_numbers.length > 0 && (
                      <div>
                        Ports:{" "}
                        <strong>
                          Port {roomDiagnostics.wired_pillar.port_numbers.join(", ")}
                        </strong>
                      </div>
                    )}
                    {(roomDiagnostics.wired_pillar.stp_guard_note ||
                      roomDiagnostics.wired_pillar.stp_root_guard_note) && (
                      <div
                        style={{
                          marginTop: "6px",
                          backgroundColor: "#3b0764",
                          border: "1px solid #9333ea",
                          borderRadius: "6px",
                          padding: "8px",
                          color: "#e9d5ff",
                          fontSize: "0.75rem",
                        }}
                      >
                        {roomDiagnostics.wired_pillar.stp_guard_note ||
                          roomDiagnostics.wired_pillar.stp_root_guard_note}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Active Diagnostics */}
              {roomDiagnostics.diagnostics.length > 0 && (
                <div>
                  <h4
                    style={{
                      margin: "0 0 10px",
                      fontSize: "0.95rem",
                      color: "#f8fafc",
                    }}
                  >
                    Active Diagnostics ({roomDiagnostics.diagnostics.length})
                  </h4>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "8px",
                    }}
                  >
                    {roomDiagnostics.diagnostics.map((d) => (
                      <div
                        key={d.id}
                        style={{
                          backgroundColor: "#0f172a",
                          border: "1px solid #334155",
                          borderRadius: "8px",
                          padding: "12px",
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                            marginBottom: "4px",
                          }}
                        >
                          <div style={{ fontWeight: 600, color: "#f8fafc" }}>
                            {d.title}
                          </div>
                          <span
                            style={{
                              fontSize: "0.7rem",
                              backgroundColor: "#334155",
                              color: "#94a3b8",
                              padding: "2px 6px",
                              borderRadius: "4px",
                            }}
                          >
                            {d.rule_code}
                          </span>
                        </div>
                        <p
                          style={{
                            margin: 0,
                            fontSize: "0.78rem",
                            color: "#cbd5e1",
                          }}
                        >
                          {d.summary}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Ranked Solution Proposals */}
              {roomDiagnostics.solution_proposals.length > 0 && (
                <div>
                  <h4
                    style={{
                      margin: "0 0 10px",
                      fontSize: "0.95rem",
                      color: "#f8fafc",
                    }}
                  >
                    Ranked Solution Proposals
                  </h4>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                    }}
                  >
                    {roomDiagnostics.solution_proposals.map((prop) => (
                      <div
                        key={prop.id}
                        style={{
                          backgroundColor: "#0f172a",
                          border: "1px solid #475569",
                          borderRadius: "8px",
                          padding: "14px",
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                            marginBottom: "6px",
                            flexWrap: "wrap",
                            gap: "8px",
                          }}
                        >
                          <div style={{ fontWeight: 600, color: "#38bdf8" }}>
                            #{prop.rank} · {prop.title}
                          </div>
                          {prop.action_type === "ONE_CLICK" && (
                            <button
                              type="button"
                              disabled={Boolean(busyAction)}
                              onClick={() => void handleExecuteProposal(prop)}
                              style={{
                                backgroundColor: "#059669",
                                color: "#ffffff",
                                border: "none",
                                borderRadius: "4px",
                                padding: "4px 10px",
                                fontSize: "0.75rem",
                                fontWeight: 600,
                                cursor: busyAction ? "not-allowed" : "pointer",
                                opacity: busyAction ? 0.65 : 1,
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "4px",
                              }}
                            >
                              {busyAction === `prop-${prop.rank}` && (
                                <span
                                  style={{
                                    display: "inline-block",
                                    animation: "sonosSpin 1.5s linear infinite",
                                  }}
                                >
                                  ⏳
                                </span>
                              )}
                              Execute: {prop.title}{busyAction === `prop-${prop.rank}` ? " (Executing...)" : ""}
                            </button>
                          )}
                        </div>
                        <p
                          style={{
                            margin: "0 0 8px",
                            fontSize: "0.78rem",
                            color: "#cbd5e1",
                          }}
                        >
                          {prop.description}
                        </p>
                        {prop.stp_guard_warning && (
                          <div
                            style={{
                              backgroundColor: "#7f1d1d",
                              border: "1px solid #ef4444",
                              borderRadius: "6px",
                              padding: "6px 10px",
                              color: "#fca5a5",
                              fontSize: "0.74rem",
                            }}
                          >
                            {prop.stp_guard_warning}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </section>
      )}

      {/* Room Historical Trends Drawer */}
      {selectedHistoryRoom && (
        <section
          role="region"
          aria-label="Room Historical Trends Drawer"
          style={{
            marginTop: "24px",
            backgroundColor: "#1e293b",
            border: "1px solid #0284c7",
            borderRadius: "10px",
            padding: "20px",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "16px",
              flexWrap: "wrap",
              gap: "10px",
            }}
          >
            <div>
              <h3 style={{ margin: 0, fontSize: "1.2rem", color: "#f8fafc" }}>
                Room Historical Trends: {selectedHistoryRoom.name}
              </h3>
              <p
                style={{
                  margin: "4px 0 0",
                  color: "#94a3b8",
                  fontSize: "0.82rem",
                }}
              >
                Time-series Sonos RF, PHY error rate, ping latency &amp; Wi-Fi telemetry from 24/7 background collector
              </p>
            </div>

            <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
              <div style={{ display: "flex", gap: "4px" }}>
                {(["1h", "24h", "7d"] as const).map((r) => (
                  <button
                    key={r}
                    type="button"
                    disabled={Boolean(busyAction)}
                    onClick={() => void handleChangeHistoryRange(r)}
                    style={{
                      backgroundColor: historyRange === r ? "#0284c7" : "#0f172a",
                      color: "#f8fafc",
                      border: "1px solid #38bdf8",
                      borderRadius: "4px",
                      padding: "4px 10px",
                      fontSize: "0.78rem",
                      fontWeight: 700,
                      cursor: busyAction ? "not-allowed" : "pointer",
                      opacity: busyAction && busyAction !== `history-range-${r}` ? 0.65 : 1,
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "4px",
                    }}
                  >
                    {busyAction === `history-range-${r}` && (
                      <span
                        style={{
                          display: "inline-block",
                          animation: "sonosSpin 1.5s linear infinite",
                        }}
                      >
                        ⏳
                      </span>
                    )}
                    {r}
                  </button>
                ))}
              </div>
              <button
                type="button"
                onClick={() => setSelectedHistoryRoom(null)}
                style={{
                  background: "transparent",
                  border: "1px solid #64748b",
                  borderRadius: "4px",
                  color: "#94a3b8",
                  padding: "4px 10px",
                  cursor: "pointer",
                  fontSize: "0.8rem",
                }}
              >
                Close
              </button>
            </div>
          </div>

          {loadingHistory && (
            <p style={{ color: "#38bdf8" }}>Loading history telemetry...</p>
          )}

          {roomHistory && (
            <div>
              {/* Metric KPI cards */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                  gap: "12px",
                  marginBottom: "16px",
                }}
              >
                <div
                  style={{
                    backgroundColor: "#0f172a",
                    padding: "12px",
                    borderRadius: "8px",
                    border: "1px solid #334155",
                  }}
                >
                  <div style={{ color: "#94a3b8", fontSize: "0.72rem" }}>
                    PEAK OFDM ANI
                  </div>
                  <div
                    style={{
                      fontSize: "1.4rem",
                      fontWeight: 700,
                      color:
                        roomHistory.peak_ani && roomHistory.peak_ani >= 7
                          ? "#ef4444"
                          : "#38bdf8",
                    }}
                  >
                    {roomHistory.peak_ani !== null &&
                    roomHistory.peak_ani !== undefined
                      ? `ANI ${roomHistory.peak_ani}`
                      : "N/A"}
                  </div>
                </div>
                <div
                  style={{
                    backgroundColor: "#0f172a",
                    padding: "12px",
                    borderRadius: "8px",
                    border: "1px solid #334155",
                  }}
                >
                  <div style={{ color: "#94a3b8", fontSize: "0.72rem" }}>
                    AVG PHY ERROR RATE
                  </div>
                  <div
                    style={{
                      fontSize: "1.4rem",
                      fontWeight: 700,
                      color:
                        roomHistory.avg_phy_error_rate &&
                        roomHistory.avg_phy_error_rate > 100
                          ? "#ef4444"
                          : "#10b981",
                    }}
                  >
                    {roomHistory.avg_phy_error_rate !== null &&
                    roomHistory.avg_phy_error_rate !== undefined
                      ? `${roomHistory.avg_phy_error_rate} err/s`
                      : "0.0 err/s"}
                  </div>
                </div>
                <div
                  style={{
                    backgroundColor: "#0f172a",
                    padding: "12px",
                    borderRadius: "8px",
                    border: "1px solid #334155",
                  }}
                >
                  <div style={{ color: "#94a3b8", fontSize: "0.72rem" }}>
                    AVG PING RTT
                  </div>
                  <div
                    style={{
                      fontSize: "1.4rem",
                      fontWeight: 700,
                      color: "#38bdf8",
                    }}
                  >
                    {roomHistory.avg_ping_rtt_ms !== null &&
                    roomHistory.avg_ping_rtt_ms !== undefined
                      ? `${roomHistory.avg_ping_rtt_ms} ms`
                      : "N/A"}
                  </div>
                </div>
                <div
                  style={{
                    backgroundColor: "#0f172a",
                    padding: "12px",
                    borderRadius: "8px",
                    border: "1px solid #334155",
                  }}
                >
                  <div style={{ color: "#94a3b8", fontSize: "0.72rem" }}>
                    TOTAL SAMPLES
                  </div>
                  <div
                    style={{
                      fontSize: "1.4rem",
                      fontWeight: 700,
                      color: "#f8fafc",
                    }}
                  >
                    {roomHistory.total_samples}
                  </div>
                </div>
              </div>

              {/* Narrative Summary */}
              <div
                style={{
                  backgroundColor: "#0f172a",
                  padding: "10px 14px",
                  borderRadius: "6px",
                  marginBottom: "16px",
                  fontSize: "0.82rem",
                  color: "#cbd5e1",
                  borderLeft: "3px solid #0284c7",
                }}
              >
                {roomHistory.summary}
              </div>

              {/* History Samples Timeline Table */}
              <div style={{ overflowX: "auto" }}>
                <table
                  style={{
                    width: "100%",
                    borderCollapse: "collapse",
                    fontSize: "0.78rem",
                  }}
                >
                  <thead>
                    <tr
                      style={{
                        background: "#0f172a",
                        color: "#94a3b8",
                        textAlign: "left",
                      }}
                    >
                      <th style={{ padding: "8px" }}>Timestamp</th>
                      <th style={{ padding: "8px" }}>Peak ANI</th>
                      <th style={{ padding: "8px" }}>PHY Err/s</th>
                      <th style={{ padding: "8px" }}>Ping RTT</th>
                      <th style={{ padding: "8px" }}>5 GHz RSSI</th>
                      <th style={{ padding: "8px" }}>STP Cost</th>
                      <th style={{ padding: "8px" }}>Health Grade</th>
                      <th style={{ padding: "8px" }}>Players</th>
                    </tr>
                  </thead>
                  <tbody>
                    {roomHistory.samples.map((pt, idx) => (
                      <tr
                        key={idx}
                        style={{ borderBottom: "1px solid #334155" }}
                      >
                        <td style={{ padding: "8px", color: "#94a3b8" }}>
                          {pt.timestamp}
                        </td>
                        <td
                          style={{
                            padding: "8px",
                            fontWeight: 700,
                            color:
                              pt.peak_ofdm_ani_level &&
                              pt.peak_ofdm_ani_level >= 7
                                ? "#ef4444"
                                : "#f8fafc",
                          }}
                        >
                          {pt.peak_ofdm_ani_level !== null &&
                          pt.peak_ofdm_ani_level !== undefined
                            ? `ANI ${pt.peak_ofdm_ani_level}`
                            : "N/A"}
                        </td>
                        <td style={{ padding: "8px" }}>
                          {pt.total_phy_error_rate !== null &&
                          pt.total_phy_error_rate !== undefined
                            ? `${pt.total_phy_error_rate} err/s`
                            : "-"}
                        </td>
                        <td style={{ padding: "8px" }}>
                          {pt.avg_ping_rtt_ms !== null &&
                          pt.avg_ping_rtt_ms !== undefined
                            ? `${pt.avg_ping_rtt_ms} ms`
                            : "-"}
                        </td>
                        <td style={{ padding: "8px" }}>
                          {pt.best_5ghz_dbm !== null &&
                          pt.best_5ghz_dbm !== undefined
                            ? `${pt.best_5ghz_dbm} dBm`
                            : "-"}
                        </td>
                        <td style={{ padding: "8px" }}>
                          {pt.worst_stp_path_cost !== null &&
                          pt.worst_stp_path_cost !== undefined
                            ? pt.worst_stp_path_cost
                            : "-"}
                        </td>
                        <td style={{ padding: "8px" }}>
                          <span
                            style={{
                              backgroundColor: "#1e3a8a",
                              padding: "2px 6px",
                              borderRadius: "4px",
                            }}
                          >
                            {pt.health_grade}
                          </span>
                        </td>
                        <td style={{ padding: "8px", color: "#cbd5e1" }}>
                          {pt.players
                            .map((p) => `${p.zone_name} (${p.connection_mode})`)
                            .join(", ") || "-"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </section>
      )}

      {/* Selected Room Wi-Fi Spectrum & Survey Drawer */}
      {selectedRoom && (
        <aside
          aria-label="Room Wi-Fi Spectrum and Survey Drawer"
          style={{
            marginTop: "24px",
            backgroundColor: "#1e293b",
            border: "1px solid #38bdf8",
            borderRadius: "10px",
            padding: "20px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ margin: 0 }}>
              Room Wi-Fi Spectrum &amp; Survey Drawer: {selectedRoom.name}
            </h3>
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
          <p style={{ color: "#cbd5e1", fontSize: "0.85rem", marginBottom: "16px" }}>
            {selectedRoom.description}
          </p>

          {/* Action toolbar for Drawer */}
          <div style={{ display: "flex", gap: "10px", marginBottom: "16px", flexWrap: "wrap" }}>
            <button
              type="button"
              disabled={Boolean(busyAction)}
              onClick={() => void handleLoadSurveyDelta(baselineSurveySlug, targetSurveySlug)}
              style={{
                backgroundColor: "#0284c7",
                color: "#ffffff",
                border: "none",
                borderRadius: "6px",
                padding: "6px 14px",
                fontSize: "0.8rem",
                fontWeight: 600,
                cursor: busyAction ? "not-allowed" : "pointer",
                opacity: busyAction ? 0.65 : 1,
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              {busyAction === "compare-delta" && (
                <span
                  style={{
                    display: "inline-block",
                    animation: "sonosSpin 1.5s linear infinite",
                  }}
                >
                  ⏳
                </span>
              )}
              Compare Surveys / View Delta{busyAction === "compare-delta" ? " (Comparing...)" : ""}
            </button>
          </div>

          {/* Survey Before/After Comparison Delta Region */}
          {deltaOpen && surveyDelta && (
            <section
              role="region"
              aria-label="Survey Before/After Comparison Delta"
              style={{
                backgroundColor: "#0f172a",
                border: "1px solid #38bdf8",
                borderRadius: "8px",
                padding: "16px",
                marginBottom: "20px",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                <h4 style={{ margin: 0, fontSize: "1rem", color: "#38bdf8" }}>
                  Survey Before/After Comparison Delta
                </h4>
                <button
                  type="button"
                  onClick={() => setDeltaOpen(false)}
                  style={{
                    background: "transparent",
                    border: "none",
                    color: "#94a3b8",
                    fontSize: "0.8rem",
                    cursor: "pointer",
                  }}
                >
                  Hide Delta
                </button>
              </div>

              {/* Survey Selectors */}
              <div style={{ display: "flex", gap: "12px", marginBottom: "12px", flexWrap: "wrap" }}>
                <label style={{ fontSize: "0.78rem", color: "#cbd5e1" }}>
                  Baseline Survey:
                  <select
                    value={baselineSurveySlug || surveyDelta.baseline_survey_slug}
                    onChange={(e) => {
                      setBaselineSurveySlug(e.target.value);
                      void handleLoadSurveyDelta(e.target.value, targetSurveySlug || surveyDelta.target_survey_slug);
                    }}
                    style={{
                      display: "block",
                      marginTop: "4px",
                      background: "#1e293b",
                      color: "#f8fafc",
                      border: "1px solid #475569",
                      padding: "4px 8px",
                      borderRadius: "4px",
                    }}
                  >
                    {roomSurveys.map((s) => (
                      <option key={s.survey_slug} value={s.survey_slug}>
                        {s.label} ({s.survey_slug})
                      </option>
                    ))}
                  </select>
                </label>

                <label style={{ fontSize: "0.78rem", color: "#cbd5e1" }}>
                  Target Survey:
                  <select
                    value={targetSurveySlug || surveyDelta.target_survey_slug}
                    onChange={(e) => {
                      setTargetSurveySlug(e.target.value);
                      void handleLoadSurveyDelta(baselineSurveySlug || surveyDelta.baseline_survey_slug, e.target.value);
                    }}
                    style={{
                      display: "block",
                      marginTop: "4px",
                      background: "#1e293b",
                      color: "#f8fafc",
                      border: "1px solid #475569",
                      padding: "4px 8px",
                      borderRadius: "4px",
                    }}
                  >
                    {roomSurveys.map((s) => (
                      <option key={s.survey_slug} value={s.survey_slug}>
                        {s.label} ({s.survey_slug})
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              {/* Narrative Summary */}
              <div
                style={{
                  backgroundColor: "#1e293b",
                  borderRadius: "6px",
                  padding: "10px 14px",
                  marginBottom: "14px",
                  color: "#f8fafc",
                  fontSize: "0.85rem",
                  borderLeft: "4px solid #38bdf8",
                }}
              >
                {surveyDelta.summary_narrative}
              </div>

              {/* Metric Delta Badges */}
              <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginBottom: "16px" }}>
                <span
                  style={{
                    backgroundColor: "#1e293b",
                    padding: "4px 10px",
                    borderRadius: "6px",
                    fontSize: "0.8rem",
                    fontWeight: 600,
                    color: (surveyDelta.delta_5ghz_dbm ?? 0) >= 0 ? "#86efac" : "#fca5a5",
                  }}
                >
                  5 GHz: {surveyDelta.delta_5ghz_dbm != null ? `${surveyDelta.delta_5ghz_dbm > 0 ? "+" : ""}${surveyDelta.delta_5ghz_dbm} dBm` : "N/A"}
                </span>
                <span
                  style={{
                    backgroundColor: "#1e293b",
                    padding: "4px 10px",
                    borderRadius: "6px",
                    fontSize: "0.8rem",
                    fontWeight: 600,
                    color: (surveyDelta.delta_24ghz_dbm ?? 0) >= 0 ? "#86efac" : "#fca5a5",
                  }}
                >
                  2.4 GHz: {surveyDelta.delta_24ghz_dbm != null ? `${surveyDelta.delta_24ghz_dbm > 0 ? "+" : ""}${surveyDelta.delta_24ghz_dbm} dBm` : "N/A"}
                </span>
                <span
                  style={{
                    backgroundColor: "#1e293b",
                    padding: "4px 10px",
                    borderRadius: "6px",
                    fontSize: "0.8rem",
                    fontWeight: 600,
                    color: (surveyDelta.delta_phy_error_rate ?? 0) <= 0 ? "#86efac" : "#fca5a5",
                  }}
                >
                  PHY Err/s: {surveyDelta.delta_phy_error_rate != null ? `${surveyDelta.delta_phy_error_rate > 0 ? "+" : ""}${surveyDelta.delta_phy_error_rate.toFixed(1)} err/s` : "0.0 err/s"}
                </span>
              </div>

              {/* BSSID Diff Table */}
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.78rem" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid #475569", color: "#94a3b8", textAlign: "left" }}>
                      <th style={{ padding: "6px" }}>BSSID</th>
                      <th style={{ padding: "6px" }}>SSID</th>
                      <th style={{ padding: "6px" }}>Band</th>
                      <th style={{ padding: "6px" }}>Baseline RSSI</th>
                      <th style={{ padding: "6px" }}>Target RSSI</th>
                      <th style={{ padding: "6px" }}>Delta RSSI</th>
                      <th style={{ padding: "6px" }}>Classification / Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {surveyDelta.bssid_deltas.map((b) => (
                      <tr key={b.bssid} style={{ borderBottom: "1px solid #1e293b" }}>
                        <td style={{ padding: "6px", color: "#f8fafc", fontFamily: "monospace" }}>{b.bssid}</td>
                        <td style={{ padding: "6px", color: "#cbd5e1" }}>{b.ssid ?? "N/A"}</td>
                        <td style={{ padding: "6px", color: "#94a3b8" }}>{b.band} (Ch {b.channel})</td>
                        <td style={{ padding: "6px", color: "#cbd5e1" }}>{b.baseline_rssi_dbm != null ? `${b.baseline_rssi_dbm} dBm` : "N/A"}</td>
                        <td style={{ padding: "6px", color: "#cbd5e1" }}>{b.target_rssi_dbm != null ? `${b.target_rssi_dbm} dBm` : "N/A"}</td>
                        <td style={{ padding: "6px", fontWeight: 700, color: (b.delta_rssi_dbm ?? 0) >= 0 ? "#86efac" : "#fca5a5" }}>
                          {b.delta_rssi_dbm != null ? `${b.delta_rssi_dbm > 0 ? "+" : ""}${b.delta_rssi_dbm} dBm` : "N/A"}
                        </td>
                        <td style={{ padding: "6px" }}>
                          {b.is_vanished ? (
                            <span style={{ backgroundColor: "#7f1d1d", color: "#fca5a5", padding: "1px 6px", borderRadius: "4px", fontWeight: 700 }}>
                              VANISHED
                            </span>
                          ) : b.is_new ? (
                            <span style={{ backgroundColor: "#064e3b", color: "#6ee7b7", padding: "1px 6px", borderRadius: "4px", fontWeight: 700 }}>
                              NEW
                            </span>
                          ) : (
                            <span style={{ color: "#94a3b8" }}>{b.classification}</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {/* Historical & Post-Remediation Surveys with BSSID Spectrum Tables */}
          <div style={{ display: "flex", flexDirection: "column", gap: "16px", marginBottom: "20px" }}>
            {roomSurveys.map((survey) => (
              <div
                key={survey.id ?? survey.survey_slug}
                style={{
                  backgroundColor: "#0f172a",
                  border: "1px solid #334155",
                  borderRadius: "8px",
                  padding: "12px",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "8px",
                    flexWrap: "wrap",
                    gap: "8px",
                  }}
                >
                  <div>
                    <strong style={{ color: "#38bdf8" }}>{survey.label}</strong>
                    <span style={{ color: "#94a3b8", fontSize: "0.8rem", marginLeft: "10px" }}>
                      AP: {survey.best_ap_name ?? "N/A"} ·{" "}
                      {survey.link_speed_mbps != null ? `${survey.link_speed_mbps} Mbps` : "N/A"} ·
                      5 GHz: {survey.best_5ghz_dbm ?? "N/A"} dBm · 2.4 GHz:{" "}
                      {survey.best_24ghz_dbm ?? "N/A"} dBm
                    </span>
                  </div>
                  <span
                    style={{
                      backgroundColor: (
                        GRADE_COLORS[survey.wifi_health_grade] ?? GRADE_COLORS.GOOD
                      ).bg,
                      color: (GRADE_COLORS[survey.wifi_health_grade] ?? GRADE_COLORS.GOOD).text,
                      padding: "2px 8px",
                      borderRadius: "999px",
                      fontSize: "0.72rem",
                      fontWeight: 700,
                    }}
                  >
                    {survey.wifi_health_grade}
                  </span>
                </div>

                <table
                  style={{
                    width: "100%",
                    borderCollapse: "collapse",
                    fontSize: "0.8rem",
                    textAlign: "left",
                  }}
                >
                  <thead>
                    <tr style={{ borderBottom: "1px solid #334155", color: "#94a3b8" }}>
                      <th style={{ padding: "6px" }}>SSID</th>
                      <th style={{ padding: "6px" }}>BSSID</th>
                      <th style={{ padding: "6px" }}>Band</th>
                      <th style={{ padding: "6px" }}>Channel (Width)</th>
                      <th style={{ padding: "6px" }}>RSSI</th>
                      <th style={{ padding: "6px" }}>Classification</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(survey.readings ?? []).map((b, idx) => {
                      const clsStyle =
                        BSSID_CLASS_COLORS[b.classification] ?? BSSID_CLASS_COLORS.NEIGHBOR_WIFI;
                      return (
                        <tr
                          key={b.id ?? `${b.bssid}-${idx}`}
                          style={{ borderBottom: "1px solid #1e293b" }}
                        >
                          <td style={{ padding: "6px", fontWeight: 600 }}>{b.ssid}</td>
                          <td style={{ padding: "6px", fontFamily: "monospace" }}>{b.bssid}</td>
                          <td style={{ padding: "6px" }}>{b.band}</td>
                          <td style={{ padding: "6px" }}>
                            Ch {b.channel} ({b.width_mhz} MHz)
                          </td>
                          <td style={{ padding: "6px", fontWeight: 700 }}>{b.rssi_dbm} dBm</td>
                          <td style={{ padding: "6px" }}>
                            <span
                              style={{
                                backgroundColor: clsStyle.bg,
                                color: clsStyle.text,
                                border: `1px solid ${clsStyle.border}`,
                                padding: "2px 8px",
                                borderRadius: "999px",
                                fontSize: "0.7rem",
                                fontWeight: 700,
                              }}
                            >
                              {b.classification}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ))}
          </div>

          {/* Record New WiFiRoomSurvey Form */}
          <form
            onSubmit={handleCreateRoomSurvey}
            style={{
              backgroundColor: "#0f172a",
              border: "1px solid #334155",
              borderRadius: "8px",
              padding: "14px",
            }}
          >
            <h4 style={{ marginTop: 0, marginBottom: "10px", color: "#38bdf8" }}>
              Record Room Wi-Fi Survey
            </h4>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
                gap: "10px",
                marginBottom: "12px",
              }}
            >
              <label style={{ fontSize: "0.78rem" }}>
                Survey Label
                <input
                  type="text"
                  value={surveyLabel}
                  onChange={(e) => setSurveyLabel(e.target.value)}
                  placeholder="e.g. Walkthrough Check"
                  style={{
                    width: "100%",
                    padding: "6px",
                    marginTop: "4px",
                    background: "#1e293b",
                    color: "#f8fafc",
                    border: "1px solid #475569",
                    borderRadius: "4px",
                  }}
                />
              </label>
              <label style={{ fontSize: "0.78rem" }}>
                Covering AP
                <input
                  type="text"
                  value={surveyApName}
                  onChange={(e) => setSurveyApName(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "6px",
                    marginTop: "4px",
                    background: "#1e293b",
                    color: "#f8fafc",
                    border: "1px solid #475569",
                    borderRadius: "4px",
                  }}
                />
              </label>
              <label style={{ fontSize: "0.78rem" }}>
                Link Speed (Mbps)
                <input
                  type="number"
                  value={surveyLinkSpeed}
                  onChange={(e) => setSurveyLinkSpeed(Number(e.target.value))}
                  style={{
                    width: "100%",
                    padding: "6px",
                    marginTop: "4px",
                    background: "#1e293b",
                    color: "#f8fafc",
                    border: "1px solid #475569",
                    borderRadius: "4px",
                  }}
                />
              </label>
              <label style={{ fontSize: "0.78rem" }}>
                BSSID
                <input
                  type="text"
                  value={surveyBssid}
                  onChange={(e) => setSurveyBssid(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "6px",
                    marginTop: "4px",
                    background: "#1e293b",
                    color: "#f8fafc",
                    border: "1px solid #475569",
                    borderRadius: "4px",
                  }}
                />
              </label>
              <label style={{ fontSize: "0.78rem" }}>
                SSID
                <input
                  type="text"
                  value={surveySsid}
                  onChange={(e) => setSurveySsid(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "6px",
                    marginTop: "4px",
                    background: "#1e293b",
                    color: "#f8fafc",
                    border: "1px solid #475569",
                    borderRadius: "4px",
                  }}
                />
              </label>
              <label style={{ fontSize: "0.78rem" }}>
                Band
                <select
                  value={surveyBand}
                  onChange={(e) => setSurveyBand(e.target.value as "2.4GHz" | "5GHz")}
                  style={{
                    width: "100%",
                    padding: "6px",
                    marginTop: "4px",
                    background: "#1e293b",
                    color: "#f8fafc",
                    border: "1px solid #475569",
                    borderRadius: "4px",
                  }}
                >
                  <option value="5GHz">5GHz</option>
                  <option value="2.4GHz">2.4GHz</option>
                </select>
              </label>
              <label style={{ fontSize: "0.78rem" }}>
                Channel
                <input
                  type="number"
                  value={surveyChannel}
                  onChange={(e) => setSurveyChannel(Number(e.target.value))}
                  style={{
                    width: "100%",
                    padding: "6px",
                    marginTop: "4px",
                    background: "#1e293b",
                    color: "#f8fafc",
                    border: "1px solid #475569",
                    borderRadius: "4px",
                  }}
                />
              </label>
              <label style={{ fontSize: "0.78rem" }}>
                Width (MHz)
                <input
                  type="number"
                  value={surveyWidth}
                  onChange={(e) => setSurveyWidth(Number(e.target.value))}
                  style={{
                    width: "100%",
                    padding: "6px",
                    marginTop: "4px",
                    background: "#1e293b",
                    color: "#f8fafc",
                    border: "1px solid #475569",
                    borderRadius: "4px",
                  }}
                />
              </label>
              <label style={{ fontSize: "0.78rem" }}>
                RSSI (dBm)
                <input
                  type="number"
                  value={surveyRssi}
                  onChange={(e) => setSurveyRssi(Number(e.target.value))}
                  style={{
                    width: "100%",
                    padding: "6px",
                    marginTop: "4px",
                    background: "#1e293b",
                    color: "#f8fafc",
                    border: "1px solid #475569",
                    borderRadius: "4px",
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
                padding: "8px 14px",
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              Record Room Wi-Fi Survey
            </button>
          </form>
        </aside>
      )}

      {/* Plain Language Room Health Advisor Modal */}
      <PlainLanguageAdvisorModal
        isOpen={Boolean(advisorRoom)}
        room={advisorRoom}
        onClose={() => setAdvisorRoom(null)}
        onActionComplete={(msg) => setActionBanner(msg)}
      />
    </div>
  );
}
