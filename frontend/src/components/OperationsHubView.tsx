import React, { useState } from "react";
import type {
  DaemonStatus,
  DeepResetResult,
  GhostFlushResult,
  HouseholdSonosSnapshot,
  PingSweepResult,
  RoomMatrixItem,
} from "../types/topology";

interface OperationsHubViewProps {
  daemonStatus: DaemonStatus | null;
  onRefreshDaemon: () => Promise<void>;
  onToggleDaemon: () => Promise<void>;
  onTriggerDaemonCycle: () => Promise<void>;
  onFlushGhostGroups: (zoneIps?: string[]) => Promise<GhostFlushResult>;
  onPollLiveMesh: () => Promise<HouseholdSonosSnapshot>;
  onRunPingSweep: () => Promise<PingSweepResult>;
  onExecuteDeepReset: (zoneIps?: string[]) => Promise<DeepResetResult>;
  allRooms?: RoomMatrixItem[];
}

const DEFAULT_PLAYERS = [
  { name: "Wohnzimmer_Bookshelf (STP Root)", ip: "192.168.10.230" },
  { name: "Fernsehecke Beam", ip: "192.168.10.241" },
  { name: "Küche", ip: "192.168.10.202" },
  { name: "Nicolas", ip: "192.168.10.165" },
  { name: "Noah", ip: "192.168.10.229" },
  { name: "Noemi", ip: "192.168.10.244" },
  { name: "Eltern", ip: "192.168.10.131" },
  { name: "Elternbad", ip: "192.168.10.113" },
  { name: "Büroecke", ip: "192.168.10.151" },
  { name: "Keller", ip: "192.168.10.217" },
  { name: "Wohnzimmer_Buchregal", ip: "192.168.10.101" },
  { name: "Wohnzimmer_Esstisch", ip: "192.168.10.160" },
];

