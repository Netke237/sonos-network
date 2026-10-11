import React, { useEffect, useMemo, useState } from "react";
import { fetchTopologyGraph } from "../api/topologyApi";
import type {
  DeviceConnectionEdge,
  DeviceRole,
  FloorMatrixItem,
  HealthGrade,
  TopologyGraphResponse,
  TopologyLayerFilter,
  TopologyNode,
} from "../types/topology";

const GRADE_STYLES: Record<HealthGrade, { bg: string; text: string; border: string }> = {
  EXCELLENT: { bg: "#064e3b", text: "#6ee7b7", border: "#10b981" },
  GOOD: { bg: "#14532d", text: "#86efac", border: "#22c55e" },
  MARGINAL: { bg: "#713f12", text: "#fde047", border: "#eab308" },
  CRITICAL: { bg: "#7f1d1d", text: "#fca5a5", border: "#ef4444" },
};

const ROLE_STYLES: Record<DeviceRole, { badgeBg: string; badgeText: string; label: string }> = {
  ROUTER: { badgeBg: "#312e81", badgeText: "#c7d2fe", label: "ROUTER" },
  SWITCH: { badgeBg: "#0f766e", badgeText: "#99f6e4", label: "SWITCH" },
  WIFI_AP: { badgeBg: "#0369a1", badgeText: "#bae6fd", label: "WIFI_AP" },
  SONOS_PLAYER: { badgeBg: "#1e3a8a", badgeText: "#bfdbfe", label: "SONOS_PLAYER" },
  CLIENT_DEVICE: { badgeBg: "#334155", badgeText: "#cbd5e1", label: "CLIENT" },
  EMI_SOURCE: { badgeBg: "#7f1d1d", badgeText: "#fecaca", label: "EMI_SOURCE" },
};

const LAYER_COLORS: Record<string, string> = {
  WIRED_LAN: "#38bdf8",
  WIFI_INFRA: "#a855f7",
  SONOS_MESH: "#10b981",
};

interface TopologyGraphViewProps {
  floors: FloorMatrixItem[];
  onInspectRoomSlug?: (roomSlug: string) => void;
}

