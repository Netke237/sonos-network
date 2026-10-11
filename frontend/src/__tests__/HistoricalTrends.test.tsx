import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import App from "../App";

const mockOverview = {
  total_floors: 4,
  total_rooms: 11,
  total_sonos_players: 14,
  total_wifi_aps: 2,
  total_switch_ports: 10,
  designated_stp_root: "9000.542a1b63fe6e (Wohnzimmer_Bookshelf 192.168.10.230)",
  active_diagnostics_count: 1,
  critical_diagnostics_count: 0,
  floors: [
    {
      id: "fl-dg",
      slug: "dachgeschoss",
      name: "Dachgeschoss",
      level_order: 3,
      is_archived: false,
      rooms: [
        {
          id: "rm-nicolas",
          slug: "nicolas",
          name: "Nicolas",
          floor_id: "fl-dg",
          pos_x: 500,
          pos_y: 80,
          health_grade: "GOOD",
          best_5ghz_rssi_dbm: -72,
          best_24ghz_rssi_dbm: -82,
          best_5ghz_dbm: -72,
          best_24ghz_dbm: -82,
          best_ap_name: "Galerie EAP650",
          link_speed_mbps: 1201,
          rogue_count: 0,
          neighbor_count: 0,
          wifi_health_grade: "GOOD",
          sonos_health_grade: "GOOD",
          wired_health_grade: "GOOD",
          active_diagnostics_count: 0,
          top_diagnostic_title: null,
          description: "Attic bedroom",
          is_archived: false,
          devices: [
            {
              id: "dev-nicolas",
              slug: "sonos-nicolas",
              name: "Nicolas",
              device_role: "SONOS_PLAYER",
              model_name: "SYMFONISK Bookshelf",
              ip_address: "192.168.10.165",
              connection_mode: "STATION_MODE",
              health_grade: "GOOD",
              ofdm_ani_level: 0,
              phy_error_rate: 0.0,
              stp_path_cost: 0,
              ping_rtt_ms: 2.3,
              room_id: "rm-nicolas",
              is_archived: false,
            },
          ],
          switch_ports: [],
        },
      ],
    },
  ],
};

const mockHistoryResponse = {
  room_id: "rm-nicolas",
  room_slug: "nicolas",
  room_name: "Nicolas",
  time_range: "24h",
  total_samples: 2,
  peak_ani: 2,
  avg_phy_error_rate: 1.5,
  avg_ping_rtt_ms: 2.4,
  summary:
    "Captured 2 snapshot(s) for Nicolas over 24h. Peak OFDM ANI: 2, Avg PHY Error Rate: 1.5 err/s, Avg Ping RTT: 2.4 ms.",
  samples: [
    {
      timestamp: "2026-10-11T14:00:00Z",
      batch_id: "batch-1",
      consumer_id: "background-60s",
      peak_ofdm_ani_level: 1,
      total_phy_error_rate: 1.0,
      avg_ping_rtt_ms: 2.2,
      best_5ghz_dbm: -72,
      best_24ghz_dbm: -82,
      link_speed_mbps: 1201,
      worst_stp_path_cost: 0,
      health_grade: "GOOD",
      players: [
        {
          rincon_uuid: "RINCON_NICOLAS",
          zone_name: "Nicolas",
          connection_mode: "STATION_MODE",
          ofdm_ani_level: 1,
          phy_error_rate: 1.0,
          ping_rtt_ms: 2.2,
        },
      ],
    },
    {
      timestamp: "2026-10-11T14:30:00Z",
      batch_id: "batch-2",
      consumer_id: "background-60s",
      peak_ofdm_ani_level: 2,
      total_phy_error_rate: 2.0,
      avg_ping_rtt_ms: 2.6,
      best_5ghz_dbm: -72,
      best_24ghz_dbm: -82,
      link_speed_mbps: 1201,
      worst_stp_path_cost: 0,
      health_grade: "GOOD",
      players: [
        {
          rincon_uuid: "RINCON_NICOLAS",
          zone_name: "Nicolas",
          connection_mode: "STATION_MODE",
          ofdm_ani_level: 2,
          phy_error_rate: 2.0,
          ping_rtt_ms: 2.6,
        },
      ],
    },
  ],
};

const mockDaemonStatus = {
  is_running: true,
  interval_sec: 60.0,
  retention_days: 7,
  last_cycle_at: "2026-10-11T14:30:00Z",
  total_cycles: 42,
  last_error: null,
};

const mockCollectResult = {
  status: "ok",
  batch_id: "batch-new-3",
  total_players: 14,
  pruned_count: 5,
  executed_at: "2026-10-11T14:35:00Z",
};

describe("T7 Room Historical Trends & 24/7 Daemon UI", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    global.fetch = vi.fn().mockImplementation((url: string | URL | Request) => {
      const urlStr = String(url);
      if (urlStr.includes("/api/overview")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockOverview),
        });
      }
      if (urlStr.includes("/api/daemon/status")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockDaemonStatus),
        });
      }
      if (urlStr.includes("/api/daemon/collect-now")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockCollectResult),
        });
      }
      if (urlStr.includes("/api/rooms/nicolas/history")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockHistoryResponse),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      });
    });
  });

  it("renders room Historical Trends button, opens the drawer, shows metrics, toggles range, and triggers daemon collection", async () => {
    render(<App />);

    // Wait for overview load
    await waitFor(() => {
      expect(screen.getAllByText("Nicolas").length).toBeGreaterThan(0);
    });

    // Check daemon badge in header
    expect(screen.getByText(/24\/7 Daemon: 60s/i)).toBeInTheDocument();

    // Trigger daemon collection from header
    const daemonBtn = screen.getByRole("button", {
      name: /Run 24\/7 Daemon Cycle/i,
    });
    fireEvent.click(daemonBtn);

    await waitFor(() => {
      expect(
        screen.getByText(
          /24\/7 Telemetry Cycle Executed: Snapshot batch-new-3 \(14 players, 5 pruned\)/i
        )
      ).toBeInTheDocument();
    });

    // Click "Historical Trends" button on room Nicolas
    const trendsBtns = screen.getAllByRole("button", { name: "Historical Trends" });
    fireEvent.click(trendsBtns[0]);

    // Verify Historical Trends Drawer appears
    await waitFor(() => {
      expect(
        screen.getByRole("region", { name: "Room Historical Trends Drawer" })
      ).toBeInTheDocument();
    });

    expect(
      screen.getByText("Room Historical Trends: Nicolas")
    ).toBeInTheDocument();
    expect(screen.getAllByText("ANI 2").length).toBeGreaterThan(0);
    expect(screen.getByText("1.5 err/s")).toBeInTheDocument();
    expect(screen.getByText("2.4 ms")).toBeInTheDocument();
    expect(screen.getByText(/Captured 2 snapshot\(s\) for Nicolas over 24h/i)).toBeInTheDocument();

    // Change range to 7d
    const range7dBtn = screen.getByRole("button", { name: "7d" });
    fireEvent.click(range7dBtn);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("range=7d")
      );
    });
  });
});
