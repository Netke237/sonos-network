import React, { useEffect, useMemo, useRef, useState } from "react";
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
  { slug: "dachgeschoss", name: "Dachgeschoss (Attic)", yMin: 20, yMax: 170 },
  { slug: "obergeschoss", name: "Obergeschoss (Upper Floor)", yMin: 185, yMax: 375 },
  { slug: "erdgeschoss", name: "Erdgeschoss (Ground Floor)", yMin: 390, yMax: 690 },
  { slug: "keller", name: "Keller (Basement)", yMin: 705, yMax: 895 },
];

interface TopologyGraphViewProps {
  floors: FloorMatrixItem[];
  onInspectRoomSlug?: (roomSlug: string) => void;
}

type PathCategoryFilter =
  | "ALL"
  | "FORWARDING_TREE"
  | "WIRED_LAN"
  | "WIFI_INFRA"
  | "BLOCKING_STP";

export const TopologyGraphView: React.FC<TopologyGraphViewProps> = ({
  floors,
  onInspectRoomSlug,
}) => {
  const [graphData, setGraphData] = useState<TopologyGraphResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Top Controls State
  const [layerFilter, setLayerFilter] = useState<TopologyLayerFilter>("ALL");
  const [showBlockedStp, setShowBlockedStp] = useState<boolean>(true);
  const [selectedFloorSlug, setSelectedFloorSlug] = useState<string>("ALL");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [rightPanelTab, setRightPanelTab] = useState<"LEGEND" | "INSPECTOR">("LEGEND");

  // Lower Explorer Filters State
  const [pathCategory, setPathCategory] = useState<PathCategoryFilter>("ALL");
  const [filterNetworkElement, setFilterNetworkElement] = useState<string>("ALL");
  const [filterDevice, setFilterDevice] = useState<string>("ALL");
  const [pathSearchQuery, setPathSearchQuery] = useState<string>("");
  const [pathViewMode, setPathViewMode] = useState<"GROUPED" | "TABLE">("TABLE");

  // Dynamic Canvas Width Tracking
  const canvasRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState<number>(1400);

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

  // Update canvas width on resize
  useEffect(() => {
    const updateWidth = () => {
      if (canvasRef.current) {
        const w = canvasRef.current.clientWidth;
        if (w > 0) {
          setContainerWidth(w);
        }
      }
    };
    updateWidth();
    window.addEventListener("resize", updateWidth);
    return () => window.removeEventListener("resize", updateWidth);
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

  // Dynamic Full-Width Layout: Distributes device cards across the full screen width with ZERO overlap
  const dynamicNodePositions = useMemo(() => {
    const positions = new Map<string, { x: number; y: number }>();
    if (!graphData) return positions;

    const width = Math.max(containerWidth, 1150);
    const cardWidth = 205;
    const leftMargin = 50;
    const rightMargin = 50;
    const usableWidth = width - leftMargin - rightMargin;

    // Group visible nodes by floor level
    const byFloor: Record<string, TopologyNode[]> = {
      dachgeschoss: [],
      obergeschoss: [],
      erdgeschoss: [],
      keller: [],
    };

    for (const node of visibleNodes) {
      const fl = (node.floor_slug ?? "erdgeschoss").toLowerCase();
      if (byFloor[fl]) {
        byFloor[fl].push(node);
      } else {
        byFloor.erdgeschoss.push(node);
      }
    }

    // 1. Dachgeschoss (Attic) — Center the nodes
    const dgNodes = byFloor.dachgeschoss;
    if (dgNodes.length === 1) {
      positions.set(dgNodes[0].id, {
        x: leftMargin + (usableWidth - cardWidth) / 2,
        y: 45,
      });
    } else if (dgNodes.length > 1) {
      const step = (usableWidth - cardWidth) / (dgNodes.length - 1);
      dgNodes.forEach((node, idx) => {
        positions.set(node.id, { x: leftMargin + idx * step, y: 45 });
      });
    }

    // 2. Obergeschoss (Upper Floor) — Even horizontal distribution
    const ogNodes = byFloor.obergeschoss;
    if (ogNodes.length > 0) {
      const step =
        ogNodes.length > 1 ? (usableWidth - cardWidth) / (ogNodes.length - 1) : 0;
      ogNodes.forEach((node, idx) => {
        positions.set(node.id, {
          x: leftMargin + (ogNodes.length === 1 ? (usableWidth - cardWidth) / 2 : idx * step),
          y: 215,
        });
      });
    }

    // 3. Erdgeschoss (Ground Floor) — 2 distinct rows: Core/Wired Row (top) + Leaf/Surround Row (bottom)
    const egNodes = byFloor.erdgeschoss;
    if (egNodes.length > 0) {
      // Prioritize row 1 for Infrastructure & Primary Root units
      const isRow1 = (n: TopologyNode) =>
        n.device_role === "WIFI_AP" ||
        n.slug.includes("bookshelf") ||
        n.slug.includes("beam") ||
        n.slug.includes("bueroccke") ||
        n.connection_mode === "ETHERNET_ROOT";

      const row1 = egNodes.filter(isRow1);
      const row2 = egNodes.filter((n) => !isRow1(n));

      // Row 1 distribution (y = 415)
      const stepRow1 =
        row1.length > 1 ? (usableWidth - cardWidth) / (row1.length - 1) : 0;
      row1.forEach((node, idx) => {
        positions.set(node.id, {
          x: leftMargin + (row1.length === 1 ? (usableWidth - cardWidth) / 2 : idx * stepRow1),
          y: 415,
        });
      });

      // Row 2 distribution (y = 550)
      const stepRow2 =
        row2.length > 1 ? (usableWidth - cardWidth) / (row2.length - 1) : 0;
      row2.forEach((node, idx) => {
        positions.set(node.id, {
          x: leftMargin + (row2.length === 1 ? (usableWidth - cardWidth) / 2 : idx * stepRow2),
          y: 550,
        });
      });
    }

    // 4. Keller (Basement) — Flow: Fritzbox ➔ Firewalla ➔ GS316EP ➔ Keller Play:3
    const kellerNodes = byFloor.keller;
    if (kellerNodes.length > 0) {
      const step =
        kellerNodes.length > 1
          ? (usableWidth - cardWidth) / (kellerNodes.length - 1)
          : 0;
      kellerNodes.forEach((node, idx) => {
        positions.set(node.id, {
          x: leftMargin + (kellerNodes.length === 1 ? (usableWidth - cardWidth) / 2 : idx * step),
          y: 735,
        });
      });
    }

    return positions;
  }, [graphData, visibleNodes, containerWidth]);

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

  // Filtered edges for the lower path explorer
  const explorerEdges: DeviceConnectionEdge[] = useMemo(() => {
    return visibleEdges.filter((edge) => {
      // 1. Path Category Filter
      if (pathCategory === "FORWARDING_TREE") {
        if (!edge.is_forwarding && edge.stp_state === "BLOCKING") return false;
      } else if (pathCategory === "WIRED_LAN") {
        if (edge.layer !== "WIRED_LAN") return false;
      } else if (pathCategory === "WIFI_INFRA") {
        if (edge.layer !== "WIFI_INFRA") return false;
      } else if (pathCategory === "BLOCKING_STP") {
        if (edge.is_forwarding || edge.stp_state !== "BLOCKING") return false;
      }

      // 2. Network Element Filter (AP, Switch, Router)
      if (filterNetworkElement !== "ALL") {
        const matchesSource = edge.source === filterNetworkElement || edge.source_slug === filterNetworkElement;
        const matchesTarget = edge.target === filterNetworkElement || edge.target_slug === filterNetworkElement;
        if (!matchesSource && !matchesTarget) return false;
      }

      // 3. Device / Speaker Filter
      if (filterDevice !== "ALL") {
        const matchesSource =
          edge.source === filterDevice ||
          edge.source_slug === filterDevice ||
          edge.source_name.toLowerCase().includes(filterDevice.toLowerCase());
        const matchesTarget =
          edge.target === filterDevice ||
          edge.target_slug === filterDevice ||
          edge.target_name.toLowerCase().includes(filterDevice.toLowerCase());
        if (!matchesSource && !matchesTarget) return false;
      }

      // 4. Free-text search query
      if (pathSearchQuery.trim()) {
        const q = pathSearchQuery.toLowerCase();
        const textToMatch = `${edge.source_name} ${edge.target_name} ${edge.label} ${edge.layer} ${edge.stp_state ?? ""}`.toLowerCase();
        if (!textToMatch.includes(q)) return false;
      }

      return true;
    });
  }, [visibleEdges, pathCategory, filterNetworkElement, filterDevice, pathSearchQuery]);

  // Cross-floor links map for visible nodes (prevents lines pointing into empty void!)
  const crossFloorLinksByNode = useMemo(() => {
    const map = new Map<string, { edge: DeviceConnectionEdge; isOutgoing: boolean }[]>();
    if (selectedFloorSlug === "ALL" || !graphData) return map;

    for (const edge of visibleEdges) {
      const sourceVisible = visibleNodeIdSet.has(edge.source);
      const targetVisible = visibleNodeIdSet.has(edge.target);

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

  const activeFloorZones = useMemo(() => {
    if (selectedFloorSlug === "ALL") return FLOOR_ZONES;
    return FLOOR_ZONES.filter((z) => z.slug.toLowerCase() === selectedFloorSlug.toLowerCase());
  }, [selectedFloorSlug]);

  // Unique lists for filter dropdowns
  const networkElementsList = useMemo(() => {
    if (!graphData) return [];
    return graphData.nodes.filter(
      (n) => n.device_role === "WIFI_AP" || n.device_role === "SWITCH" || n.device_role === "ROUTER"
    );
  }, [graphData]);

  const devicesList = useMemo(() => {
    if (!graphData) return [];
    return graphData.nodes
      .filter((n) => n.device_role === "SONOS_PLAYER")
      .sort((a, b) => a.name.localeCompare(b.name));
  }, [graphData]);

  // Statistics for path summary
  const pathStats = useMemo(() => {
    const total = visibleEdges.length;
    const forwarding = visibleEdges.filter((e) => e.is_forwarding && e.layer === "SONOS_MESH").length;
    const wired = visibleEdges.filter((e) => e.layer === "WIRED_LAN").length;
    const wifi = visibleEdges.filter((e) => e.layer === "WIFI_INFRA").length;
    const blocked = visibleEdges.filter((e) => !e.is_forwarding || e.stp_state === "BLOCKING").length;
    return { total, forwarding, wired, wifi, blocked };
  }, [visibleEdges]);

  // Auto-switch to Inspector tab when a node is clicked
  const handleSelectNode = (nodeId: string) => {
    setSelectedNodeId(nodeId);
    setRightPanelTab("INSPECTOR");
  };

  const svgCanvasWidth = Math.max(containerWidth, 1150);
  const svgCanvasHeight = 920;

  return (
    <section
      aria-label="Interactive Network Topology Graph"
      style={{
        backgroundColor: "#1e293b",
        borderRadius: "12px",
        padding: "20px",
        border: "1px solid #334155",
        width: "100%",
        boxSizing: "border-box",
      }}
    >
      {/* Top Controls Toolbar */}
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
              padding: "6px 14px",
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
              padding: "6px 14px",
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
              padding: "6px 14px",
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
                padding: "5px 10px",
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

      {loading && <p>Loading network topology graph...</p>}
      {error && <p style={{ color: "#f87171" }}>Error: {error}</p>}

      {!loading && graphData && (
        <>
          {/* Main Layout: Full-Width Canvas + Right Legend/Inspector Pane */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 340px",
              gap: "16px",
              alignItems: "start",
              width: "100%",
            }}
          >
            {/* Full-Width Interactive Canvas Container */}
            <div
              ref={canvasRef}
              style={{
                position: "relative",
                minHeight: `${svgCanvasHeight}px`,
                backgroundColor: "#0f172a",
                borderRadius: "10px",
                border: "1px solid #334155",
                overflow: "hidden",
                width: "100%",
              }}
            >
              {/* SVG Directed Edge & Floor Zones Layer */}
              <svg
                width={svgCanvasWidth}
                height={svgCanvasHeight}
                style={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  width: "100%",
                  height: "100%",
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

                {/* Physical Floor Zone Background Bands expanding across 100% width */}
                {activeFloorZones.map((zone) => (
                  <g key={zone.slug}>
                    <rect
                      x="20"
                      y={zone.yMin}
                      width={Math.max(svgCanvasWidth - 40, 1000)}
                      height={zone.yMax - zone.yMin}
                      fill={
                        zone.slug === "keller" || zone.slug === "obergeschoss"
                          ? "#0b1329"
                          : "#0d1b2a"
                      }
                      stroke="#1e293b"
                      strokeWidth="1.2"
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

                {/* Draw Directed Edges between dynamically distributed nodes */}
                {visibleEdges.map((edge) => {
                  const src = nodesById.get(edge.source);
                  const tgt = nodesById.get(edge.target);
                  if (!src || !tgt) return null;

                  // Cross-floor connections are rendered as explicit badges on node cards, never pointing to empty space
                  if (!visibleNodeIdSet.has(edge.source) || !visibleNodeIdSet.has(edge.target)) {
                    return null;
                  }

                  const srcPos = dynamicNodePositions.get(src.id) ?? { x: src.x, y: src.y };
                  const tgtPos = dynamicNodePositions.get(tgt.id) ?? { x: tgt.x, y: tgt.y };

                  // Dynamic card center snapping
                  const x1 = srcPos.x + 102;
                  const y1 = srcPos.y + 44;
                  const x2 = tgtPos.x + 102;
                  const y2 = tgtPos.y + 44;

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

              {/* Interactive Device Nodes Layer — Full Width, Non-Overlapping */}
              <div style={{ position: "relative", width: "100%", height: `${svgCanvasHeight}px` }}>
                {visibleNodes.map((node) => {
                  const pos = dynamicNodePositions.get(node.id) ?? { x: node.x, y: node.y };
                  const gradeStyle = GRADE_STYLES[node.health_grade] ?? GRADE_STYLES.GOOD;
                  const roleStyle = ROLE_STYLES[node.device_role] ?? ROLE_STYLES.SONOS_PLAYER;
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
                      onClick={() => handleSelectNode(node.id)}
                      style={{
                        position: "absolute",
                        left: `${pos.x}px`,
                        top: `${pos.y}px`,
                        width: "205px",
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
                        transition: "left 0.2s ease, top 0.2s ease, box-shadow 0.15s ease",
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

                      {/* Cross-Floor Uplink / Downlink Anchor Badges */}
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
                              {!isOutgoing ? "▲ Uplink:" : "▼ Downlink:"} {otherNode?.name ?? "Node"} ({otherNode?.floor_name ?? "Floor"})
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
            </div>

            {/* Right Side Pane: Interactive Legend & Node Inspector */}
            <aside
              style={{
                backgroundColor: "#0f172a",
                borderRadius: "10px",
                border: "1px solid #334155",
                padding: "16px",
                display: "flex",
                flexDirection: "column",
                gap: "14px",
              }}
            >
              {/* Tab Selector: Legend vs Inspector */}
              <div
                style={{
                  display: "flex",
                  borderRadius: "6px",
                  backgroundColor: "#1e293b",
                  padding: "2px",
                  border: "1px solid #334155",
                }}
              >
                <button
                  type="button"
                  onClick={() => setRightPanelTab("LEGEND")}
                  style={{
                    flex: 1,
                    backgroundColor: rightPanelTab === "LEGEND" ? "#0284c7" : "transparent",
                    color: rightPanelTab === "LEGEND" ? "#ffffff" : "#94a3b8",
                    border: "none",
                    borderRadius: "4px",
                    padding: "6px 10px",
                    fontSize: "0.78rem",
                    fontWeight: 700,
                    cursor: "pointer",
                  }}
                >
                  Network Legend
                </button>
                <button
                  type="button"
                  onClick={() => setRightPanelTab("INSPECTOR")}
                  style={{
                    flex: 1,
                    backgroundColor: rightPanelTab === "INSPECTOR" ? "#0284c7" : "transparent",
                    color: rightPanelTab === "INSPECTOR" ? "#ffffff" : "#94a3b8",
                    border: "none",
                    borderRadius: "4px",
                    padding: "6px 10px",
                    fontSize: "0.78rem",
                    fontWeight: 700,
                    cursor: "pointer",
                  }}
                >
                  {selectedNode ? "Node Inspector" : "Inspector"}
                </button>
              </div>

              {/* View 1: Comprehensive Network Legend */}
              {rightPanelTab === "LEGEND" && (
                <div style={{ fontSize: "0.78rem", color: "#cbd5e1" }}>
                  <h4 style={{ margin: "0 0 10px", color: "#38bdf8", fontSize: "0.9rem" }}>
                    Network Path &amp; Signal Key
                  </h4>

                  {/* Links Key */}
                  <div style={{ marginBottom: "12px" }}>
                    <div style={{ fontWeight: 700, color: "#f8fafc", marginBottom: "6px" }}>
                      Link Layers:
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span style={{ color: "#38bdf8", fontWeight: 900, fontSize: "1.1rem" }}>━</span>
                        <span>
                          <strong style={{ color: "#38bdf8" }}>WIRED_LAN</strong> · Trunk / Cat6
                        </span>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span style={{ color: "#a855f7", fontWeight: 900, fontSize: "1.1rem" }}>━</span>
                        <span>
                          <strong style={{ color: "#a855f7" }}>WIFI_INFRA</strong> · 5GHz Ch 44 / 40
                        </span>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span style={{ color: "#10b981", fontWeight: 900, fontSize: "1.1rem" }}>━</span>
                        <span>
                          <strong style={{ color: "#10b981" }}>SONOS_MESH Active</strong> (STP 03/04)
                        </span>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span style={{ color: "#64748b", fontWeight: 900, fontSize: "1.1rem" }}>╌</span>
                        <span>
                          <strong style={{ color: "#94a3b8" }}>SONOS_MESH Blocked</strong> (STP 00 Backup)
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Device Roles */}
                  <div style={{ marginBottom: "12px", borderTop: "1px solid #1e293b", paddingTop: "10px" }}>
                    <div style={{ fontWeight: 700, color: "#f8fafc", marginBottom: "6px" }}>
                      Device Roles:
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
                      {Object.entries(ROLE_STYLES).map(([role, st]) => (
                        <span
                          key={role}
                          style={{
                            fontSize: "0.64rem",
                            fontWeight: 700,
                            padding: "2px 6px",
                            borderRadius: "4px",
                            backgroundColor: st.badgeBg,
                            color: st.badgeText,
                          }}
                        >
                          {st.label}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Cleanliness / ANI Scale */}
                  <div style={{ borderTop: "1px solid #1e293b", paddingTop: "10px" }}>
                    <div style={{ fontWeight: 700, color: "#f8fafc", marginBottom: "6px" }}>
                      Atheros OFDM ANI Cleanliness:
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "4px", fontSize: "0.74rem" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#10b981" }} />
                        <span><strong>0 – 3:</strong> Clean Air (Full Sensitivity)</span>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#f59e0b" }} />
                        <span><strong>4 – 6:</strong> Elevated Background Hash</span>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#ef4444" }} />
                        <span><strong>7 – 9:</strong> Severe EMI (USB-C Docks / Noise)</span>
                      </div>
                    </div>
                  </div>

                  {/* Quick Tip */}
                  <div
                    style={{
                      marginTop: "14px",
                      backgroundColor: "#1e293b",
                      padding: "8px 10px",
                      borderRadius: "6px",
                      fontSize: "0.72rem",
                      color: "#94a3b8",
                      borderLeft: "3px solid #38bdf8",
                    }}
                  >
                    💡 Click any node on the canvas to inspect connected edges or spotlight its audio forwarding paths.
                  </div>
                </div>
              )}

              {/* View 2: Node Detail Inspector Panel */}
              {rightPanelTab === "INSPECTOR" && (
                <div>
                  {selectedNode ? (
                    <div role="region" aria-label="Topology Node Detail Panel">
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
                          <strong>Role / Model:</strong> {selectedNode.device_role} · {selectedNode.model_name}
                        </div>
                        <div>
                          <strong>Room / Floor:</strong> {selectedNode.room_name ?? "N/A"} ({selectedNode.floor_name ?? "N/A"})
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
                            <strong>PHY Error Velocity:</strong> {selectedNode.phy_error_rate.toFixed(1)} err/s
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

                      <h4 style={{ margin: "0 0 8px", fontSize: "0.85rem", color: "#e2e8f0" }}>
                        Connected Edges ({connectedEdgesForSelected.length})
                      </h4>
                      <div style={{ display: "flex", flexDirection: "column", gap: "6px", maxHeight: "260px", overflowY: "auto" }}>
                        {connectedEdgesForSelected.map((edge) => (
                          <div
                            key={edge.id}
                            style={{
                              backgroundColor: "#1e293b",
                              border: edge.is_forwarding ? "1px solid #334155" : "1px dashed #64748b",
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
                    </div>
                  ) : (
                    <div style={{ textAlign: "center", padding: "20px 0", color: "#94a3b8", fontSize: "0.8rem" }}>
                      No device selected. Click any device card on the canvas to inspect its details and connected paths.
                    </div>
                  )}
                </div>
              )}
            </aside>
          </div>

          {/* Lower Part: Classified & Filterable Path Telemetry Explorer */}
          <section
            aria-label="Network Path and Telemetry Explorer"
            style={{
              marginTop: "20px",
              backgroundColor: "#0b1329",
              borderRadius: "10px",
              border: "1px solid #1e293b",
              padding: "16px 20px",
            }}
          >
            {/* Explorer Header & Statistics Strip */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "12px",
                marginBottom: "16px",
                paddingBottom: "12px",
                borderBottom: "1px solid #1e293b",
              }}
            >
              <div>
                <h3 style={{ margin: 0, fontSize: "1.05rem", color: "#38bdf8" }}>
                  Network Path &amp; Telemetry Explorer
                </h3>
                <p style={{ margin: "3px 0 0", fontSize: "0.76rem", color: "#94a3b8" }}>
                  Showing {explorerEdges.length} of {visibleEdges.length} filtered paths across the house
                </p>
              </div>

              {/* Category Quick Badges */}
              <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                <button
                  type="button"
                  onClick={() => setPathCategory("ALL")}
                  style={{
                    backgroundColor: pathCategory === "ALL" ? "#0284c7" : "#1e293b",
                    color: pathCategory === "ALL" ? "#ffffff" : "#cbd5e1",
                    border: "1px solid #334155",
                    borderRadius: "999px",
                    padding: "3px 10px",
                    fontSize: "0.72rem",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  All ({pathStats.total})
                </button>
                <button
                  type="button"
                  onClick={() => setPathCategory("FORWARDING_TREE")}
                  style={{
                    backgroundColor: pathCategory === "FORWARDING_TREE" ? "#065f46" : "#1e293b",
                    color: pathCategory === "FORWARDING_TREE" ? "#6ee7b7" : "#cbd5e1",
                    border: "1px solid #10b981",
                    borderRadius: "999px",
                    padding: "3px 10px",
                    fontSize: "0.72rem",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  ⚡ Active Forwarding ({pathStats.forwarding})
                </button>
                <button
                  type="button"
                  onClick={() => setPathCategory("WIRED_LAN")}
                  style={{
                    backgroundColor: pathCategory === "WIRED_LAN" ? "#075985" : "#1e293b",
                    color: pathCategory === "WIRED_LAN" ? "#7dd3fc" : "#cbd5e1",
                    border: "1px solid #38bdf8",
                    borderRadius: "999px",
                    padding: "3px 10px",
                    fontSize: "0.72rem",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  🔌 Wired Trunks ({pathStats.wired})
                </button>
                <button
                  type="button"
                  onClick={() => setPathCategory("WIFI_INFRA")}
                  style={{
                    backgroundColor: pathCategory === "WIFI_INFRA" ? "#6b21a8" : "#1e293b",
                    color: pathCategory === "WIFI_INFRA" ? "#d8b4fe" : "#cbd5e1",
                    border: "1px solid #a855f7",
                    borderRadius: "999px",
                    padding: "3px 10px",
                    fontSize: "0.72rem",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  📶 Wi-Fi APs ({pathStats.wifi})
                </button>
                <button
                  type="button"
                  onClick={() => setPathCategory("BLOCKING_STP")}
                  style={{
                    backgroundColor: pathCategory === "BLOCKING_STP" ? "#334155" : "#1e293b",
                    color: pathCategory === "BLOCKING_STP" ? "#cbd5e1" : "#94a3b8",
                    border: "1px solid #64748b",
                    borderRadius: "999px",
                    padding: "3px 10px",
                    fontSize: "0.72rem",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  🚫 Blocked STP ({pathStats.blocked})
                </button>
              </div>
            </div>

            {/* Interactive Filters Bar */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                gap: "12px",
                marginBottom: "16px",
                alignItems: "end",
              }}
            >
              {/* Filter 1: By Network Element (AP / Switch / Router) */}
              <div>
                <label style={{ display: "block", fontSize: "0.75rem", color: "#94a3b8", marginBottom: "4px" }}>
                  Filter by Infrastructure Element:
                </label>
                <select
                  value={filterNetworkElement}
                  onChange={(e) => setFilterNetworkElement(e.target.value)}
                  style={{
                    width: "100%",
                    backgroundColor: "#1e293b",
                    color: "#f8fafc",
                    border: "1px solid #475569",
                    borderRadius: "6px",
                    padding: "6px 8px",
                    fontSize: "0.78rem",
                  }}
                >
                  <option value="ALL">All Network Elements</option>
                  {networkElementsList.map((ne) => (
                    <option key={ne.id} value={ne.id}>
                      {ne.name} ({ne.device_role})
                    </option>
                  ))}
                </select>
              </div>

              {/* Filter 2: By Device / Room (Noemi, Nicolas, Wohnzimmer Bookshelf, etc.) */}
              <div>
                <label style={{ display: "block", fontSize: "0.75rem", color: "#94a3b8", marginBottom: "4px" }}>
                  Filter by Device / Speaker:
                </label>
                <select
                  value={filterDevice}
                  onChange={(e) => setFilterDevice(e.target.value)}
                  style={{
                    width: "100%",
                    backgroundColor: "#1e293b",
                    color: "#f8fafc",
                    border: "1px solid #475569",
                    borderRadius: "6px",
                    padding: "6px 8px",
                    fontSize: "0.78rem",
                  }}
                >
                  <option value="ALL">All Devices &amp; Speakers</option>
                  {devicesList.map((dev) => (
                    <option key={dev.id} value={dev.id}>
                      {dev.name} ({dev.room_name ?? "Room"})
                    </option>
                  ))}
                </select>
              </div>

              {/* Filter 3: Free-Text Search Query */}
              <div>
                <label style={{ display: "block", fontSize: "0.75rem", color: "#94a3b8", marginBottom: "4px" }}>
                  Search Paths / Labels:
                </label>
                <input
                  type="text"
                  placeholder="e.g. Noemi, Kitchen, Ch 44, HT Bond..."
                  value={pathSearchQuery}
                  onChange={(e) => setPathSearchQuery(e.target.value)}
                  style={{
                    width: "100%",
                    backgroundColor: "#1e293b",
                    color: "#f8fafc",
                    border: "1px solid #475569",
                    borderRadius: "6px",
                    padding: "6px 8px",
                    fontSize: "0.78rem",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              {/* View Mode Toggle & Reset */}
              <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                <button
                  type="button"
                  onClick={() => setPathViewMode(pathViewMode === "TABLE" ? "GROUPED" : "TABLE")}
                  style={{
                    flex: 1,
                    backgroundColor: "#1e293b",
                    color: "#38bdf8",
                    border: "1px solid #38bdf8",
                    borderRadius: "6px",
                    padding: "6px 10px",
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  {pathViewMode === "TABLE" ? "⊞ Card View" : "☰ Table View"}
                </button>
                {(filterNetworkElement !== "ALL" ||
                  filterDevice !== "ALL" ||
                  pathSearchQuery.trim() !== "" ||
                  pathCategory !== "ALL") && (
                  <button
                    type="button"
                    onClick={() => {
                      setPathCategory("ALL");
                      setFilterNetworkElement("ALL");
                      setFilterDevice("ALL");
                      setPathSearchQuery("");
                    }}
                    style={{
                      backgroundColor: "#7f1d1d",
                      color: "#fca5a5",
                      border: "none",
                      borderRadius: "6px",
                      padding: "6px 10px",
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    Reset
                  </button>
                )}
              </div>
            </div>

            {/* Quick Filter Shortcut Chips */}
            <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginBottom: "14px" }}>
              <span style={{ fontSize: "0.72rem", color: "#64748b", alignSelf: "center" }}>
                Quick Filters:
              </span>
              {[
                { label: "AP: Kitchen EAP650", action: () => setFilterNetworkElement("ap-kitchen-eap650") },
                { label: "AP: Galerie EAP650", action: () => setFilterNetworkElement("ap-galerie-eap650") },
                { label: "Noemi Paths", action: () => setFilterDevice("sonos-noemi") },
                { label: "Nicolas (Station Mode)", action: () => setFilterDevice("sonos-nicolas") },
                { label: "Wohnzimmer Root", action: () => setFilterDevice("sonos-wohnzimmer-bookshelf") },
              ].map((chip) => (
                <button
                  key={chip.label}
                  type="button"
                  onClick={chip.action}
                  style={{
                    backgroundColor: "#1e293b",
                    color: "#cbd5e1",
                    border: "1px solid #334155",
                    borderRadius: "4px",
                    padding: "2px 8px",
                    fontSize: "0.68rem",
                    cursor: "pointer",
                  }}
                >
                  {chip.label}
                </button>
              ))}
            </div>

            {/* Path Representation 1: Structured Telemetry Table */}
            {pathViewMode === "TABLE" ? (
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
                        borderBottom: "1px solid #334155",
                        color: "#94a3b8",
                        textAlign: "left",
                      }}
                    >
                      <th style={{ padding: "8px" }}>Source ➔ Target</th>
                      <th style={{ padding: "8px" }}>Layer</th>
                      <th style={{ padding: "8px" }}>STP State</th>
                      <th style={{ padding: "8px" }}>Telemetry Details</th>
                      <th style={{ padding: "8px" }}>Health</th>
                      <th style={{ padding: "8px", textAlign: "right" }}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {explorerEdges.map((edge) => {
                      const gradeStyle = GRADE_STYLES[edge.health_grade] ?? GRADE_STYLES.GOOD;
                      const isHighlighted =
                        selectedNode &&
                        (edge.source === selectedNode.id || edge.target === selectedNode.id);

                      let layerBadgeBg = "#075985";
                      let layerBadgeText = "#7dd3fc";
                      if (edge.layer === "SONOS_MESH") {
                        layerBadgeBg = "#064e3b";
                        layerBadgeText = "#6ee7b7";
                      } else if (edge.layer === "WIFI_INFRA") {
                        layerBadgeBg = "#581c87";
                        layerBadgeText = "#d8b4fe";
                      }

                      return (
                        <tr
                          key={edge.id}
                          data-testid={`topology-edge-${edge.id}`}
                          style={{
                            borderBottom: "1px solid #1e293b",
                            backgroundColor: isHighlighted ? "#422006" : "transparent",
                          }}
                        >
                          <td style={{ padding: "8px 10px", fontWeight: 600, color: "#f8fafc" }}>
                            <span>{edge.source_name} ➔ {edge.target_name}</span>
                          </td>
                          <td style={{ padding: "8px 10px" }}>
                            <span
                              style={{
                                backgroundColor: layerBadgeBg,
                                color: layerBadgeText,
                                padding: "2px 6px",
                                borderRadius: "4px",
                                fontSize: "0.68rem",
                                fontWeight: 700,
                              }}
                            >
                              {edge.layer}
                            </span>
                          </td>
                          <td style={{ padding: "8px 10px" }}>
                            <span
                              style={{
                                color: edge.is_forwarding ? "#86efac" : "#94a3b8",
                                fontWeight: edge.is_forwarding ? 700 : 400,
                              }}
                            >
                              {edge.stp_state ?? (edge.is_forwarding ? "FORWARDING" : "BLOCKING")}
                            </span>
                          </td>
                          <td style={{ padding: "8px 10px", color: "#cbd5e1" }}>
                            {edge.label}
                          </td>
                          <td style={{ padding: "8px 10px" }}>
                            <span
                              style={{
                                backgroundColor: gradeStyle.bg,
                                color: gradeStyle.text,
                                padding: "1px 6px",
                                borderRadius: "999px",
                                fontSize: "0.68rem",
                                fontWeight: 700,
                              }}
                            >
                              {edge.health_grade}
                            </span>
                          </td>
                          <td style={{ padding: "8px 10px", textAlign: "right" }}>
                            <button
                              type="button"
                              onClick={() => handleSelectNode(edge.source)}
                              style={{
                                backgroundColor: "#1e293b",
                                color: "#38bdf8",
                                border: "1px solid #334155",
                                borderRadius: "4px",
                                padding: "3px 8px",
                                fontSize: "0.7rem",
                                cursor: "pointer",
                              }}
                            >
                              Spotlight
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              /* Path Representation 2: Grouped Cards View */
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
                  gap: "10px",
                  maxHeight: "360px",
                  overflowY: "auto",
                }}
              >
                {explorerEdges.map((edge) => {
                  const gradeStyle = GRADE_STYLES[edge.health_grade] ?? GRADE_STYLES.GOOD;
                  const isHighlighted =
                    selectedNode &&
                    (edge.source === selectedNode.id || edge.target === selectedNode.id);

                  return (
                    <div
                      key={edge.id}
                      data-testid={`topology-edge-${edge.id}`}
                      style={{
                        backgroundColor: isHighlighted ? "#422006" : "#1e293b",
                        border: edge.is_forwarding ? `1px solid ${gradeStyle.border}` : "1px dashed #64748b",
                        borderRadius: "8px",
                        padding: "10px 12px",
                        fontSize: "0.76rem",
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
                        <span style={{ fontWeight: 700, color: "#f8fafc" }}>
                          {edge.source_name} ➔ {edge.target_name}
                        </span>
                        <span
                          style={{
                            backgroundColor: gradeStyle.bg,
                            color: gradeStyle.text,
                            padding: "1px 6px",
                            borderRadius: "999px",
                            fontSize: "0.64rem",
                            fontWeight: 700,
                          }}
                        >
                          {edge.health_grade}
                        </span>
                      </div>
                      <div style={{ color: "#94a3b8", marginBottom: "4px" }}>
                        [{edge.layer}] {edge.label}
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ color: edge.is_forwarding ? "#86efac" : "#64748b", fontSize: "0.7rem" }}>
                          {edge.is_forwarding ? "● Active Forwarding" : "○ Blocked Backup"}
                        </span>
                        <button
                          type="button"
                          onClick={() => handleSelectNode(edge.source)}
                          style={{
                            background: "transparent",
                            border: "1px solid #38bdf8",
                            color: "#38bdf8",
                            borderRadius: "4px",
                            padding: "2px 6px",
                            fontSize: "0.68rem",
                            cursor: "pointer",
                          }}
                        >
                          Spotlight
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </section>
        </>
      )}
    </section>
  );
};
