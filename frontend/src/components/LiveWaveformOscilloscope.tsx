import React, { useEffect, useMemo, useRef, useState } from "react";
import type { LiveRfSample } from "../types/topology";
import { AniCleanlinessMeter } from "./AniCleanlinessMeter";

export interface LiveWaveformOscilloscopeProps {
  samples: LiveRfSample[];
  isConnected: boolean;
  isPaused: boolean;
  onTogglePause?: () => void;
  roomFilter?: string;
  onRoomFilterChange?: (room: string) => void;
  availableRooms?: { slug: string; name: string }[];
}

interface TimePoint {
  timestamp: number;
  timeStr: string;
  phyErrorRate: number;
  aniLevel: number | null;
}

export const LiveWaveformOscilloscope: React.FC<LiveWaveformOscilloscopeProps> = ({
  samples,
  isConnected,
  isPaused,
  onTogglePause,
  roomFilter = "all",
  onRoomFilterChange,
  availableRooms = [],
}) => {
  // Select speaker to focus waveform on
  const [selectedSpeakerId, setSelectedSpeakerId] = useState<string>("auto-worst");
  const [historySeconds, setHistorySeconds] = useState<number>(45);

  // Time-series history buffer per speaker rincon_uuid
  const historyRef = useRef<Map<string, TimePoint[]>>(new Map());
  const [, setTick] = useState<number>(0);

  // Determine active speaker list from current samples
  const activeSpeakers = useMemo(() => {
    return samples.map((s) => ({
      uuid: s.rincon_uuid,
      name: s.zone_name,
      ani: s.ofdm_ani_level,
      rate: s.phy_error_rate,
    }));
  }, [samples]);

  // Identify speaker with highest current PHY error rate
  const worstSpeaker = useMemo(() => {
    if (samples.length === 0) return null;
    return [...samples].sort((a, b) => b.phy_error_rate - a.phy_error_rate)[0];
  }, [samples]);

  // Actual speaker being tracked
  const targetUuid = useMemo(() => {
    if (selectedSpeakerId === "auto-worst") {
      return worstSpeaker?.rincon_uuid ?? samples[0]?.rincon_uuid ?? null;
    }
    return selectedSpeakerId;
  }, [selectedSpeakerId, worstSpeaker, samples]);

  const targetSample = useMemo(() => {
    if (!targetUuid) return null;
    return samples.find((s) => s.rincon_uuid === targetUuid) ?? null;
  }, [samples, targetUuid]);

  // Update history buffer when samples change
  useEffect(() => {
    if (isPaused || samples.length === 0) return;
    const now = Date.now();
    const cutoff = now - historySeconds * 1000;
    const timeStr = new Date(now).toLocaleTimeString();

    for (const s of samples) {
      let speakerPoints = historyRef.current.get(s.rincon_uuid);
      if (!speakerPoints) {
        speakerPoints = [];
        historyRef.current.set(s.rincon_uuid, speakerPoints);
      }
      speakerPoints.push({
        timestamp: now,
        timeStr,
        phyErrorRate: s.phy_error_rate,
        aniLevel: s.ofdm_ani_level ?? null,
      });

      // Filter points older than cutoff
      const filtered = speakerPoints.filter((p) => p.timestamp >= cutoff);
      historyRef.current.set(s.rincon_uuid, filtered);
    }

    setTick((t) => t + 1);
  }, [samples, isPaused, historySeconds]);

  // Get points for target speaker
  const currentPoints = useMemo(() => {
    if (!targetUuid) return [];
    return historyRef.current.get(targetUuid) ?? [];
  }, [targetUuid, samples]);

  // Calculate statistics in window
  const stats = useMemo(() => {
    if (currentPoints.length === 0) {
      return {
        current: targetSample?.phy_error_rate ?? 0,
        peak: targetSample?.phy_error_rate ?? 0,
        avg: targetSample?.phy_error_rate ?? 0,
      };
    }
    const rates = currentPoints.map((p) => p.phyErrorRate);
    const peak = Math.max(...rates);
    const avg = rates.reduce((a, b) => a + b, 0) / rates.length;
    const current = rates[rates.length - 1] ?? 0;
    return { current, peak, avg };
  }, [currentPoints, targetSample]);

  // SVG chart dimensions
  const svgWidth = 840;
  const svgHeight = 220;
  const padding = { top: 20, right: 30, bottom: 35, left: 55 };
  const graphWidth = svgWidth - padding.left - padding.right;
  const graphHeight = svgHeight - padding.top - padding.bottom;

  // Maximum scale for Y-axis (dynamic with minimum 50 err/s)
  const maxY = useMemo(() => {
    const rawMax = Math.max(stats.peak * 1.15, 30);
    // Round up to clean increments
    if (rawMax <= 50) return 50;
    if (rawMax <= 200) return 200;
    if (rawMax <= 500) return 500;
    if (rawMax <= 1200) return 1200;
    return Math.ceil(rawMax / 500) * 500;
  }, [stats.peak]);

  // Compute SVG coordinates
  const now = Date.now();
  const startTime = now - historySeconds * 1000;

  const pointsCoordinates = useMemo(() => {
    if (currentPoints.length === 0) return [];
    return currentPoints.map((p) => {
      const xRatio = Math.max(0, Math.min(1, (p.timestamp - startTime) / (historySeconds * 1000)));
      const x = padding.left + xRatio * graphWidth;
      const yRatio = Math.max(0, Math.min(1, p.phyErrorRate / maxY));
      const y = padding.top + (1 - yRatio) * graphHeight;
      return { x, y, ...p };
    });
  }, [currentPoints, startTime, historySeconds, graphWidth, graphHeight, maxY, padding]);

  // Build SVG path
  const pathD = useMemo(() => {
    if (pointsCoordinates.length === 0) return "";
    return pointsCoordinates.reduce((acc, p, idx) => {
      return idx === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`;
    }, "");
  }, [pointsCoordinates]);

  // Build SVG area fill path
  const areaD = useMemo(() => {
    if (pointsCoordinates.length === 0) return "";
    const bottomY = padding.top + graphHeight;
    const firstX = pointsCoordinates[0].x;
    const lastX = pointsCoordinates[pointsCoordinates.length - 1].x;
    return `${pathD} L ${lastX} ${bottomY} L ${firstX} ${bottomY} Z`;
  }, [pathD, pointsCoordinates, padding.top, graphHeight]);

  // Severity color based on current error rate
  let severityColor = "#10b981"; // green < 20
  let severityText = "Clean Spectrum (< 20 err/s)";
  if (stats.current >= 100) {
    severityColor = "#ef4444"; // red >= 100
    severityText = "Severe RF Jamming / Audio Ducking Risk (> 100 err/s)";
  } else if (stats.current >= 20) {
    severityColor = "#f59e0b"; // amber 20..100
    severityText = "Elevated Hash (20–100 err/s)";
  }

  return (
    <div
      style={{
        backgroundColor: "#0f172a",
        borderRadius: "12px",
        border: "1px solid #334155",
        padding: "20px",
        marginBottom: "24px",
        boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.4)",
      }}
      data-testid="live-waveform-oscilloscope"
    >
      {/* Top Header Bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
          marginBottom: "16px",
          borderBottom: "1px solid #1e293b",
          paddingBottom: "14px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span
              style={{
                width: "10px",
                height: "10px",
                borderRadius: "50%",
                backgroundColor: isConnected ? (isPaused ? "#f59e0b" : "#10b981") : "#ef4444",
                boxShadow: isConnected && !isPaused ? "0 0 10px #10b981" : "none",
                display: "inline-block",
              }}
            />
            <h3 style={{ margin: 0, color: "#f8fafc", fontSize: "1.1rem" }}>
              Live RF & PHY Error Oscilloscope
            </h3>
            <span
              style={{
                fontSize: "0.72rem",
                padding: "2px 8px",
                borderRadius: "999px",
                backgroundColor: isConnected ? "#064e3b" : "#7f1d1d",
                color: isConnected ? "#6ee7b7" : "#fca5a5",
                fontWeight: 700,
              }}
            >
              {isConnected ? (isPaused ? "STREAM PAUSED" : "LIVE 1.5s POLLING") : "CONNECTING..."}
            </span>
          </div>
          <p style={{ margin: "4px 0 0", fontSize: "0.8rem", color: "#94a3b8" }}>
            Real-time Atheros packet corruption velocity ({historySeconds}s rolling window) for sequential EMI hunting
          </p>
        </div>

        {/* Controls */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          {/* Target Speaker Selector */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <label htmlFor="waveform-speaker-select" style={{ fontSize: "0.78rem", color: "#94a3b8" }}>
              Monitored Speaker:
            </label>
            <select
              id="waveform-speaker-select"
              value={selectedSpeakerId}
              onChange={(e) => setSelectedSpeakerId(e.target.value)}
              style={{
                backgroundColor: "#1e293b",
                color: "#f8fafc",
                border: "1px solid #475569",
                borderRadius: "6px",
                padding: "4px 8px",
                fontSize: "0.78rem",
              }}
            >
              <option value="auto-worst">
                ⚡ Auto: Worst ({worstSpeaker ? `Node ${worstSpeaker.zone_name}` : "None"})
              </option>
              {activeSpeakers.map((s) => (
                <option key={s.uuid} value={s.uuid}>
                  Node: {s.name}
                </option>
              ))}
            </select>
          </div>

          {/* Time Window Selector */}
          <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            {[30, 45, 60].map((sec) => (
              <button
                key={sec}
                type="button"
                onClick={() => setHistorySeconds(sec)}
                style={{
                  backgroundColor: historySeconds === sec ? "#0284c7" : "#1e293b",
                  color: historySeconds === sec ? "#ffffff" : "#94a3b8",
                  border: "1px solid #334155",
                  borderRadius: "4px",
                  padding: "3px 8px",
                  fontSize: "0.72rem",
                  cursor: "pointer",
                }}
              >
                {sec}s
              </button>
            ))}
          </div>

          {/* Pause / Resume */}
          {onTogglePause && (
            <button
              type="button"
              onClick={onTogglePause}
              style={{
                backgroundColor: isPaused ? "#059669" : "#d97706",
                color: "#ffffff",
                border: "none",
                borderRadius: "6px",
                padding: "4px 12px",
                fontSize: "0.78rem",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              {isPaused ? "▶ Resume" : "⏸ Pause"}
            </button>
          )}
        </div>
      </div>

      {/* KPI Highlight Strip */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "12px",
          marginBottom: "16px",
        }}
      >
        {/* Current PHY Rate */}
        <div
          style={{
            backgroundColor: "#1e293b",
            padding: "10px 14px",
            borderRadius: "8px",
            borderLeft: `4px solid ${severityColor}`,
          }}
        >
          <div style={{ fontSize: "0.72rem", color: "#94a3b8", textTransform: "uppercase", fontWeight: 700 }}>
            Current PHY Error Rate
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: "6px", marginTop: "2px" }}>
            <span style={{ fontSize: "1.45rem", fontWeight: 800, color: severityColor }}>
              {stats.current.toFixed(1)}
            </span>
            <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>errors/s</span>
          </div>
          <div style={{ fontSize: "0.7rem", color: severityColor, marginTop: "2px", fontWeight: 600 }}>
            {severityText}
          </div>
        </div>

        {/* Peak in Window */}
        <div
          style={{
            backgroundColor: "#1e293b",
            padding: "10px 14px",
            borderRadius: "8px",
            border: "1px solid #334155",
          }}
        >
          <div style={{ fontSize: "0.72rem", color: "#94a3b8", textTransform: "uppercase", fontWeight: 700 }}>
            Window Peak / Average
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginTop: "2px" }}>
            <span style={{ fontSize: "1.25rem", fontWeight: 800, color: "#f8fafc" }}>
              {stats.peak.toFixed(1)}
            </span>
            <span style={{ fontSize: "0.75rem", color: "#64748b" }}>peak</span>
            <span style={{ fontSize: "1.05rem", fontWeight: 700, color: "#94a3b8", marginLeft: "6px" }}>
              {stats.avg.toFixed(1)}
            </span>
            <span style={{ fontSize: "0.75rem", color: "#64748b" }}>avg</span>
          </div>
          <div style={{ fontSize: "0.7rem", color: "#94a3b8", marginTop: "2px" }}>
            Active Speaker: <strong style={{ color: "#38bdf8" }}>Focus: {targetSample?.zone_name ?? "None"}</strong>
          </div>
        </div>

        {/* Atheros Noise Immunity Meter */}
        <div
          style={{
            backgroundColor: "#1e293b",
            padding: "10px 14px",
            borderRadius: "8px",
            border: "1px solid #334155",
          }}
        >
          <div style={{ fontSize: "0.72rem", color: "#94a3b8", textTransform: "uppercase", fontWeight: 700 }}>
            Adaptive Noise Immunity (ANI)
          </div>
          <div style={{ marginTop: "6px" }}>
            <AniCleanlinessMeter aniLevel={targetSample?.ofdm_ani_level} showExplanation={true} badgePrefix="Immunity " />
          </div>
          <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "4px" }}>
            Noise floor: {targetSample?.noise_floor_dbm ? `${targetSample.noise_floor_dbm} dBm` : "N/A"}
          </div>
        </div>
      </div>

      {/* Real-time Oscilloscope SVG Canvas */}
      <div
        style={{
          backgroundColor: "#030712",
          borderRadius: "8px",
          border: "1px solid #1f2937",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          style={{ width: "100%", height: "auto", display: "block" }}
        >
          <defs>
            <linearGradient id="waveGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={severityColor} stopOpacity="0.35" />
              <stop offset="100%" stopColor={severityColor} stopOpacity="0.0" />
            </linearGradient>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Background Grid Lines */}
          {[0, 0.25, 0.5, 0.75, 1.0].map((ratio) => {
            const y = padding.top + (1 - ratio) * graphHeight;
            const val = ratio * maxY;
            return (
              <g key={ratio}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={padding.left + graphWidth}
                  y2={y}
                  stroke="#1f2937"
                  strokeWidth="1"
                  strokeDasharray="4 4"
                />
                <text
                  x={padding.left - 8}
                  y={y + 4}
                  textAnchor="end"
                  fill="#64748b"
                  fontSize="10"
                  fontFamily="monospace"
                >
                  {val.toFixed(0)}
                </text>
              </g>
            );
          })}

          {/* Time markers on X axis */}
          {[0, 0.25, 0.5, 0.75, 1.0].map((ratio) => {
            const x = padding.left + ratio * graphWidth;
            const secAgo = Math.round((1 - ratio) * historySeconds);
            return (
              <g key={ratio}>
                <line
                  x1={x}
                  y1={padding.top}
                  x2={x}
                  y2={padding.top + graphHeight}
                  stroke="#111827"
                  strokeWidth="1"
                />
                <text
                  x={x}
                  y={padding.top + graphHeight + 18}
                  textAnchor="middle"
                  fill="#64748b"
                  fontSize="10"
                  fontFamily="monospace"
                >
                  {secAgo === 0 ? "NOW" : `-${secAgo}s`}
                </text>
              </g>
            );
          })}

          {/* Threshold alert line at 100 err/s */}
          {maxY >= 100 && (
            <g>
              <line
                x1={padding.left}
                y1={padding.top + (1 - 100 / maxY) * graphHeight}
                x2={padding.left + graphWidth}
                y2={padding.top + (1 - 100 / maxY) * graphHeight}
                stroke="#ef4444"
                strokeWidth="1"
                strokeDasharray="6 3"
                opacity="0.6"
              />
              <text
                x={padding.left + graphWidth - 4}
                y={padding.top + (1 - 100 / maxY) * graphHeight - 4}
                textAnchor="end"
                fill="#fca5a5"
                fontSize="9"
                fontWeight="700"
              >
                100 err/s (DPC Ducking Threshold)
              </text>
            </g>
          )}

          {/* Filled Area below waveform */}
          {areaD && <path d={areaD} fill="url(#waveGradient)" />}

          {/* Glowing Waveform Line */}
          {pathD && (
            <path
              d={pathD}
              fill="none"
              stroke={severityColor}
              strokeWidth="2.5"
              filter="url(#glow)"
            />
          )}

          {/* Current Leading Point Indicator */}
          {pointsCoordinates.length > 0 && (
            <circle
              cx={pointsCoordinates[pointsCoordinates.length - 1].x}
              cy={pointsCoordinates[pointsCoordinates.length - 1].y}
              r="4.5"
              fill="#ffffff"
              stroke={severityColor}
              strokeWidth="2"
            />
          )}
        </svg>

        {/* Empty State Overlay */}
        {pointsCoordinates.length < 2 && (
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#94a3b8",
              fontSize: "0.85rem",
              backgroundColor: "rgba(3, 7, 18, 0.7)",
            }}
          >
            Streaming real-time telemetry... (waiting for samples)
          </div>
        )}
      </div>

      {/* Sequential EMI Isolation Procedure - Interactive Step-by-Step Guide */}
      <div
        style={{
          marginTop: "16px",
          backgroundColor: "#1e1b4b",
          border: "1px solid #4338ca",
          borderRadius: "8px",
          padding: "14px 18px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
          <span style={{ fontSize: "1.1rem" }}>🔍</span>
          <strong style={{ color: "#c7d2fe", fontSize: "0.9rem" }}>
            Sequential EMI Isolation Procedure
          </strong>
          <span style={{ fontSize: "0.75rem", color: "#a5b4fc" }}>
            (How to find the offending electronic device in under 2 minutes)
          </span>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
            gap: "12px",
            fontSize: "0.8rem",
            color: "#e0e7ff",
          }}
        >
          <div style={{ backgroundColor: "#312e81", padding: "10px 12px", borderRadius: "6px" }}>
            <strong style={{ color: "#facc15" }}>Step 1: Baseline</strong>
            <p style={{ margin: "4px 0 0", color: "#cbd5e1" }}>
              Observe the waveform above. In an EMI-flooded room (near suspect docks or active electronics),
              you will see elevated red spikes across the time series.
            </p>
          </div>

          <div style={{ backgroundColor: "#312e81", padding: "10px 12px", borderRadius: "6px" }}>
            <strong style={{ color: "#38bdf8" }}>Step 2: Unplug Sequentially</strong>
            <p style={{ margin: "4px 0 0", color: "#cbd5e1" }}>
              Unplug suspect devices one by one (USB-C laptop dock on Galerie desk, laptop power bricks, unshielded HDMI cables).
              Wait 5–10 seconds between each.
            </p>
          </div>

          <div style={{ backgroundColor: "#312e81", padding: "10px 12px", borderRadius: "6px" }}>
            <strong style={{ color: "#4ade80" }}>Step 3: Watch for the Plunge</strong>
            <p style={{ margin: "4px 0 0", color: "#cbd5e1" }}>
              When the waveform instantly plunges to <strong style={{ color: "#4ade80" }}>0.0 err/s</strong>, you have
              identified the exact noise emitter!
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
