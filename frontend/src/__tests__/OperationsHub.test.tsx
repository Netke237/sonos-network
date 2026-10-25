import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import App from "../App";

const mockOverview = {
  total_floors: 1,
  total_rooms: 1,
  total_sonos_players: 1,
  total_wifi_aps: 1,
  total_switch_ports: 1,
  designated_stp_root: "9000.542a1b63fe6e (Wohnzimmer_Bookshelf 192.168.10.230)",
  active_diagnostics_count: 0,
  critical_diagnostics_count: 0,
  floors: [
    {
      id: "fl-og",
      slug: "obergeschoss",
      name: "Obergeschoss",
      level_order: 1,
      is_archived: false,
      rooms: [
        {
          id: "rm-nicolas",
          slug: "nicolas",
          name: "Nicolas",
          floor_id: "fl-og",
          pos_x: 100,
          pos_y: 100,
          health_grade: "GOOD",
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

const mockDaemonStatus = {
  is_running: true,
  interval_sec: 60,
  retention_days: 365,
  total_cycles: 463,
  last_cycle_at: "2026-10-15T15:30:00Z",
};

describe("Operations & Unclog Hub Tab", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/api/overview")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockOverview),
        });
      }
      if (url.includes("/api/daemon/status")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockDaemonStatus),
        });
      }
      if (url.includes("/api/actions/ghost-flush")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              flushed_count: 1,
              flushed_zones: ["Nicolas"],
              results: [
                {
                  zone_name: "Nicolas",
                  rincon_uuid: "RINCON_001",
                  ip_address: "192.168.10.165",
                  new_group_id: "RINCON_001:0",
                  status: "FLUSHED",
                },
              ],
              captured_at: new Date().toISOString(),
            }),
        });
      }
      if (url.includes("/api/actions/deep-reset")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              total_targeted: 1,
              success_count: 1,
              reset_zones: ["Nicolas"],
              failed_zones: [],
              results: [
                {
                  zone_name: "Nicolas",
                  ip_address: "192.168.10.165",
                  rincon_uuid: "RINCON_001",
                  stopped: true,
                  queue_cleared: true,
                  coordinator_reset: true,
                  status: "RESET_OK",
                  details: "Stopped playback, cleared AVTransport queue, reset group coordinator.",
                },
              ],
              elapsed_ms: 120,
              captured_at: new Date().toISOString(),
            }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      });
    });
  });

  it("switches to the Operations Hub tab and displays 24/7 daemon and remediation controls", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("⚡ Operations & Unclog Hub")).toBeInTheDocument();
    });

    // Click tab
    fireEvent.click(screen.getByText("⚡ Operations & Unclog Hub"));

    // Check daemon status card
    await waitFor(() => {
      expect(
        screen.getByText(/24\/7 Autonomous Telemetry & Auto-Heal Daemon/i)
      ).toBeInTheDocument();
      expect(screen.getByText("463")).toBeInTheDocument();
    });

    // Check non-invasive actions
    expect(screen.getByText(/1-Click Flush Ghost Groups/i)).toBeInTheDocument();
    expect(screen.getByText(/Poll Live Sonos Mesh/i)).toBeInTheDocument();
    expect(screen.getByText(/ICMP Latency Sweep/i)).toBeInTheDocument();

    // Check hardcore deep reset card
    expect(screen.getByText(/Hardcore Deep Reset & Unfreeze/i)).toBeInTheDocument();
    expect(screen.getByText(/Target Zone:/i)).toBeInTheDocument();
    expect(screen.getByText(/Execute Hardcore Reset/i)).toBeInTheDocument();
  });
});
