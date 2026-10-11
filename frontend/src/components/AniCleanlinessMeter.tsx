import React, { useState } from "react";

export interface AniCleanlinessMeterProps {
  aniLevel: number | null | undefined;
  compact?: boolean;
  showExplanation?: boolean;
  badgePrefix?: string;
}

export const AniCleanlinessMeter: React.FC<AniCleanlinessMeterProps> = ({
  aniLevel,
  compact = false,
  showExplanation = true,
  badgePrefix = "ANI ",
}) => {
  const [showModal, setShowModal] = useState(false);

  if (aniLevel === null || aniLevel === undefined) {
    return (
      <span
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "4px",
          backgroundColor: "#1e293b",
          color: "#94a3b8",
          padding: "2px 6px",
          borderRadius: "4px",
          fontSize: compact ? "0.68rem" : "0.75rem",
        }}
      >
        <span>ANI N/A</span>
        <span style={{ fontSize: "0.65rem", color: "#64748b" }}>(Wi-Fi/Wired)</span>
      </span>
    );
  }

  const level = Math.max(0, Math.min(9, aniLevel));

  let statusText = "Clean Air";
  let statusColor = "#10b981"; // emerald-500
  let badgeBg = "#064e3b";
  let description = "Antenna receiver operating at 100% full sensitivity. Zero local interference.";

  if (level >= 7) {
    statusText = "Severe Electronic EMI";
    statusColor = "#ef4444"; // red-500
    badgeBg = "#7f1d1d";
    description =
      "Radio receiver heavily desensitized to reject local electronic noise. Audio packet corruption risk.";
  } else if (level >= 4) {
    statusText = "Elevated Hash";
    statusColor = "#f59e0b"; // amber-500
    badgeBg = "#78350f";
    description =
      "Background electromagnetic hash detected. Radio stepped up carrier sensitivity threshold.";
  }

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        flexWrap: "wrap",
      }}
    >
      {/* Visual Meter Bar */}
      <div
        style={{
          display: "inline-flex",
          gap: "2px",
          padding: "2px 4px",
          backgroundColor: "#0f172a",
          borderRadius: "4px",
          border: "1px solid #334155",
        }}
        title={`OFDM ANI Level ${level}/9: ${statusText}`}
      >
        {[...Array(10)].map((_, i) => {
          const isActive = i <= level;
          let barColor = "#334155";
          if (isActive) {
            if (i <= 3) barColor = "#10b981";
            else if (i <= 6) barColor = "#f59e0b";
            else barColor = "#ef4444";
          }
          return (
            <div
              key={i}
              style={{
                width: compact ? "3px" : "4px",
                height: compact ? "10px" : "14px",
                backgroundColor: barColor,
                borderRadius: "1px",
              }}
            />
          );
        })}
      </div>

      {/* Status Badge */}
      <span
        style={{
          backgroundColor: badgeBg,
          color: statusColor,
          padding: compact ? "1px 6px" : "2px 8px",
          borderRadius: "999px",
          fontSize: compact ? "0.68rem" : "0.74rem",
          fontWeight: 700,
          border: `1px solid ${statusColor}`,
          display: "inline-flex",
          alignItems: "center",
          gap: "4px",
        }}
      >
        <span>{badgePrefix}{level}</span>
        {!compact && <span>· {statusText}</span>}
      </span>

      {/* Info Button */}
      {showExplanation && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            setShowModal(true);
          }}
          aria-label="Explain OFDM ANI"
          style={{
            background: "transparent",
            border: "1px solid #475569",
            borderRadius: "50%",
            color: "#94a3b8",
            width: "18px",
            height: "18px",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "0.65rem",
            cursor: "pointer",
            fontWeight: 700,
            padding: 0,
          }}
          title="What is OFDM ANI?"
        >
          i
        </button>
      )}

      {/* Explanation Modal */}
      {showModal && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="ani-modal-title"
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.75)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 9999,
            padding: "20px",
          }}
          onClick={(e) => {
            e.stopPropagation();
            setShowModal(false);
          }}
        >
          <div
            style={{
              backgroundColor: "#1e293b",
              borderRadius: "12px",
              border: "1px solid #64748b",
              maxWidth: "520px",
              width: "100%",
              padding: "24px",
              color: "#f8fafc",
              boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.5)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "16px",
                borderBottom: "1px solid #334155",
                paddingBottom: "10px",
              }}
            >
              <h3
                id="ani-modal-title"
                style={{ margin: 0, color: "#38bdf8", fontSize: "1.1rem" }}
              >
                Understanding OFDM ANI (Adaptive Noise Immunity)
              </h3>
              <button
                type="button"
                onClick={() => setShowModal(false)}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#94a3b8",
                  fontSize: "1.2rem",
                  cursor: "pointer",
                  fontWeight: 700,
                }}
              >
                ×
              </button>
            </div>

            <div style={{ fontSize: "0.85rem", lineHeight: "1.5", color: "#cbd5e1" }}>
              <p style={{ marginTop: 0 }}>
                <strong>Current Value:</strong>{" "}
                <span style={{ color: statusColor, fontWeight: 700 }}>
                  ANI {level} / 9 ({statusText})
                </span>
                <br />
                <em>{description}</em>
              </p>

              <h4 style={{ margin: "14px 0 6px", color: "#f8fafc" }}>
                What does this scale mean?
              </h4>
              <ul style={{ paddingLeft: "20px", margin: "0 0 14px" }}>
                <li style={{ marginBottom: "6px" }}>
                  <strong style={{ color: "#10b981" }}>0 – 3 (Clean Spectrum)</strong>: The radio
                  operates at full sensitivity. High throughput and pristine audio streaming.
                </li>
                <li style={{ marginBottom: "6px" }}>
                  <strong style={{ color: "#f59e0b" }}>4 – 6 (Elevated Background Noise)</strong>:
                  Mild RF noise present. The chip adapts by raising carrier detection thresholds.
                </li>
                <li>
                  <strong style={{ color: "#ef4444" }}>7 – 9 (Severe Electronic EMI Flooding)</strong>:
                  The radio is blasted with extreme local noise and forcefully desensitizes its receiver.
                  This corrupts audio packets, triggering PHY errors and volume ducking.
                </li>
              </ul>

              <h4 style={{ margin: "14px 0 6px", color: "#f8fafc" }}>
                Why does this happen if no Wi-Fi network is there?
              </h4>
              <p style={{ margin: "0 0 10px" }}>
                The 2.4 GHz spectrum is shared by electronics. High-speed <strong>USB 3.0 / USB-C docks</strong>,
                switching power bricks, unshielded HDMI cables, and laptop chargers emit broad-spectrum
                electromagnetic interference (EMI) around 2.4–2.5 GHz.
              </p>
              <div
                style={{
                  backgroundColor: "#0f172a",
                  padding: "10px 14px",
                  borderRadius: "6px",
                  borderLeft: "3px solid #ef4444",
                  fontSize: "0.8rem",
                }}
              >
                <strong>The Sequential Isolation Test:</strong>
                <br />
                Unplug suspect electronic devices (USB-C dock, laptop charger) one by one while watching
                the live PHY error counter. When errors plunge to <strong>0.0 err/s</strong>, you have
                isolated the offending power brick or cable!
              </div>
            </div>

            <div style={{ marginTop: "20px", textAlign: "right" }}>
              <button
                type="button"
                onClick={() => setShowModal(false)}
                style={{
                  backgroundColor: "#0284c7",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "6px",
                  padding: "6px 16px",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Got it
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
