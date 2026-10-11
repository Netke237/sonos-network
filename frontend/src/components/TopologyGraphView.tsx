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
import { AniCleanlinessMeter } from "./AniCleanlinessMeter";

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

interface FloorZone {
  slug: string;
  name: string;
  yMin: number;
  yMax: number;
}

const FLOOR_ZONES: FloorZone[] = [
  { slug: "dachgeschoss", name: "Dachgeschoss (Attic)", yMin: 20, yMax: 180 },
  { slug: "obergeschoss", name: "Obergeschoss (Upper Floor)", yMin: 190, yMax: 380 },
  { slug: "erdgeschoss", name: "Erdgeschoss (Ground Floor)", yMin: 390, yMax: 660 },
  { slug: "keller", name: "Keller (Basement)", yMin: 670, yMax: 840 },
];

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
  const [showEdgeList, setShowEdgeList] = useState<boolean>(true);

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

  const nodesById = useMemo(() => {
    const map = new Map<string, TopologyNode>();
    if (graphData) {
      for (const n of graphData.nodes) {
        map.set(n.id, n);
      }
    }
    return map;
  }, [graphData]);

  // Edges filtered by current active layer, STP blocking flag, and floor visibility
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

  // Map of cross-floor links for each visible node (so we never draw lines into empty void!)
  const crossFloorLinksByNode = useMemo(() => {
    const map = new Map<string, { edge: DeviceConnectionEdge; isOutgoing: boolean }[]>();
    if (selectedFloorSlug === "ALL" || !graphData) return map;

    for (const edge of visibleEdges) {
      const sourceVisible = visibleNodeIdSet.has(edge.source);
      const targetVisible = visibleNodeIdSet.has(edge.target);

      // Only cross-floor when one end is visible and the other is NOT visible
      if (sourceVisible && !targetVisible) {
        const list = map.get(edge.source) ?? [];
        list.push({ edge, isOutgoing: true });
        map.set(edge.source, list);
      } else if (targetVisible && !sourceVisible) {
        const list = map.get(edge.target) ?? [];
        list.push({ edge, isOutgoing: false });
        map.set(edge.target, list);
      }
    }
    return map;
  }, [selectedFloorSlug, graphData, visibleEdges, visibleNodeIdSet]);

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

  // Filter floor zones to show only the selected floor if filtered
  const activeFloorZones = useMemo(() => {
    if (selectedFloorSlug === "ALL") return FLOOR_ZONES;
    return FLOOR_ZONES.filter((z) => z.slug.toLowerCase() === selectedFloorSlug.toLowerCase());
  }, [selectedFloorSlug]);

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

      {/* Legend & Guidance Strip */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
          marginBottom: "14px",
          fontSize: "0.75rem",
          color: "#94a3b8",
        }}
      >
        <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
          <span>
            <strong style={{ color: "#38bdf8" }}>━━</strong> WIRED_LAN (Trunk / VLAN 10)
          </span>
          <span>
            <strong style={{ color: "#a855f7" }}>━━</strong> WIFI_INFRA (EAP650 Ch 44 / Ch 40)
          </span>
          <span>
            <strong style={{ color: "#10b981" }}>━━</strong> SONOS_MESH Active Audio Tree (STP 03/04 &amp; 5GHz Ch 48)
          </span>
          <span>
            <strong style={{ color: "#64748b" }}>╌╌</strong> SONOS_MESH Blocked Backup Path (STP 00)
          </span>
        </div>
        <div style={{ color: "#cbd5e1" }}>
          <span>Click any device card to spotlight connected mesh paths</span>
        </div>
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
          {/* Main Interactive Canvas Container */}
          <div
            style={{
              position: "relative",
              minHeight: "860px",
              backgroundColor: "#0f172a",
              borderRadius: "10px",
              border: "1px solid #334155",
              overflow: "auto",
              padding: "16px",
            }}
          >
            {/* SVG Layer for Floor Zones, Grid Lines, and Directed Edges */}
            <svg
              width="1050"
              height="860"
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
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#10b981" />
                </marker>
                <marker
                  id="arrow-wired"
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
                  id="arrow-wifi"
                  viewBox="0 0 10 10"
                  refX="8"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#a855f7" />
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
                <marker
                  id="arrow-highlight"
                  viewBox="0 0 10 10"
                  refX="8"
                  refY="5"
                  markerWidth="7"
                  markerHeight="7"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#facc15" />
                </marker>
              </defs>

              {/* Physical Floor Zone Background Bands */}
              {activeFloorZones.map((zone) => (
                <g key={zone.slug}>
                  <rect
                    x="20"
                    y={zone.yMin}
                    width="1010"
                    height={zone.yMax - zone.yMin}
                    fill={zone.slug === "keller" || zone.slug === "obergeschoss" ? "#0b1329" : "#0d1b2a"}
                    stroke="#1e293b"
                    strokeWidth="1"
                    rx="8"
                  />
                  <text
                    x="35"
                    y={zone.yMin + 22}
                    fill="#64748b"
                    fontSize="11"
                    fontWeight="700"
                    fontFamily="sans-serif"
                    letterSpacing="1px"
                  >
                    {zone.name.toUpperCase()}
                  </text>
                </g>
              ))}

              {/* Draw Directed Edges — STRICT RULE: Only between two nodes visible on the canvas! */}
              {visibleEdges.map((edge) => {
                const src = nodesById.get(edge.source);
                const tgt = nodesById.get(edge.target);
                if (!src || !tgt) return null;

                // CRITICAL FIX: If either endpoint is not visible on the current floor filter,
                // NEVER draw lines into empty void! Cross-floor connections are rendered as Uplink Badges on the node card!
                if (!visibleNodeIdSet.has(edge.source) || !visibleNodeIdSet.has(edge.target)) {
                  return null;
                }

                // Dynamic coordinate centering
                const x1 = src.x + 95;
                const y1 = src.y + 45;
                const x2 = tgt.x + 95;
                const y2 = tgt.y + 45;

                const isHighlighted =
                  selectedNode &&
                  (edge.source === selectedNode.id || edge.target === selectedNode.id);

                let strokeColor = LAYER_COLORS[edge.layer] ?? "#38bdf8";
                let markerId = "url(#arrow-wired)";
                if (edge.layer === "SONOS_MESH") {
                  markerId = "url(#arrow-forward)";
                  strokeColor = "#10b981";
                } else if (edge.layer === "WIFI_INFRA") {
                  markerId = "url(#arrow-wifi)";
                  strokeColor = "#a855f7";
                }

                if (!edge.is_forwarding) {
                  strokeColor = "#64748b";
                  markerId = "url(#arrow-blocking)";
                }

                if (isHighlighted) {
                  strokeColor = "#facc15";
                  markerId = "url(#arrow-highlight)";
                }

                return (
                  <g key={edge.id}>
                    <line
                      x1={x1}
                      y1={y1}
                      x2={x2}
                      y2={y2}
                      stroke={strokeColor}
                      strokeWidth={isHighlighted ? 3.5 : edge.is_forwarding ? 2.2 : 1.5}
                      strokeDasharray={edge.is_forwarding ? "none" : "5 4"}
                      markerEnd={markerId}
                    />
                  </g>
                );
              })}
            </svg>

            {/* Interactive Device Nodes Layer */}
            <div style={{ position: "relative", width: "1030px", height: "860px" }}>
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

                const crossFloorEntries = crossFloorLinksByNode.get(node.id) ?? [];

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
                      boxShadow: isSelected
                        ? "0 0 16px rgba(56, 189, 248, 0.4)"
                        : "0 4px 10px rgba(0, 0, 0, 0.35)",
                      zIndex: isSelected ? 10 : 5,
                      transition: "transform 0.15s ease, box-shadow 0.15s ease",
                    }}
                  >
                    {/* Role & Health Grade Badges */}
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

                    {/* Node Name */}
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

                    {/* IP & Connection Mode */}
                    <div style={{ fontSize: "0.68rem", color: "#94a3b8" }}>
                      {node.ip_address ?? "Bonded"} ·{" "}
                      {node.connection_mode ?? node.model_name}
                    </div>

                    {/* AP Radio Channels */}
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

                    {/* Sonos Player Live RF & Cleanliness Telemetry */}
                    {node.device_role === "SONOS_PLAYER" && (
                      <div style={{ marginTop: "6px" }}>
                        <div style={{ marginBottom: "4px" }}>
                          <AniCleanlinessMeter
                            aniLevel={node.ofdm_ani_level}
                            compact={true}
                            showExplanation={false}
                          />
                        </div>
                        <div
                          style={{
                            fontSize: "0.66rem",
                            color: "#cbd5e1",
                            display: "flex",
                            justifyContent: "space-between",
                            flexWrap: "wrap",
                            gap: "4px",
                          }}
                        >
                          {node.phy_error_rate != null ? (
                            <span
                              style={{
                                color:
                                  node.phy_error_rate > 100
                                    ? "#f87171"
                                    : node.phy_error_rate > 20
                                    ? "#fbbf24"
                                    : "#86efac",
                                fontWeight: 700,
                              }}
                            >
                              {node.phy_error_rate.toFixed(1)} err/s
                            </span>
                          ) : (
                            <span>0.0 err/s</span>
                          )}
                          {node.stp_path_cost != null && (
                            <span style={{ color: "#94a3b8" }}>Cost {node.stp_path_cost}</span>
                          )}
                          {node.rssi_dbm != null && (
                            <span style={{ color: "#38bdf8" }}>{node.rssi_dbm} dBm</span>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Cross-Floor Uplink / Downlink Anchor Badges (Eliminates boxes hanging in thin air!) */}
                    {crossFloorEntries.map(({ edge, isOutgoing }) => {
                      const otherNode = nodesById.get(isOutgoing ? edge.target : edge.source);
                      return (
                        <div
                          key={`cross-anchor-${edge.id}`}
                          style={{
                            marginTop: "6px",
                            padding: "3px 6px",
                            backgroundColor: "#1e1b4b",
                            border: "1px solid #6366f1",
                            borderRadius: "4px",
                            fontSize: "0.64rem",
                            color: "#c7d2fe",
                          }}
                          title={`Connected across floors to ${otherNode?.name ?? "other node"}`}
                        >
                          <div style={{ fontWeight: 700, color: "#a5b4fc" }}>
                            {isOutgoing ? "▲ Uplink:" : "▼ Downlink:"} {otherNode?.name ?? "Node"} ({otherNode?.floor_name ?? "Floor"})
                          </div>
                          <div style={{ color: "#e0e7ff", fontSize: "0.62rem" }}>
                            {edge.label}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </div>

            {/* Collapsible Active Network Links & Path Telemetry Strip */}
            <div
              style={{
                marginTop: "16px",
                backgroundColor: "#0b1329",
                borderRadius: "8px",
                border: "1px solid #1e293b",
                padding: "12px 16px",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  cursor: "pointer",
                  marginBottom: showEdgeList ? "10px" : "0",
                }}
                onClick={() => setShowEdgeList(!showEdgeList)}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "0.82rem", fontWeight: 700, color: "#e2e8f0" }}>
                    Active Network Links &amp; Path Telemetry ({visibleEdges.length})
                  </span>
                  <span style={{ fontSize: "0.72rem", color: "#94a3b8" }}>
                    (Forwarding audio tree &amp; physical trunks)
                  </span>
                </div>
                <span style={{ fontSize: "0.74rem", color: "#38bdf8", fontWeight: 600 }}>
                  {showEdgeList ? "▲ Hide Details" : "▼ Show Details"}
                </span>
              </div>

              {showEdgeList && (
                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "6px",
                    maxHeight: "180px",
                    overflowY: "auto",
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
              )}
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
                    <strong>OFDM ANI Level:</strong>
                    <div style={{ marginTop: "4px" }}>
                      <AniCleanlinessMeter aniLevel={selectedNode.ofdm_ani_level} />
                    </div>
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
