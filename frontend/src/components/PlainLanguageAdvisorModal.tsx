import React, { useState, useEffect } from "react";
import {
  RoomMatrixItem,
  RoomDiagnosticSummary,
  SolutionProposal,
  HealthGrade,
} from "../types/topology";
import { fetchRoomDiagnostics, flushGhostGroups, pollLiveSonosNow, runPingSweep } from "../api/topologyApi";

interface PlainLanguageAdvisorModalProps {
  isOpen: boolean;
  room: RoomMatrixItem | null;
  onClose: () => void;
  onActionComplete?: (message: string) => void;
}

export const PlainLanguageAdvisorModal: React.FC<PlainLanguageAdvisorModalProps> = ({
  isOpen,
  room,
  onClose,
  onActionComplete,
}) => {
  const [activeTab, setActiveTab] = useState<"ROOT_CAUSE" | "RECOMMENDED_ACTION">("ROOT_CAUSE");
  const [diagnostics, setDiagnostics] = useState<RoomDiagnosticSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState<boolean>(false);
  const [executingAction, setExecutingAction] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !room) {
      setDiagnostics(null);
      setError(null);
      return;
    }

    let active = true;
    const loadDiagnostics = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await fetchRoomDiagnostics(room.slug);
        if (active) {
          setDiagnostics(data);
        }
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "Failed to load room diagnostics");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    void loadDiagnostics();
    return () => {
      active = false;
    };
  }, [isOpen, room]);

  if (!isOpen || !room) return null;

  // Determine Primary Rule / Problem Code
  const topDiag = diagnostics?.diagnostics?.[0];
  const ruleCode = topDiag?.rule_code ?? "";
  const isMultihop =
    ruleCode === "STP_MULTIHOP_DETOUR" ||
    room.top_diagnostic_title?.toLowerCase().includes("multi-hop") ||
    room.top_diagnostic_title?.toLowerCase().includes("detour");
  const isEmiSpike =
    ruleCode === "EMI_NON_WIFI_SPIKE" ||
    room.top_diagnostic_title?.toLowerCase().includes("emi");
  const isBasementTrap =
    ruleCode === "BASEMENT_ROOT_TRAP" ||
    room.top_diagnostic_title?.toLowerCase().includes("basement");
  const isAirtimeSaturation =
    ruleCode === "SONOSNET_AIRTIME_SATURATION" ||
    room.top_diagnostic_title?.toLowerCase().includes("airtime");
  const isGhostGroup =
    ruleCode === "GHOST_GROUP_MISMATCH" ||
    room.top_diagnostic_title?.toLowerCase().includes("ghost");
  const isWeakWifi =
    ruleCode === "WIFI_WEAK_COVERAGE" ||
    room.top_diagnostic_title?.toLowerCase().includes("weak");

  const availablePort = room.switch_ports?.[0];
  const portBadge = availablePort
    ? `Switch Port ${availablePort.port_number} (${availablePort.connected_device_label || "Wall Jack"})`
    : null;

  // 1-Click Action Handlers
  const handleExecuteAction = async (action: string) => {
    setExecutingAction(action);
    try {
      if (action === "FLUSH_GHOST_GROUPS") {
        const res = await flushGhostGroups();
        onActionComplete?.(
          `Flushed ghost groups on ${res.flushed_count} zones: ${res.flushed_zones.join(", ") || "All clean"}`
        );
      } else if (action === "POLL_NOW") {
        const res = await pollLiveSonosNow();
        onActionComplete?.(`Polled live Sonos snapshot: ${res.reachable_players}/${res.total_players} reachable`);
      } else if (action === "RUN_PING_JITTER_SWEEP") {
        const res = await runPingSweep();
        onActionComplete?.(
          `Ping sweep complete: Avg ${res.avg_rtt_ms.toFixed(1)} ms, Max ${res.max_rtt_ms.toFixed(1)} ms`
        );
      }
      // Reload room diagnostics
      const updated = await fetchRoomDiagnostics(room.slug);
      setDiagnostics(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to execute action");
    } finally {
      setExecutingAction(null);
    }
  };

  const gradeColor =
    room.health_grade === "CRITICAL"
      ? { bg: "#7f1d1d", text: "#fca5a5", border: "#ef4444" }
      : room.health_grade === "MARGINAL"
      ? { bg: "#78350f", text: "#fde68a", border: "#f59e0b" }
      : { bg: "#064e3b", text: "#86efac", border: "#10b981" };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="advisor-modal-title"
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(0, 0, 0, 0.75)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 99999,
        padding: "16px",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        style={{
          backgroundColor: "#0f172a",
          border: `2px solid ${gradeColor.border}`,
          borderRadius: "14px",
          width: "100%",
          maxWidth: "760px",
          maxHeight: "90vh",
          display: "flex",
          flexDirection: "column",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.6)",
          overflow: "hidden",
        }}
      >
        {/* Modal Header */}
        <div
          style={{
            padding: "18px 24px",
            borderBottom: "1px solid #334155",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            backgroundColor: "#1e293b",
          }}
        >
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span style={{ fontSize: "1.4rem" }}>💡</span>
              <h2
                id="advisor-modal-title"
                style={{ margin: 0, fontSize: "1.25rem", color: "#f8fafc", fontWeight: 700 }}
              >
                Room Health Advisor: {room.name}
              </h2>
              <span
                style={{
                  backgroundColor: gradeColor.bg,
                  color: gradeColor.text,
                  border: `1px solid ${gradeColor.border}`,
                  padding: "2px 10px",
                  borderRadius: "999px",
                  fontSize: "0.72rem",
                  fontWeight: 800,
                  letterSpacing: "0.05em",
                }}
              >
                {room.health_grade}
              </span>
            </div>
            <p style={{ margin: "4px 0 0", color: "#94a3b8", fontSize: "0.82rem" }}>
              Plain-Language Root Cause &amp; Step-by-Step Action Guide
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close Advisor"
            style={{
              background: "#334155",
              border: "none",
              color: "#cbd5e1",
              borderRadius: "6px",
              padding: "6px 12px",
              fontSize: "0.85rem",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            ✕ Close
          </button>
        </div>

        {/* Tab Navigation */}
        <div
          style={{
            display: "flex",
            borderBottom: "1px solid #334155",
            backgroundColor: "#0b1329",
          }}
        >
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "ROOT_CAUSE"}
            onClick={() => setActiveTab("ROOT_CAUSE")}
            style={{
              flex: 1,
              padding: "12px 16px",
              background: activeTab === "ROOT_CAUSE" ? "#0f172a" : "transparent",
              color: activeTab === "ROOT_CAUSE" ? "#38bdf8" : "#94a3b8",
              border: "none",
              borderBottom: activeTab === "ROOT_CAUSE" ? "3px solid #38bdf8" : "3px solid transparent",
              fontSize: "0.92rem",
              fontWeight: 700,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
            }}
          >
            <span>🔍</span>
            <span>What is the Root Cause?</span>
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "RECOMMENDED_ACTION"}
            onClick={() => setActiveTab("RECOMMENDED_ACTION")}
            style={{
              flex: 1,
              padding: "12px 16px",
              background: activeTab === "RECOMMENDED_ACTION" ? "#0f172a" : "transparent",
              color: activeTab === "RECOMMENDED_ACTION" ? "#4ade80" : "#94a3b8",
              border: "none",
              borderBottom: activeTab === "RECOMMENDED_ACTION" ? "3px solid #4ade80" : "3px solid transparent",
              fontSize: "0.92rem",
              fontWeight: 700,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
            }}
          >
            <span>🛠️</span>
            <span>How do I Fix It? (Recommended Steps)</span>
          </button>
        </div>

        {/* Modal Body Content */}
        <div style={{ padding: "20px 24px", overflowY: "auto", flex: 1 }}>
          {loading && (
            <div style={{ textAlign: "center", padding: "30px", color: "#94a3b8" }}>
              <span style={{ fontSize: "1.5rem", display: "inline-block", animation: "sonosSpin 1.5s linear infinite" }}>
                ⏳
              </span>
              <p style={{ marginTop: "10px", fontSize: "0.9rem" }}>Analyzing room telemetry and health factors...</p>
            </div>
          )}

          {error && (
            <div style={{ backgroundColor: "#7f1d1d", color: "#fecaca", padding: "12px 16px", borderRadius: "8px", marginBottom: "16px" }}>
              <strong>Notice:</strong> {error}
            </div>
          )}

          {!loading && activeTab === "ROOT_CAUSE" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {/* Problem Headline Banner */}
              <div
                style={{
                  backgroundColor: gradeColor.bg,
                  border: `1px solid ${gradeColor.border}`,
                  borderRadius: "8px",
                  padding: "14px 18px",
                }}
              >
                <div style={{ fontSize: "0.8rem", color: gradeColor.text, fontWeight: 700, marginBottom: "4px" }}>
                  {room.health_grade === "CRITICAL"
                    ? "CRITICAL ISSUE DETECTED"
                    : room.health_grade === "MARGINAL"
                    ? "PERFORMANCE WARNING"
                    : "ROOM STATUS HEALTHY"}
                </div>
                <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff" }}>
                  {isMultihop
                    ? "Audio Signal Detour Between Floors (Multi-Hop Wireless Relay)"
                    : isEmiSpike
                    ? "Severe Electrical Interference from Nearby Electronics"
                    : isBasementTrap
                    ? "Basement Speaker Trapped as Network Master"
                    : isAirtimeSaturation
                    ? "Too Many Wireless Speakers on One 2.4 GHz Channel"
                    : isWeakWifi
                    ? "Weak Wi-Fi Reception in this Room"
                    : isGhostGroup
                    ? "Sonos Room Group Desynchronization"
                    : room.health_grade === "GOOD" || room.health_grade === "EXCELLENT"
                    ? "Clean & Stable Audio Playback — No Active Issues"
                    : room.top_diagnostic_title || "Network Attention Needed"}
                </div>
              </div>

              {/* Plain English Story / Explanation */}
              <div
                style={{
                  backgroundColor: "#1e293b",
                  borderRadius: "8px",
                  padding: "16px 20px",
                  fontSize: "0.9rem",
                  lineHeight: "1.6",
                  color: "#cbd5e1",
                }}
              >
                <h4 style={{ margin: "0 0 10px", color: "#38bdf8", fontSize: "0.95rem" }}>
                  What is happening in {room.name}?
                </h4>

                {isMultihop ? (
                  <>
                    <p style={{ margin: "0 0 12px" }}>
                      The speaker in <strong>{room.name}</strong> is physically separated from the main Living Room
                      music coordinator by thick ceilings and distance. Because a direct wireless link is too weak,
                      the speaker cannot talk directly to the coordinator.
                    </p>
                    <p style={{ margin: "0 0 12px" }}>
                      Instead, its audio signal has to <strong>relay ("hop") through other upstairs speakers first</strong> before
                      reaching the ground floor. Think of it like a game of telephone: every extra wireless hop halves
                      available transmission speed and adds latency.
                    </p>
                    <p style={{ margin: 0 }}>
                      <strong>Why this causes problems:</strong> When playing to multiple rooms at once, this multi-hop
                      detour causes audio buffer underruns, resulting in <em>stuttering, volume fluctuations, or songs cutting out</em>.
                    </p>
                  </>
                ) : isEmiSpike ? (
                  <>
                    <p style={{ margin: "0 0 12px" }}>
                      A nearby electrical device (such as a <strong>laptop USB-C dock, power adapter, or external monitor</strong>)
                      is leaking radio noise on the 2.4 GHz band directly into this room.
                    </p>
                    <p style={{ margin: 0 }}>
                      This electrical noise jams the speaker's internal radio antennas. Even if your internet is fast,
                      the speaker cannot clearly hear incoming audio packets, causing high framing errors and sudden dropouts.
                    </p>
                  </>
                ) : isBasementTrap ? (
                  <>
                    <p style={{ margin: "0 0 12px" }}>
                      The basement speaker became the master root bridge for the sound system. However, the basement
                      is surrounded by reinforced concrete that blocks radio waves to the upper floors.
                    </p>
                    <p style={{ margin: 0 }}>
                      Because the master is trapped underground, all upper-floor speakers struggle to maintain contact.
                    </p>
                  </>
                ) : isAirtimeSaturation ? (
                  <>
                    <p style={{ margin: "0 0 12px" }}>
                      More than 10 Sonos speakers are sharing the single 2.4 GHz wireless channel (Channel 6).
                    </p>
                    <p style={{ margin: 0 }}>
                      The wireless airtime is saturated. When streaming high-resolution audio to the entire house,
                      Sonos dynamically lowers the volume (ducking) to protect audio sync.
                    </p>
                  </>
                ) : isWeakWifi ? (
                  <>
                    <p style={{ margin: "0 0 12px" }}>
                      The Wi-Fi signal from your access points reaching {room.name} is weak (below -70 dBm).
                    </p>
                    <p style={{ margin: 0 }}>
                      Wall materials and distance are attenuating the signal, causing low link rates and packet retries.
                    </p>
                  </>
                ) : (
                  <p style={{ margin: 0 }}>
                    The network path and radio telemetry in {room.name} are clean. The speaker has a direct, low-latency
                    connection to the living room root bridge with zero electrical interference.
                  </p>
                )}
              </div>

              {/* Radio Environment Reality Check Cards */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "10px" }}>
                <div style={{ backgroundColor: "#1e293b", padding: "12px 14px", borderRadius: "8px", border: "1px solid #334155" }}>
                  <div style={{ fontSize: "0.72rem", color: "#94a3b8", textTransform: "uppercase", fontWeight: 700 }}>
                    Local Electrical Noise
                  </div>
                  <div style={{ fontSize: "0.92rem", fontWeight: 700, color: isEmiSpike ? "#f87171" : "#86efac", marginTop: "4px" }}>
                    {isEmiSpike ? "🔴 Severe 2.4 GHz Noise Spike" : "✅ Clean (No Electrical Jamming)"}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "2px" }}>
                    {isEmiSpike ? "Nearby chargers/docks creating noise" : "Hardware & room environment clean"}
                  </div>
                </div>

                <div style={{ backgroundColor: "#1e293b", padding: "12px 14px", borderRadius: "8px", border: "1px solid #334155" }}>
                  <div style={{ fontSize: "0.72rem", color: "#94a3b8", textTransform: "uppercase", fontWeight: 700 }}>
                    Wireless Connection Path
                  </div>
                  <div style={{ fontSize: "0.92rem", fontWeight: 700, color: isMultihop ? "#fbbf24" : "#86efac", marginTop: "4px" }}>
                    {isMultihop ? "⚠️ Multi-Hop Relay Detour" : "✅ Direct Upstream Route"}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "2px" }}>
                    {isMultihop ? "Hopping through intermediate rooms" : "Direct connection to root"}
                  </div>
                </div>

                <div style={{ backgroundColor: "#1e293b", padding: "12px 14px", borderRadius: "8px", border: "1px solid #334155" }}>
                  <div style={{ fontSize: "0.72rem", color: "#94a3b8", textTransform: "uppercase", fontWeight: 700 }}>
                    Home Wi-Fi Strength (5 GHz)
                  </div>
                  <div style={{ fontSize: "0.92rem", fontWeight: 700, color: (room.best_5ghz_rssi_dbm ?? -99) >= -67 ? "#86efac" : "#fbbf24", marginTop: "4px" }}>
                    {room.best_5ghz_rssi_dbm != null ? `${room.best_5ghz_rssi_dbm} dBm` : "N/A"}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "2px" }}>
                    From {room.best_ap_name ?? "Access Point"}
                  </div>
                </div>
              </div>

              {/* Technical Telemetry Dropdown */}
              <div style={{ borderTop: "1px solid #334155", paddingTop: "12px" }}>
                <button
                  type="button"
                  onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
                  style={{
                    background: "transparent",
                    border: "none",
                    color: "#38bdf8",
                    fontSize: "0.8rem",
                    fontWeight: 600,
                    cursor: "pointer",
                    padding: 0,
                  }}
                >
                  {showTechnicalDetails ? "▲ Hide Technical Telemetry Details" : "▼ Show Technical Engineering Telemetry (Advanced)"}
                </button>

                {showTechnicalDetails && (
                  <div
                    style={{
                      marginTop: "10px",
                      backgroundColor: "#0b1329",
                      padding: "12px",
                      borderRadius: "6px",
                      fontSize: "0.76rem",
                      color: "#94a3b8",
                      fontFamily: "monospace",
                    }}
                  >
                    <div>Room Slug: {room.slug} | Health Grade: {room.health_grade}</div>
                    <div>Top Diagnostic: {room.top_diagnostic_title ?? "None"}</div>
                    {availablePort && (
                      <div>Wall Port: Port {availablePort.port_number} (VLAN {availablePort.pvid ?? 10})</div>
                    )}
                    {topDiag?.evidence && (
                      <pre style={{ margin: "6px 0 0", color: "#cbd5e1", whiteSpace: "pre-wrap" }}>
                        {JSON.stringify(topDiag.evidence, null, 2)}
                      </pre>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {!loading && activeTab === "RECOMMENDED_ACTION" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {/* Option 1: The Gold Standard Permanent Fix */}
              {isMultihop && availablePort ? (
                <div
                  style={{
                    backgroundColor: "#064e3b",
                    border: "2px solid #10b981",
                    borderRadius: "10px",
                    padding: "18px 20px",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                    <span
                      style={{
                        backgroundColor: "#10b981",
                        color: "#022c22",
                        padding: "2px 8px",
                        borderRadius: "4px",
                        fontSize: "0.72rem",
                        fontWeight: 800,
                      }}
                    >
                      🌟 BEST SOLUTION (PERMANENT FIX)
                    </span>
                    <span style={{ color: "#a7f3d0", fontSize: "0.78rem", fontWeight: 600 }}>
                      Takes ~2 minutes
                    </span>
                  </div>

                  <h3 style={{ margin: "0 0 10px", color: "#ffffff", fontSize: "1.08rem" }}>
                    Plug into Ethernet Wall Socket + Turn Off Speaker Wi-Fi
                  </h3>

                  <div style={{ fontSize: "0.88rem", color: "#d1fae5", lineHeight: "1.6" }}>
                    <p style={{ margin: "0 0 10px" }}>
                      You already have an active, dedicated network wall socket in this room:{" "}
                      <strong>{portBadge}</strong>.
                    </p>

                    <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "10px" }}>
                      <div style={{ display: "flex", gap: "10px", alignItems: "start" }}>
                        <span style={{ backgroundColor: "#047857", color: "#fff", width: "22px", height: "22px", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.75rem", fontWeight: 700, flexShrink: 0 }}>
                          1
                        </span>
                        <div>
                          <strong>Plug in an Ethernet cable:</strong> Connect a network cable from the back of the speaker into the wall jack.
                        </div>
                      </div>

                      <div style={{ display: "flex", gap: "10px", alignItems: "start" }}>
                        <span style={{ backgroundColor: "#047857", color: "#fff", width: "22px", height: "22px", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.75rem", fontWeight: 700, flexShrink: 0 }}>
                          2
                        </span>
                        <div>
                          <strong>Turn off Wi-Fi on the speaker:</strong> In the Sonos app, go to{" "}
                          <em>Settings ➔ System ➔ Products ➔ {room.name} ➔ Turn off Wi-Fi</em>.
                          <div style={{ fontSize: "0.8rem", color: "#a7f3d0", marginTop: "2px" }}>
                            💡 <em>Why?</em> This forces the speaker to use the ultra-fast cable and prevents it from competing with the living room for network leadership.
                          </div>
                        </div>
                      </div>
                    </div>

                    <div style={{ marginTop: "14px", padding: "10px 12px", backgroundColor: "#044e39", borderRadius: "6px", fontSize: "0.82rem", color: "#a7f3d0" }}>
                      ✅ <strong>Result:</strong> Connection path cost drops from 528 down to 10. Flawless audio playback with zero multi-hop lag.
                    </div>
                  </div>
                </div>
              ) : isEmiSpike ? (
                <div
                  style={{
                    backgroundColor: "#451a03",
                    border: "2px solid #f59e0b",
                    borderRadius: "10px",
                    padding: "18px 20px",
                  }}
                >
                  <span
                    style={{
                      backgroundColor: "#f59e0b",
                      color: "#451a03",
                      padding: "2px 8px",
                      borderRadius: "4px",
                      fontSize: "0.72rem",
                      fontWeight: 800,
                    }}
                  >
                    RECOMMENDED ACTION: EMI ISOLATION
                  </span>

                  <h3 style={{ margin: "10px 0 8px", color: "#ffffff", fontSize: "1.08rem" }}>
                    Identify &amp; Relocate Electrical Noise Source
                  </h3>

                  <div style={{ fontSize: "0.88rem", color: "#fef3c7", lineHeight: "1.6" }}>
                    <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "10px" }}>
                      <div style={{ display: "flex", gap: "10px", alignItems: "start" }}>
                        <span style={{ backgroundColor: "#b45309", color: "#fff", width: "22px", height: "22px", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.75rem", fontWeight: 700, flexShrink: 0 }}>
                          1
                        </span>
                        <div>
                          <strong>Sequential Unplug Test:</strong> Unplug laptop USB-C docks, charging bricks, and monitors near or directly above {room.name} one by one while watching the Live RF meter.
                        </div>
                      </div>

                      <div style={{ display: "flex", gap: "10px", alignItems: "start" }}>
                        <span style={{ backgroundColor: "#b45309", color: "#fff", width: "22px", height: "22px", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.75rem", fontWeight: 700, flexShrink: 0 }}>
                          2
                        </span>
                        <div>
                          <strong>Move the speaker 1–2 meters:</strong> Reposition the speaker laterally away from power transformers or charging hubs.
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : null}

              {/* Option 2: Quick Alternative (Wireless) */}
              <div
                style={{
                  backgroundColor: "#1e293b",
                  border: "1px solid #475569",
                  borderRadius: "10px",
                  padding: "16px 20px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                  <span
                    style={{
                      backgroundColor: "#334155",
                      color: "#93c5fd",
                      padding: "2px 8px",
                      borderRadius: "4px",
                      fontSize: "0.72rem",
                      fontWeight: 700,
                    }}
                  >
                    ALTERNATIVE OPTION (WIRELESS)
                  </span>
                  <span style={{ color: "#94a3b8", fontSize: "0.76rem" }}>
                    If no cable is available
                  </span>
                </div>

                <h4 style={{ margin: "4px 0 8px", color: "#f8fafc", fontSize: "0.98rem" }}>
                  Switch Speaker to 5 GHz Home Wi-Fi (Station Mode)
                </h4>

                <p style={{ margin: "0 0 10px", fontSize: "0.86rem", color: "#cbd5e1", lineHeight: "1.5" }}>
                  In the Sonos App, connect {room.name} directly to your home 5 GHz Wi-Fi (<em>WuTangLan-Family</em>)
                  instead of the 2.4 GHz Sonos wireless mesh. This completely bypasses intermediate relays, exactly like Nicolas in the attic.
                </p>
              </div>

              {/* Option 3: Quick Mesh Renegotiation */}
              <div
                style={{
                  backgroundColor: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: "10px",
                  padding: "14px 18px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  flexWrap: "wrap",
                  gap: "10px",
                }}
              >
                <div>
                  <div style={{ fontWeight: 700, fontSize: "0.9rem", color: "#f8fafc" }}>
                    Quick 10-Second Power Cycle
                  </div>
                  <div style={{ fontSize: "0.8rem", color: "#94a3b8", marginTop: "2px" }}>
                    Unplug {room.name}&apos;s power cord for 10 seconds to force the speaker to re-evaluate nearest wireless routes.
                  </div>
                </div>
              </div>

              {/* 1-Click Helper Actions */}
              <div
                style={{
                  backgroundColor: "#0b1329",
                  border: "1px solid #334155",
                  borderRadius: "8px",
                  padding: "14px 16px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  flexWrap: "wrap",
                  gap: "10px",
                }}
              >
                <div>
                  <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#e2e8f0" }}>
                    Run Live Diagnostic Tools
                  </div>
                  <div style={{ fontSize: "0.74rem", color: "#94a3b8" }}>
                    Trigger real-time telemetry queries to verify changes
                  </div>
                </div>

                <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                  <button
                    type="button"
                    disabled={Boolean(executingAction)}
                    onClick={() => handleExecuteAction("POLL_NOW")}
                    style={{
                      backgroundColor: "#0d9488",
                      color: "#fff",
                      border: "none",
                      borderRadius: "6px",
                      padding: "6px 12px",
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      cursor: executingAction ? "not-allowed" : "pointer",
                      opacity: executingAction ? 0.6 : 1,
                    }}
                  >
                    {executingAction === "POLL_NOW" ? "Polling..." : "Poll Live Telemetry"}
                  </button>

                  <button
                    type="button"
                    disabled={Boolean(executingAction)}
                    onClick={() => handleExecuteAction("RUN_PING_JITTER_SWEEP")}
                    style={{
                      backgroundColor: "#0284c7",
                      color: "#fff",
                      border: "none",
                      borderRadius: "6px",
                      padding: "6px 12px",
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      cursor: executingAction ? "not-allowed" : "pointer",
                      opacity: executingAction ? 0.6 : 1,
                    }}
                  >
                    {executingAction === "RUN_PING_JITTER_SWEEP" ? "Sweeping..." : "Run Ping Sweep"}
                  </button>

                  {isGhostGroup && (
                    <button
                      type="button"
                      disabled={Boolean(executingAction)}
                      onClick={() => handleExecuteAction("FLUSH_GHOST_GROUPS")}
                      style={{
                        backgroundColor: "#dc2626",
                        color: "#fff",
                        border: "none",
                        borderRadius: "6px",
                        padding: "6px 12px",
                        fontSize: "0.75rem",
                        fontWeight: 700,
                        cursor: executingAction ? "not-allowed" : "pointer",
                        opacity: executingAction ? 0.6 : 1,
                      }}
                    >
                      {executingAction === "FLUSH_GHOST_GROUPS" ? "Flushing..." : "Flush Ghost Groups"}
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
