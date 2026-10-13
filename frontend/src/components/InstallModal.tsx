import React from "react";

interface InstallModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const API_BASE =
  (import.meta as unknown as { env?: Record<string, string> }).env
    ?.VITE_API_BASE_URL ?? "http://192.168.55.60:8001";

export function InstallModal({ isOpen, onClose }: InstallModalProps) {
  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Install Android App Modal"
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.75)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 9999,
        padding: "16px",
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: "#1e293b",
          border: "1px solid #334155",
          borderRadius: "16px",
          maxWidth: "480px",
          width: "100%",
          padding: "28px 24px",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.7)",
          position: "relative",
          textAlign: "center",
          color: "#f8fafc",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          onClick={onClose}
          aria-label="Close install modal"
          style={{
            position: "absolute",
            top: "16px",
            right: "16px",
            background: "none",
            border: "none",
            color: "#94a3b8",
            fontSize: "1.4rem",
            cursor: "pointer",
            padding: "4px 8px",
          }}
        >
          ✕
        </button>

        <div
          style={{
            display: "inline-block",
            backgroundColor: "#064e3b",
            color: "#6ee7b7",
            border: "1px solid #10b981",
            padding: "3px 10px",
            borderRadius: "6px",
            fontSize: "0.75rem",
            fontWeight: 700,
            marginBottom: "12px",
          }}
        >
          Local Wi-Fi & Firewalla VPN Ready
        </div>

        <h2 style={{ margin: "0 0 6px", fontSize: "1.35rem", color: "#38bdf8" }}>
          Install Sonos Network Companion
        </h2>
        <p style={{ margin: "0 0 20px", color: "#94a3b8", fontSize: "0.88rem" }}>
          Scan the QR code with your phone camera or tap download.
        </p>

        <div
          style={{
            display: "inline-block",
            backgroundColor: "#ffffff",
            padding: "14px",
            borderRadius: "12px",
            boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.4)",
            marginBottom: "20px",
          }}
        >
          <img
            src={`${API_BASE}/api/companion/qr`}
            alt="Companion App Installation QR Code"
            style={{ display: "block", width: "200px", height: "200px" }}
          />
        </div>

        <div style={{ marginBottom: "20px" }}>
          <a
            href={`${API_BASE}/api/companion/apk`}
            download="sonos-network-companion.apk"
            style={{
              display: "inline-block",
              backgroundColor: "#0284c7",
              color: "#ffffff",
              padding: "10px 22px",
              borderRadius: "8px",
              fontWeight: 700,
              textDecoration: "none",
              fontSize: "0.95rem",
              boxShadow: "0 4px 6px -1px rgba(2, 132, 199, 0.3)",
            }}
          >
            ⬇️ Download APK Directly
          </a>
        </div>

        <div
          style={{
            backgroundColor: "#0f172a",
            border: "1px solid #334155",
            borderRadius: "8px",
            padding: "14px 18px",
            textAlign: "left",
            fontSize: "0.82rem",
            color: "#cbd5e1",
            lineHeight: 1.5,
          }}
        >
          <strong style={{ color: "#38bdf8" }}>Quick Install Steps:</strong>
          <ol style={{ margin: "6px 0 0", paddingLeft: "18px" }}>
            <li>Scan QR with Android camera or download APK directly.</li>
            <li>Tap downloaded APK to install (allow <em>Unknown Sources</em>).</li>
            <li>Connect to <strong>WuTangLan-Family</strong> or <strong>Firewalla VPN</strong>.</li>
            <li>Open app to inspect live rooms and trigger 1-click UPnP actions.</li>
          </ol>
        </div>
      </div>
    </div>
  );
}