export const OperationsHubView: React.FC<OperationsHubViewProps> = ({
  daemonStatus,
  onRefreshDaemon,
  onToggleDaemon,
  onTriggerDaemonCycle,
  onFlushGhostGroups,
  onPollLiveMesh,
  onRunPingSweep,
  onExecuteDeepReset,
  allRooms,
}) => {
  const [targetZone, setTargetZone] = useState<string>("ALL");
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [consoleLogs, setConsoleLogs] = useState<string[]>([
    `[${new Date().toLocaleTimeString()}] Operations Hub initialized. Ready to execute actions.`,
  ]);
  const [confirmDeepReset, setConfirmDeepReset] = useState<boolean>(false);

  const log = (msg: string) => {
    const time = new Date().toLocaleTimeString();
    setConsoleLogs((prev) => [`[${time}] ${msg}`, ...prev]);
  };

  const clearConsole = () => {
    setConsoleLogs([`[${new Date().toLocaleTimeString()}] Console cleared.`]);
  };

  // Compile list of players from allRooms if available, else use fallback
  const playerOptions = React.useMemo(() => {
    if (allRooms && allRooms.length > 0) {
      const extracted: { name: string; ip: string }[] = [];
      for (const room of allRooms) {
        for (const dev of room.devices || []) {
          if (dev.device_role === "SONOS_PLAYER" && dev.ip_address) {
            extracted.push({ name: `${dev.name} (${room.name})`, ip: dev.ip_address });
          }
        }
      }
      if (extracted.length > 0) {
        return extracted;
      }
    }
    return DEFAULT_PLAYERS;
  }, [allRooms]);

  const handleTriggerCycle = async () => {
    setBusyAction("daemon-cycle");
    log("Triggering autonomous 24/7 daemon telemetry cycle...");
    try {
      await onTriggerDaemonCycle();
      log("✓ Daemon collection cycle completed successfully.");
      await onRefreshDaemon();
    } catch (e: unknown) {
      log(`❌ Failed to trigger daemon: ${(e as Error).message}`);
    } finally {
      setBusyAction(null);
    }
  };

  const handleToggle = async () => {
    setBusyAction("daemon-toggle");
    const targetState = daemonStatus?.is_running !== false ? "OFF" : "ON";
    log(`Switching 24/7 Background Daemon to ${targetState}...`);
    try {
      await onToggleDaemon();
      log(`✓ Daemon successfully set to ${targetState}.`);
      await onRefreshDaemon();
    } catch (e: unknown) {
      log(`❌ Failed to toggle daemon: ${(e as Error).message}`);
    } finally {
      setBusyAction(null);
    }
  };

  const handleFlush = async () => {
    setBusyAction("flush-ghost");
    log("Executing 1-Click Ghost Group Flush across all zones...");
    try {
      const res = await onFlushGhostGroups();
      log(
        `✓ Ghost Groups Flushed: ${res.flushed_count} zones sanitized (${
          res.flushed_zones?.length ? res.flushed_zones.join(", ") : "All zones clean"
        }).`
      );
    } catch (e: unknown) {
      log(`❌ Error flushing ghost groups: ${(e as Error).message}`);
    } finally {
      setBusyAction(null);
    }
  };

  const handlePollMesh = async () => {
    setBusyAction("poll-mesh");
    log("Polling live Sonos mesh telemetry across all 14 players on VLAN 10...");
    try {
      const snap = await onPollLiveMesh();
      log(
        `✓ Live Poll Complete: ${snap.players.length} players probed, Root: ${
          snap.designated_stp_root || "OK"
        }.`
      );
    } catch (e: unknown) {
      log(`❌ Error polling Sonos mesh: ${(e as Error).message}`);
    } finally {
      setBusyAction(null);
    }
  };

  const handlePing = async () => {
    setBusyAction("ping-sweep");
    log("Running ICMP latency and jitter sweep across all speakers...");
    try {
      const res = await onRunPingSweep();
      log(
        `✓ Ping Sweep Complete: ${res.reachable_count}/${res.total_probed} reachable, Avg RTT: ${res.avg_rtt_ms.toFixed(
          1
        )}ms, Max RTT: ${res.max_rtt_ms.toFixed(1)}ms.`
      );
    } catch (e: unknown) {
      log(`❌ Error running ping sweep: ${(e as Error).message}`);
    } finally {
      setBusyAction(null);
    }
  };

  const handleDeepReset = async () => {
    const isAll = targetZone === "ALL";
    const zoneIps = isAll ? undefined : [targetZone];
    const targetLabel = isAll
      ? "ALL Household Zones (12 Zones)"
      : playerOptions.find((p) => p.ip === targetZone)?.name ?? targetZone;

    setBusyAction("deep-reset");
    log(`🚨 EXECUTING HARDCORE DEEP RESET on: ${targetLabel}...`);
    try {
      const res = await onExecuteDeepReset(zoneIps);
      log(
        `✓ Deep Reset Finished in ${res.elapsed_ms.toFixed(0)}ms: ${res.success_count}/${
          res.total_targeted
        } zones unhooked and restored.`
      );
      if (res.results && res.results.length > 0) {
        res.results.forEach((r) => {
          log(`   ↳ [${r.status}] ${r.zone_name} (${r.ip_address}): ${r.details}`);
        });
      }
      setConfirmDeepReset(false);
    } catch (e: unknown) {
      log(`❌ Error executing deep reset: ${(e as Error).message}`);
    } finally {
      setBusyAction(null);
    }
  };

  const isRunning = daemonStatus?.is_running !== false;

  return (
    <section
      role="region"
      aria-label="Operations & Unclog Hub"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "20px",
        maxWidth: "960px",
        margin: "0 auto",
      }}
    >
      {/* 24/7 Background Daemon Card */}
      <div
        style={{
          backgroundColor: "#1e293b",
          border: "1px solid #334155",
          borderRadius: "12px",
          padding: "20px",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "12px",
            flexWrap: "wrap",
            gap: "10px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "1.3rem" }}>🤖</span>
            <div>
              <h3 style={{ margin: 0, fontSize: "1.1rem", color: "#f8fafc" }}>
                24/7 Autonomous Telemetry & Auto-Heal Daemon
              </h3>
              <p style={{ margin: "2px 0 0", fontSize: "0.82rem", color: "#94a3b8" }}>
                Continuous 60-second Atheros OFDM ANI, PHY error velocity, and UPnP ghost heal
              </p>
            </div>
          </div>
          <span
            style={{
              backgroundColor: isRunning ? "#064e3b" : "#7f1d1d",
              color: isRunning ? "#6ee7b7" : "#fca5a5",
              border: `1px solid ${isRunning ? "#10b981" : "#ef4444"}`,
              padding: "4px 12px",
              borderRadius: "9999px",
              fontSize: "0.85rem",
              fontWeight: 700,
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <span
              style={{
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                backgroundColor: isRunning ? "#10b981" : "#ef4444",
                display: "inline-block",
              }}
            />
            {isRunning ? "● ACTIVE" : "● PAUSED"}
          </span>
        </div>

        {/* Daemon Metrics Strip */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            gap: "10px",
            marginBottom: "16px",
          }}
        >
          <div
            style={{
              backgroundColor: "#0f172a",
              border: "1px solid #334155",
              borderRadius: "8px",
              padding: "10px 14px",
            }}
          >
            <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>Polling Interval</div>
            <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#38bdf8" }}>
              {daemonStatus?.interval_sec ?? 60}s
            </div>
          </div>
          <div
            style={{
              backgroundColor: "#0f172a",
              border: "1px solid #334155",
              borderRadius: "8px",
              padding: "10px 14px",
            }}
          >
            <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>Cycles Completed</div>
            <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#f8fafc" }}>
              {daemonStatus?.total_cycles ?? 0}
            </div>
          </div>
          <div
            style={{
              backgroundColor: "#0f172a",
              border: "1px solid #334155",
              borderRadius: "8px",
              padding: "10px 14px",
            }}
          >
            <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>Retention History</div>
            <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#a855f7" }}>
              {daemonStatus?.retention_days ?? 365} Days
            </div>
          </div>
          <div
            style={{
              backgroundColor: "#0f172a",
              border: "1px solid #334155",
              borderRadius: "8px",
              padding: "10px 14px",
            }}
          >
            <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>Autonomous Heal</div>
            <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#22c55e" }}>
              Active
            </div>
          </div>
        </div>

        {/* Daemon Controls */}
        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
          <button
            type="button"
            disabled={Boolean(busyAction)}
            onClick={handleTriggerCycle}
            style={{
              backgroundColor: "#0284c7",
              color: "#ffffff",
              border: "none",
              borderRadius: "6px",
              padding: "10px 16px",
              fontWeight: 600,
              cursor: busyAction ? "not-allowed" : "pointer",
              opacity: busyAction ? 0.65 : 1,
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            ⚡ Collect Live Telemetry Now
          </button>
          <button
            type="button"
            disabled={Boolean(busyAction)}
            onClick={handleToggle}
            style={{
              backgroundColor: isRunning ? "#b91c1c" : "#16a34a",
              color: "#ffffff",
              border: "none",
              borderRadius: "6px",
              padding: "10px 16px",
              fontWeight: 600,
              cursor: busyAction ? "not-allowed" : "pointer",
              opacity: busyAction ? 0.65 : 1,
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            {isRunning ? "⏸️ Pause 24/7 Daemon" : "▶️ Resume 24/7 Daemon"}
          </button>
        </div>
      </div>

      {/* Tier 1: Non-Invasive Quick Actions */}
      <div
        style={{
          backgroundColor: "#1e293b",
          border: "1px solid #334155",
          borderRadius: "12px",
          padding: "20px",
        }}
      >
        <div style={{ marginBottom: "12px" }}>
          <h3 style={{ margin: 0, fontSize: "1.1rem", color: "#38bdf8" }}>
            🧹 Tier 1: Non-Invasive Quick Actions (Safe Mid-Stream)
          </h3>
          <p style={{ margin: "4px 0 0", fontSize: "0.85rem", color: "#94a3b8" }}>
            Routine UPnP unhooking and live network sweeps that run safely without stopping active music playback.
          </p>
        </div>
        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
          <button
            type="button"
            disabled={Boolean(busyAction)}
            onClick={handleFlush}
            style={{
              backgroundColor: "#065f46",
              color: "#34d399",
              border: "1px solid #059669",
              borderRadius: "6px",
              padding: "10px 16px",
              fontWeight: 600,
              cursor: busyAction ? "not-allowed" : "pointer",
              opacity: busyAction ? 0.65 : 1,
            }}
          >
            🧹 1-Click Flush Ghost Groups
          </button>
          <button
            type="button"
            disabled={Boolean(busyAction)}
            onClick={handlePollMesh}
            style={{
              backgroundColor: "#1e3a8a",
              color: "#93c5fd",
              border: "1px solid #2563eb",
              borderRadius: "6px",
              padding: "10px 16px",
              fontWeight: 600,
              cursor: busyAction ? "not-allowed" : "pointer",
              opacity: busyAction ? 0.65 : 1,
            }}
          >
            📊 Poll Live Sonos Mesh
          </button>
          <button
            type="button"
            disabled={Boolean(busyAction)}
            onClick={handlePing}
            style={{
              backgroundColor: "#4c1d95",
              color: "#c4b5fd",
              border: "1px solid #7c3aed",
              borderRadius: "6px",
              padding: "10px 16px",
              fontWeight: 600,
              cursor: busyAction ? "not-allowed" : "pointer",
              opacity: busyAction ? 0.65 : 1,
            }}
          >
            📶 ICMP Latency Sweep
          </button>
        </div>
      </div>

      {/* Tier 3: Hardcore Deep Remediation */}
      <div
        style={{
          backgroundColor: "#1e293b",
          border: "2px solid #b91c1c",
          borderRadius: "12px",
          padding: "20px",
          boxShadow: "0 0 16px rgba(185, 28, 28, 0.2)",
        }}
      >
        <div style={{ marginBottom: "14px" }}>
          <h3 style={{ margin: 0, fontSize: "1.1rem", color: "#f87171" }}>
            🚨 Tier 3: Hardcore Deep Reset & Unfreeze
          </h3>
          <p style={{ margin: "4px 0 0", fontSize: "0.85rem", color: "#fca5a5", lineHeight: "1.4" }}>
            For unresponsive, stuck, or frozen speakers. Forcibly terminates hung playback threads (
            <code>AVTransport:Stop</code>), purges corrupted queue buffers (<code>RemoveAllTracksFromQueue</code>),
            restores standalone coordinator status, and forces UPnP re-announcement.
          </p>
        </div>

        <div style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
          <label style={{ fontSize: "0.85rem", color: "#cbd5e1" }}>
            Target Zone:
            <select
              value={targetZone}
              onChange={(e) => {
                setTargetZone(e.target.value);
                setConfirmDeepReset(false);
              }}
              style={{
                marginLeft: "8px",
                padding: "8px 12px",
                background: "#0f172a",
                color: "#f8fafc",
                border: "1px solid #475569",
                borderRadius: "6px",
                fontSize: "0.9rem",
              }}
            >
              <option value="ALL">🚨 ALL Household Zones (12 Zones)</option>
              {playerOptions.map((p) => (
                <option key={p.ip} value={p.ip}>
                  {p.name} ({p.ip})
                </option>
              ))}
            </select>
          </label>

          {!confirmDeepReset ? (
            <button
              type="button"
              disabled={Boolean(busyAction)}
              onClick={() => setConfirmDeepReset(true)}
              style={{
                backgroundColor: "#dc2626",
                color: "#ffffff",
                border: "none",
                borderRadius: "6px",
                padding: "9px 18px",
                fontWeight: 700,
                cursor: busyAction ? "not-allowed" : "pointer",
                opacity: busyAction ? 0.65 : 1,
                boxShadow: "0 0 10px rgba(220, 38, 38, 0.4)",
              }}
            >
              🚨 Execute Hardcore Reset
            </button>
          ) : (
            <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
              <button
                type="button"
                disabled={Boolean(busyAction)}
                onClick={handleDeepReset}
                style={{
                  backgroundColor: "#991b1b",
                  color: "#ffffff",
                  border: "2px solid #ef4444",
                  borderRadius: "6px",
                  padding: "9px 18px",
                  fontWeight: 700,
                  cursor: busyAction ? "not-allowed" : "pointer",
                  animation: "pulse 1.5s infinite",
                }}
              >
                ⚠️ Confirm Reset ({targetZone === "ALL" ? "All Zones" : targetZone})
              </button>
              <button
                type="button"
                onClick={() => setConfirmDeepReset(false)}
                style={{
                  backgroundColor: "#334155",
                  color: "#f8fafc",
                  border: "none",
                  borderRadius: "6px",
                  padding: "9px 14px",
                  fontSize: "0.85rem",
                  cursor: "pointer",
                }}
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Action Output Console */}
      <div
        style={{
          backgroundColor: "#1e293b",
          border: "1px solid #334155",
          borderRadius: "12px",
          padding: "16px 20px",
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
          <h4 style={{ margin: 0, fontSize: "0.95rem", color: "#38bdf8" }}>
            📟 Real-Time Action Console &amp; Logs
          </h4>
          <button
            type="button"
            onClick={clearConsole}
            style={{
              backgroundColor: "#334155",
              color: "#cbd5e1",
              border: "none",
              borderRadius: "4px",
              padding: "4px 10px",
              fontSize: "0.75rem",
              cursor: "pointer",
            }}
          >
            Clear Console
          </button>
        </div>
        <div
          tabIndex={0}
          aria-label="Action console log entries"
          style={{
            backgroundColor: "#090d16",
            border: "1px solid #1e293b",
            borderRadius: "6px",
            padding: "12px",
            fontFamily: "monospace",
            fontSize: "0.85rem",
            color: "#38bdf8",
            maxHeight: "220px",
            overflowY: "auto",
            display: "flex",
            flexDirection: "column",
            gap: "4px",
          }}
        >
          {consoleLogs.map((logLine, idx) => (
            <div
              key={idx}
              style={{
                color: logLine.includes("❌")
                  ? "#f87171"
                  : logLine.includes("🚨") || logLine.includes("⚠️")
                  ? "#fca5a5"
                  : logLine.includes("✓")
                  ? "#4ade80"
                  : "#94a3b8",
                whiteSpace: "pre-wrap",
              }}
            >
              {logLine}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
