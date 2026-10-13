import React, { useState } from "react";
import { RoomHistoryResponse, RoomHistoryRollupBucket } from "../types/topology";

interface YearlyHistoricalVisualizerProps {
  roomHistory: RoomHistoryResponse;
  currentRange: string;
  onRangeChange?: (range: "1h" | "24h" | "7d" | "30d" | "90d" | "1y") => void;
  busy?: boolean;
}

export const YearlyHistoricalVisualizer: React.FC<YearlyHistoricalVisualizerProps> = ({
  roomHistory,
  currentRange,
  onRangeChange,
  busy,
}) => {
  const isLongTerm = ["30d", "90d", "365d", "1y"].includes(currentRange);
  const [viewMode, setViewMode] = useState<"MONTHLY" | "WEEKLY" | "SAMPLES">(
    currentRange === "1y" || currentRange === "365d"
      ? "MONTHLY"
      : isLongTerm
      ? "WEEKLY"
      : "SAMPLES"
  );
  const [selectedBucket, setSelectedBucket] = useState<RoomHistoryRollupBucket | null>(
    roomHistory.rollup_buckets.length > 0
      ? roomHistory.rollup_buckets[roomHistory.rollup_buckets.length - 1]
      : null
  );

  const buckets = roomHistory.rollup_buckets;

  const getAniColor = (ani: number | null | undefined): string => {
    if (ani === null || ani === undefined) return "#64748b";
    if (ani <= 3) return "#10b981"; // Clean
    if (ani <= 6) return "#f59e0b"; // Elevated
    return "#ef4444"; // Severe
  };

  const getHealthBadgeStyle = (grade: string) => {
    switch (grade) {
      case "EXCELLENT":
        return { bg: "#064e3b", text: "#6ee7b7", border: "#10b981" };
      case "GOOD":
        return { bg: "#065f46", text: "#a7f3d0", border: "#34d399" };
      case "MARGINAL":
        return { bg: "#78350f", text: "#fde68a", border: "#f59e0b" };
      case "CRITICAL":
      default:
        return { bg: "#7f1d1d", text: "#fecaca", border: "#ef4444" };
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "16px",
      }}
    >
      {/* View Mode & Range Toolbar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "10px",
          backgroundColor: "#0f172a",
          padding: "10px 14px",
          borderRadius: "8px",
          border: "1px solid #334155",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "0.8rem", color: "#94a3b8", fontWeight: 600 }}>
            Visualization Mode:
          </span>
          <div style={{ display: "flex", gap: "4px" }}>
            <button
              type="button"
              disabled={buckets.length === 0}
              onClick={() => setViewMode("MONTHLY")}
              style={{
                backgroundColor: viewMode === "MONTHLY" ? "#0284c7" : "#1e293b",
                color: "#f8fafc",
                border: "1px solid #38bdf8",
                borderRadius: "4px",
                padding: "4px 10px",
                fontSize: "0.76rem",
                fontWeight: 700,
                cursor: buckets.length === 0 ? "not-allowed" : "pointer",
                opacity: buckets.length === 0 ? 0.5 : 1,
              }}
            >
              📅 Monthly Rollup
            </button>
            <button
              type="button"
              disabled={buckets.length === 0}
              onClick={() => setViewMode("WEEKLY")}
              style={{
                backgroundColor: viewMode === "WEEKLY" ? "#0284c7" : "#1e293b",
                color: "#f8fafc",
                border: "1px solid #38bdf8",
                borderRadius: "4px",
                padding: "4px 10px",
                fontSize: "0.76rem",
                fontWeight: 700,
                cursor: buckets.length === 0 ? "not-allowed" : "pointer",
                opacity: buckets.length === 0 ? 0.5 : 1,
              }}
            >
              📆 Weekly Rollup
            </button>
            <button
              type="button"
              onClick={() => setViewMode("SAMPLES")}
              style={{
                backgroundColor: viewMode === "SAMPLES" ? "#0284c7" : "#1e293b",
                color: "#f8fafc",
                border: "1px solid #38bdf8",
                borderRadius: "4px",
                padding: "4px 10px",
                fontSize: "0.76rem",
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              📊 Sample Points ({roomHistory.samples.length})
            </button>
          </div>
        </div>

        {onRangeChange && (
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ fontSize: "0.76rem", color: "#94a3b8" }}>Range:</span>
            {(["1h", "24h", "7d", "30d", "90d", "1y"] as const).map((r) => (
              <button
                key={r}
                type="button"
                disabled={Boolean(busy)}
                onClick={() => onRangeChange(r)}
                style={{
                  backgroundColor: currentRange === r ? "#0284c7" : "#1e293b",
                  color: "#f8fafc",
                  border: currentRange === r ? "1px solid #38bdf8" : "1px solid #475569",
                  borderRadius: "4px",
                  padding: "3px 8px",
                  fontSize: "0.75rem",
                  fontWeight: currentRange === r ? 700 : 500,
                  cursor: busy ? "not-allowed" : "pointer",
                }}
              >
                {r === "1y" ? "365d (1y)" : r}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Seasonal Health Heatmap Strip */}
      {buckets.length > 0 && viewMode !== "SAMPLES" && (
        <div
          style={{
            backgroundColor: "#0f172a",
            padding: "12px",
            borderRadius: "8px",
            border: "1px solid #334155",
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
            <span style={{ fontSize: "0.78rem", fontWeight: 700, color: "#cbd5e1" }}>
              🗓️ Yearly Temporal Heatmap &amp; RF Stability Drift
            </span>
            <div style={{ display: "flex", gap: "8px", fontSize: "0.7rem", color: "#94a3b8" }}>
              <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                <span
                  style={{
                    width: "8px",
                    height: "8px",
                    backgroundColor: "#10b981",
                    borderRadius: "2px",
                  }}
                />
                Clean (ANI 0-3)
              </span>
              <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                <span
                  style={{
                    width: "8px",
                    height: "8px",
                    backgroundColor: "#f59e0b",
                    borderRadius: "2px",
                  }}
                />
                Elevated (ANI 4-6)
              </span>
              <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                <span
                  style={{
                    width: "8px",
                    height: "8px",
                    backgroundColor: "#ef4444",
                    borderRadius: "2px",
                  }}
                />
                Critical EMI (ANI 7-9)
              </span>
            </div>
          </div>

          <div
            style={{
              display: "flex",
              gap: "4px",
              flexWrap: "wrap",
              padding: "4px 0",
            }}
          >
            {buckets.map((b) => {
              const isSelected = selectedBucket?.bucket_key === b.bucket_key;
              const aniColor = getAniColor(b.peak_ofdm_ani_level);
              return (
                <button
                  key={b.bucket_key}
                  type="button"
                  onClick={() => setSelectedBucket(b)}
                  title={`${b.bucket_label}: Peak ANI ${b.peak_ofdm_ani_level ?? "N/A"}, PHY ${b.avg_phy_error_rate ?? 0} err/s (${b.sample_count} samples)`}
                  style={{
                    flex: "1 1 28px",
                    minWidth: "24px",
                    height: "36px",
                    backgroundColor: aniColor,
                    border: isSelected ? "2px solid #ffffff" : "1px solid rgba(0,0,0,0.3)",
                    borderRadius: "4px",
                    cursor: "pointer",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "center",
                    alignItems: "center",
                    padding: "2px",
                    transition: "transform 0.1s",
                    transform: isSelected ? "scale(1.08)" : "none",
                  }}
                >
                  <span
                    style={{
                      fontSize: "0.6rem",
                      fontWeight: 700,
                      color: "#ffffff",
                      textShadow: "0 1px 2px rgba(0,0,0,0.8)",
                    }}
                  >
                    {b.bucket_key.split("-")[1]}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Selected Bucket Detail Banner */}
      {selectedBucket && viewMode !== "SAMPLES" && (
        <div
          style={{
            backgroundColor: "#1e293b",
            border: "1px solid #38bdf8",
            borderRadius: "8px",
            padding: "14px",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
            gap: "12px",
          }}
        >
          <div>
            <div style={{ color: "#94a3b8", fontSize: "0.7rem", fontWeight: 600 }}>
              BUCKET PERIOD
            </div>
            <div style={{ fontSize: "1.05rem", fontWeight: 700, color: "#f8fafc" }}>
              {selectedBucket.bucket_label}
            </div>
            <div style={{ fontSize: "0.7rem", color: "#64748b" }}>
              {selectedBucket.sample_count} samples logged
            </div>
          </div>

          <div>
            <div style={{ color: "#94a3b8", fontSize: "0.7rem", fontWeight: 600 }}>
              OFDM ANI LEVEL
            </div>
            <div
              style={{
                fontSize: "1.05rem",
                fontWeight: 700,
                color: getAniColor(selectedBucket.peak_ofdm_ani_level),
              }}
            >
              Peak: {selectedBucket.peak_ofdm_ani_level ?? "N/A"}{" "}
              <span style={{ fontSize: "0.76rem", color: "#94a3b8" }}>
                (Avg: {selectedBucket.avg_ofdm_ani_level ?? "N/A"})
              </span>
            </div>
          </div>

          <div>
            <div style={{ color: "#94a3b8", fontSize: "0.7rem", fontWeight: 600 }}>
              PHY ERROR RATE
            </div>
            <div
              style={{
                fontSize: "1.05rem",
                fontWeight: 700,
                color:
                  selectedBucket.avg_phy_error_rate && selectedBucket.avg_phy_error_rate > 100
                    ? "#ef4444"
                    : "#10b981",
              }}
            >
              Avg: {selectedBucket.avg_phy_error_rate ?? 0.0} err/s
              {selectedBucket.peak_phy_error_rate !== null &&
                selectedBucket.peak_phy_error_rate !== undefined && (
                  <span style={{ fontSize: "0.72rem", color: "#94a3b8", display: "block" }}>
                    Peak burst: {selectedBucket.peak_phy_error_rate} err/s
                  </span>
                )}
            </div>
          </div>

          <div>
            <div style={{ color: "#94a3b8", fontSize: "0.7rem", fontWeight: 600 }}>
              AVG PING RTT
            </div>
            <div style={{ fontSize: "1.05rem", fontWeight: 700, color: "#38bdf8" }}>
              {selectedBucket.avg_ping_rtt_ms !== null && selectedBucket.avg_ping_rtt_ms !== undefined
                ? `${selectedBucket.avg_ping_rtt_ms} ms`
                : "N/A"}
            </div>
          </div>

          <div>
            <div style={{ color: "#94a3b8", fontSize: "0.7rem", fontWeight: 600 }}>
              HEALTH GRADE
            </div>
            <div>
              {(() => {
                const badge = getHealthBadgeStyle(selectedBucket.health_grade);
                return (
                  <span
                    style={{
                      display: "inline-block",
                      backgroundColor: badge.bg,
                      color: badge.text,
                      border: `1px solid ${badge.border}`,
                      borderRadius: "4px",
                      padding: "2px 8px",
                      fontSize: "0.78rem",
                      fontWeight: 700,
                    }}
                  >
                    {selectedBucket.health_grade}
                  </span>
                );
              })()}
            </div>
          </div>
        </div>
      )}

      {/* Visual Bar Columns Chart */}
      {buckets.length > 0 && viewMode !== "SAMPLES" && (
        <div
          style={{
            backgroundColor: "#0f172a",
            padding: "16px",
            borderRadius: "8px",
            border: "1px solid #334155",
          }}
        >
          <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#cbd5e1", marginBottom: "12px" }}>
            📊 {viewMode === "MONTHLY" ? "Monthly" : "Weekly"} Interference &amp; PHY Corruption Distribution
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "flex-end",
              gap: "8px",
              height: "180px",
              paddingBottom: "24px",
              borderBottom: "1px solid #334155",
              position: "relative",
              overflowX: "auto",
            }}
          >
            {buckets.map((b) => {
              const ani = b.peak_ofdm_ani_level ?? 0;
              // ANI scale 0-9 mapped to 15% to 100% height
              const heightPct = Math.max(12, (ani / 9) * 100);
              const color = getAniColor(b.peak_ofdm_ani_level);
              const isSelected = selectedBucket?.bucket_key === b.bucket_key;

              return (
                <div
                  key={b.bucket_key}
                  onClick={() => setSelectedBucket(b)}
                  style={{
                    flex: "1 1 36px",
                    minWidth: "32px",
                    height: "100%",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "flex-end",
                    alignItems: "center",
                    cursor: "pointer",
                  }}
                >
                  <span
                    style={{
                      fontSize: "0.68rem",
                      fontWeight: 700,
                      color: color,
                      marginBottom: "4px",
                    }}
                  >
                    {b.peak_ofdm_ani_level !== null && b.peak_ofdm_ani_level !== undefined
                      ? `ANI ${b.peak_ofdm_ani_level}`
                      : "—"}
                  </span>
                  <div
                    style={{
                      width: "100%",
                      maxWidth: "38px",
                      height: `${heightPct}%`,
                      backgroundColor: color,
                      borderRadius: "4px 4px 0 0",
                      border: isSelected ? "2px solid #ffffff" : "none",
                      boxShadow: isSelected ? "0 0 8px rgba(56, 189, 248, 0.8)" : "none",
                      transition: "height 0.2s, background-color 0.2s",
                    }}
                  />
                  <span
                    style={{
                      position: "absolute",
                      bottom: "4px",
                      fontSize: "0.65rem",
                      color: isSelected ? "#38bdf8" : "#94a3b8",
                      fontWeight: isSelected ? 700 : 500,
                      whiteSpace: "nowrap",
                    }}
                  >
                    {b.bucket_key.split("-")[1]}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Raw Sample Points Table (when in SAMPLES mode) */}
      {viewMode === "SAMPLES" && (
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
                        pt.peak_ofdm_ani_level && pt.peak_ofdm_ani_level >= 7
                          ? "#ef4444"
                          : "#f8fafc",
                    }}
                  >
                    {pt.peak_ofdm_ani_level !== null && pt.peak_ofdm_ani_level !== undefined
                      ? `ANI ${pt.peak_ofdm_ani_level}`
                      : "N/A"}
                  </td>
                  <td style={{ padding: "8px" }}>
                    {pt.total_phy_error_rate !== null && pt.total_phy_error_rate !== undefined
                      ? `${pt.total_phy_error_rate} err/s`
                      : "0.0 err/s"}
                  </td>
                  <td style={{ padding: "8px" }}>
                    {pt.avg_ping_rtt_ms !== null && pt.avg_ping_rtt_ms !== undefined
                      ? `${pt.avg_ping_rtt_ms} ms`
                      : "N/A"}
                  </td>
                  <td style={{ padding: "8px" }}>
                    {pt.best_5ghz_dbm ? `${pt.best_5ghz_dbm} dBm` : "N/A"}
                  </td>
                  <td style={{ padding: "8px" }}>
                    {pt.worst_stp_path_cost !== null && pt.worst_stp_path_cost !== undefined
                      ? pt.worst_stp_path_cost
                      : "N/A"}
                  </td>
                  <td style={{ padding: "8px" }}>
                    <span
                      style={{
                        padding: "2px 6px",
                        borderRadius: "3px",
                        fontSize: "0.72rem",
                        fontWeight: 700,
                        backgroundColor:
                          pt.health_grade === "CRITICAL"
                            ? "#7f1d1d"
                            : pt.health_grade === "MARGINAL"
                            ? "#78350f"
                            : "#064e3b",
                        color:
                          pt.health_grade === "CRITICAL"
                            ? "#fecaca"
                            : pt.health_grade === "MARGINAL"
                            ? "#fde68a"
                            : "#6ee7b7",
                      }}
                    >
                      {pt.health_grade}
                    </span>
                  </td>
                  <td style={{ padding: "8px" }}>
                    {pt.players.map((pl) => (
                      <span
                        key={pl.rincon_uuid}
                        style={{
                          display: "inline-block",
                          marginRight: "6px",
                          color: "#cbd5e1",
                        }}
                      >
                        {pl.zone_name} ({pl.connection_mode})
                      </span>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