export const TopologyGraphView: React.FC<TopologyGraphViewProps> = ({
  floors,
  onInspectRoomSlug,
}) => {
  const [graphData, setGraphData] = useState<TopologyGraphResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [layerFilter, setLayerFilter] = useState<TopologyLayerFilter>("ALL");
  const [showBlockedStp, setShowBlockedStp] = useState<boolean>(true);
  const [selectedFloorSlug, setSelectedFloorSlug] = useState<string>("ALL");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const loadGraph = async () => {
      try {
        setLoading(true);
        const data = await fetchTopologyGraph({
          layer: "ALL",
          include_blocking: true,
        });
        if (active) {
          setGraphData(data);
          setError(null);
        }
      } catch (err) {
        if (active) {
          setError(
            err instanceof Error ? err.message : "Failed to load topology graph"
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };
    void loadGraph();
    return () => {
      active = false;
    };
  }, []);

  const visibleNodes: TopologyNode[] = useMemo(() => {
    if (!graphData) return [];
    return graphData.nodes.filter((node) => {
      if (selectedFloorSlug !== "ALL") {
        return (node.floor_slug ?? "").toLowerCase() === selectedFloorSlug.toLowerCase();
      }
      return true;
    });
  }, [graphData, selectedFloorSlug]);

  const visibleNodeIdSet = useMemo(
    () => new Set(visibleNodes.map((n) => n.id)),
    [visibleNodes]
  );

  const visibleEdges: DeviceConnectionEdge[] = useMemo(() => {
    if (!graphData) return [];
    return graphData.edges.filter((edge) => {
      if (!showBlockedStp && (!edge.is_forwarding || edge.stp_state === "BLOCKING")) {
        return false;
      }
      if (layerFilter === "WIFI_VLAN") {
        if (edge.layer !== "WIFI_INFRA" && edge.layer !== "WIRED_LAN") {
          return false;
        }
      } else if (layerFilter === "SONOS_STP") {
        if (edge.layer !== "SONOS_MESH" && edge.layer !== "WIRED_LAN") {
          return false;
        }
      } else if (
        layerFilter === "WIRED_LAN" ||
        layerFilter === "WIFI_INFRA" ||
        layerFilter === "SONOS_MESH"
      ) {
        if (edge.layer !== layerFilter) {
          return false;
        }
      }

      if (selectedFloorSlug !== "ALL") {
        return (
          visibleNodeIdSet.has(edge.source) || visibleNodeIdSet.has(edge.target)
        );
      }
      return true;
    });
  }, [graphData, layerFilter, showBlockedStp, selectedFloorSlug, visibleNodeIdSet]);

  const nodesById = useMemo(() => {
    const map = new Map<string, TopologyNode>();
    if (graphData) {
      for (const n of graphData.nodes) {
        map.set(n.id, n);
      }
    }
    return map;
  }, [graphData]);

  const selectedNode: TopologyNode | null = useMemo(() => {
    if (!selectedNodeId) return null;
    return nodesById.get(selectedNodeId) ?? null;
  }, [nodesById, selectedNodeId]);

  const connectedEdgesForSelected: DeviceConnectionEdge[] = useMemo(() => {
    if (!selectedNode || !graphData) return [];
    return graphData.edges.filter(
      (e) => e.source === selectedNode.id || e.target === selectedNode.id
    );
  }, [graphData, selectedNode]);

  return (
    <section
      aria-label="Interactive Network Topology Graph"
      style={{
        backgroundColor: "#1e293b",
        borderRadius: "12px",
        padding: "20px",
        border: "1px solid #334155",
      }}
    >
      {/* Top Controls Bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
          marginBottom: "16px",
          paddingBottom: "12px",
          borderBottom: "1px solid #334155",
        }}
      >
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          <button
            type="button"
            onClick={() => setLayerFilter("ALL")}
            style={{
              backgroundColor: layerFilter === "ALL" ? "#0284c7" : "#0f172a",
              color: "#f8fafc",
              border: "1px solid #38bdf8",
              borderRadius: "6px",
              padding: "6px 12px",
              fontSize: "0.82rem",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            All Layers
          </button>
          <button
            type="button"
            onClick={() => setLayerFilter("WIFI_VLAN")}
            style={{
              backgroundColor: layerFilter === "WIFI_VLAN" ? "#7e22ce" : "#0f172a",
              color: "#f8fafc",
              border: "1px solid #a855f7",
              borderRadius: "6px",
              padding: "6px 12px",
              fontSize: "0.82rem",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Wi-Fi &amp; VLAN Layer
          </button>
          <button
            type="button"
            onClick={() => setLayerFilter("SONOS_STP")}
            style={{
              backgroundColor: layerFilter === "SONOS_STP" ? "#059669" : "#0f172a",
              color: "#f8fafc",
              border: "1px solid #10b981",
              borderRadius: "6px",
              padding: "6px 12px",
              fontSize: "0.82rem",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Sonos Mesh &amp; STP Layer
          </button>
        </div>

        <div style={{ display: "flex", gap: "16px", alignItems: "center", flexWrap: "wrap" }}>
          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              fontSize: "0.82rem",
              color: "#e2e8f0",
              cursor: "pointer",
            }}
          >
            <input
              type="checkbox"
              checked={showBlockedStp}
              onChange={(e) => setShowBlockedStp(e.target.checked)}
            />
            Show Blocked STP Links (STP 00)
          </label>

          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              fontSize: "0.82rem",
              color: "#e2e8f0",
            }}
          >
            Floor Filter:
            <select
              aria-label="Floor Filter"
              value={selectedFloorSlug}
              onChange={(e) => setSelectedFloorSlug(e.target.value)}
              style={{
                backgroundColor: "#0f172a",
                color: "#f8fafc",
                border: "1px solid #475569",
                borderRadius: "4px",
                padding: "4px 8px",
                fontSize: "0.82rem",
              }}
            >
              <option value="ALL">All Floors</option>
              {floors.map((f) => (
                <option key={f.id} value={f.slug}>
                  {f.name}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      {/* Legend Strip */}
      <div
        style={{
          display: "flex",
          gap: "16px",
          flexWrap: "wrap",
          fontSize: "0.75rem",
          color: "#94a3b8",
          marginBottom: "14px",
        }}
      >
        <span>
          <strong style={{ color: "#38bdf8" }}>━━</strong> WIRED_LAN (Trunk / VLAN 10)
        </span>
        <span>
          <strong style={{ color: "#a855f7" }}>━━</strong> WIFI_INFRA (EAP650 Ch 44 / Ch 40)
        </span>
        <span>
          <strong style={{ color: "#10b981" }}>━━</strong> SONOS_MESH Active Forwarding (STP 03/04 &amp; 5GHz HT Ch 48)
        </span>
        <span>
          <strong style={{ color: "#64748b" }}>╌╌</strong> SONOS_MESH Blocked Backup Path (STP 00)
        </span>
      </div>

      {loading && <p>Loading network topology graph...</p>}
      {error && <p style={{ color: "#f87171" }}>Error: {error}</p>}

      {!loading && graphData && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: selectedNode ? "1fr 340px" : "1fr",
            gap: "16px",
            alignItems: "start",
          }}
        >
          {/* Interactive 2D SVG + Node Canvas */}
          <div
            style={{
              position: "relative",
              minHeight: "820px",
              backgroundColor: "#0f172a",
              borderRadius: "10px",
              border: "1px solid #334155",
              overflow: "auto",
              padding: "16px",
            }}
          >
            {/* SVG Directed Edge Layer */}
            <svg
              width="1050"
              height="800"
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                pointerEvents: "none",
              }}
            >
              <defs>
                <marker
                  id="arrow-forward"
                  viewBox="0 0 10 10"
                  refX="8"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#38bdf8" />
                </marker>
                <marker
                  id="arrow-blocking"
                  viewBox="0 0 10 10"
                  refX="8"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" />
                </marker>
              </defs>

              {visibleEdges.map((edge) => {
                const src = nodesById.get(edge.source);
                const tgt = nodesById.get(edge.target);
                if (!src || !tgt) return null;

                const x1 = src.x + 85;
                const y1 = src.y + 38;
                const x2 = tgt.x + 85;
                const y2 = tgt.y + 38;

                const isHighlighted =
                  selectedNode &&
                  (edge.source === selectedNode.id || edge.target === selectedNode.id);

                const strokeColor = !edge.is_forwarding
                  ? "#64748b"
                  : isHighlighted
                  ? "#facc15"
                  : LAYER_COLORS[edge.layer] ?? "#38bdf8";

                return (
                  <g key={edge.id}>
                    <line
                      x1={x1}
                      y1={y1}
                      x2={x2}
                      y2={y2}
                      stroke={strokeColor}
                      strokeWidth={isHighlighted ? 3 : 2}
                      strokeDasharray={edge.is_forwarding ? "none" : "6 4"}
                      markerEnd={
                        edge.is_forwarding ? "url(#arrow-forward)" : "url(#arrow-blocking)"
                      }
                    />
                  </g>
                );
              })}
            </svg>

            {/* Edge Label Pills Layer */}
            <div style={{ position: "relative", zIndex: 2, marginBottom: "16px" }}>
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "6px",
                  marginBottom: "12px",
                }}
              >
                {visibleEdges.map((edge) => {
                  const gradeStyle =
                    GRADE_STYLES[edge.health_grade] ?? GRADE_STYLES.GOOD;
                  const isHighlighted =
                    selectedNode &&
                    (edge.source === selectedNode.id || edge.target === selectedNode.id);
                  return (
                    <div
                      key={edge.id}
                      data-testid={`topology-edge-${edge.id}`}
                      style={{
                        fontSize: "0.72rem",
                        padding: "3px 8px",
                        borderRadius: "999px",
                        backgroundColor: isHighlighted ? "#422006" : "#1e293b",
                        color: edge.is_forwarding ? gradeStyle.text : "#94a3b8",
                        border: edge.is_forwarding
                          ? `1px solid ${gradeStyle.border}`
                          : "1px dashed #64748b",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "6px",
                      }}
                    >
                      <span style={{ fontWeight: 700, color: "#cbd5e1" }}>
                        {edge.source_name} ➔ {edge.target_name}:
                      </span>
                      <span>{edge.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Interactive Device Nodes Canvas */}
            <div style={{ position: "relative", width: "1020px", height: "760px" }}>
              {visibleNodes.map((node) => {
                const gradeStyle =
                  GRADE_STYLES[node.health_grade] ?? GRADE_STYLES.GOOD;
                const roleStyle =
                  ROLE_STYLES[node.device_role] ?? ROLE_STYLES.SONOS_PLAYER;
                const isSelected = selectedNode?.id === node.id;
                const isSameRoomSelected =
                  selectedNode &&
                  selectedNode.room_slug &&
                  selectedNode.room_slug === node.room_slug;

                return (
                  <div
                    key={node.id}
                    data-testid={`topology-node-${node.id}`}
                    onClick={() => setSelectedNodeId(node.id)}
                    style={{
                      position: "absolute",
                      left: `${node.x}px`,
                      top: `${node.y}px`,
                      width: "195px",
                      backgroundColor: isSelected
                        ? "#1e3a8a"
                        : isSameRoomSelected
                        ? "#172554"
                        : "#1e293b",
                      border: isSelected
                        ? "2px solid #38bdf8"
                        : `1.5px solid ${gradeStyle.border}`,
                      borderRadius: "8px",
                      padding: "8px 10px",
                      cursor: "pointer",
                      boxShadow: "0 4px 10px rgba(0, 0, 0, 0.35)",
                      zIndex: isSelected ? 10 : 5,
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        gap: "4px",
                        marginBottom: "4px",
                      }}
                    >
                      <span
                        style={{
                          fontSize: "0.62rem",
                          fontWeight: 700,
                          padding: "1px 5px",
                          borderRadius: "4px",
                          backgroundColor: roleStyle.badgeBg,
                          color: roleStyle.badgeText,
                        }}
                      >
                        {roleStyle.label}
                      </span>
                      <span
                        style={{
                          fontSize: "0.62rem",
                          fontWeight: 700,
                          padding: "1px 6px",
                          borderRadius: "999px",
                          backgroundColor: gradeStyle.bg,
                          color: gradeStyle.text,
                        }}
                      >
                        {node.health_grade}
                      </span>
                    </div>

                    <div
                      style={{
                        fontWeight: 700,
                        fontSize: "0.82rem",
                        color: "#f8fafc",
                        marginBottom: "2px",
                      }}
                    >
                      {node.name}
                    </div>

                    <div style={{ fontSize: "0.68rem", color: "#94a3b8" }}>
                      {node.ip_address ?? "Bonded"} ·{" "}
                      {node.connection_mode ?? node.model_name}
                    </div>

                    {node.ap_channels && (
                      <div
                        style={{
                          fontSize: "0.66rem",
                          color: "#38bdf8",
                          marginTop: "3px",
                        }}
                      >
                        {node.ap_channels}
                      </div>
                    )}

                    {node.device_role === "SONOS_PLAYER" && (
                      <div
                        style={{
                          fontSize: "0.66rem",
                          color: "#cbd5e1",
                          marginTop: "3px",
                          display: "flex",
                          flexWrap: "wrap",
                          gap: "6px",
                        }}
                      >
                        <span>
                          {node.ofdm_ani_level != null
                            ? `ANI ${node.ofdm_ani_level}`
                            : "ANI N/A"}
                        </span>
                        {node.phy_error_rate != null && (
                          <span>{`${node.phy_error_rate.toFixed(1)} err/s`}</span>
                        )}
                        {node.stp_path_cost != null && (
                          <span>{`STP Cost ${node.stp_path_cost}`}</span>
                        )}
                        {node.rssi_dbm != null && (
                          <span>{`${node.rssi_dbm} dBm`}</span>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Node Detail Inspector Panel */}
          {selectedNode && (
            <aside
              role="region"
              aria-label="Topology Node Detail Panel"
              style={{
                backgroundColor: "#0f172a",
                border: "1px solid #38bdf8",
                borderRadius: "10px",
                padding: "16px",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "10px",
                }}
              >
                <h3 style={{ margin: 0, fontSize: "1rem", color: "#38bdf8" }}>
                  {selectedNode.name}
                </h3>
                <button
                  type="button"
                  onClick={() => setSelectedNodeId(null)}
                  style={{
                    background: "transparent",
                    border: "none",
                    color: "#94a3b8",
                    cursor: "pointer",
                    fontSize: "0.8rem",
                  }}
                >
                  Close
                </button>
              </div>

              <div
                style={{
                  fontSize: "0.8rem",
                  color: "#cbd5e1",
                  display: "flex",
                  flexDirection: "column",
                  gap: "6px",
                  marginBottom: "14px",
                }}
              >
                <div>
                  <strong>Role / Model:</strong> {selectedNode.device_role} ·{" "}
                  {selectedNode.model_name}
                </div>
                <div>
                  <strong>Room / Floor:</strong> {selectedNode.room_name ?? "N/A"} (
                  {selectedNode.floor_name ?? "N/A"})
                </div>
                <div>
                  <strong>IP Address:</strong> {selectedNode.ip_address ?? "Bonded"}
                </div>
                {selectedNode.connection_mode && (
                  <div>
                    <strong>Connection Mode:</strong> {selectedNode.connection_mode}
                  </div>
                )}
                {selectedNode.stp_path_cost != null && (
                  <div>
                    <strong>STP Path Cost:</strong> {selectedNode.stp_path_cost}
                    {selectedNode.is_stp_root ? " (Designated STP Root Bridge)" : ""}
                  </div>
                )}
                {selectedNode.ofdm_ani_level !== undefined && (
                  <div>
                    <strong>OFDM ANI Level:</strong>{" "}
                    {selectedNode.ofdm_ani_level != null
                      ? selectedNode.ofdm_ani_level
                      : "N/A"}
                  </div>
                )}
                {selectedNode.phy_error_rate != null && (
                  <div>
                    <strong>PHY Error Velocity:</strong>{" "}
                    {selectedNode.phy_error_rate.toFixed(1)} err/s
                  </div>
                )}
                {selectedNode.ap_channels && (
                  <div>
                    <strong>AP Channels:</strong> {selectedNode.ap_channels}
                  </div>
                )}
              </div>

              {selectedNode.room_slug && onInspectRoomSlug && (
                <button
                  type="button"
                  onClick={() => onInspectRoomSlug(selectedNode.room_slug!)}
                  style={{
                    width: "100%",
                    backgroundColor: "#0284c7",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "6px",
                    padding: "8px 12px",
                    fontSize: "0.8rem",
                    fontWeight: 600,
                    cursor: "pointer",
                    marginBottom: "14px",
                  }}
                >
                  Inspect Room ({selectedNode.room_name})
                </button>
              )}

              <h4
                style={{
                  margin: "0 0 8px",
                  fontSize: "0.85rem",
                  color: "#e2e8f0",
                }}
              >
                Connected Edges ({connectedEdgesForSelected.length})
              </h4>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                {connectedEdgesForSelected.map((edge) => (
                  <div
                    key={edge.id}
                    style={{
                      backgroundColor: "#1e293b",
                      border: edge.is_forwarding
                        ? "1px solid #334155"
                        : "1px dashed #64748b",
                      borderRadius: "6px",
                      padding: "6px 8px",
                      fontSize: "0.75rem",
                    }}
                  >
                    <div style={{ fontWeight: 600, color: "#f8fafc" }}>
                      {edge.source_name} ➔ {edge.target_name}
                    </div>
                    <div style={{ color: "#94a3b8" }}>
                      [{edge.layer}] {edge.label}
                    </div>
                  </div>
                ))}
              </div>
            </aside>
          )}
        </div>
      )}
    </section>
  );
};
