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
          health_grade: "EXCELLENT",
          best_5ghz_rssi_dbm: -72,
          best_24ghz_rssi_dbm: -82,
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
              health_grade: "EXCELLENT",
              ofdm_ani_level: 0,
              room_id: "rm-nicolas",
              is_archived: false,
            },
          ],
          switch_ports: [
            {
              id: "sp-5",
              port_number: 5,
              switch_name: "Netgear GS316EP",
              switch_ip: "192.168.55.155",
              pvid: 10,
              untagged_vlans: "10",
              tagged_vlans: "",
              bpdu_policy: "PASS_THROUGH",
              loop_detection_disabled: true,
              patched_room_id: "rm-nicolas",
              connected_device_label: "Nicolas Wall Jack (VLAN 10)",
              is_archived: false,
            },
          ],
        },
      ],
    },
    {
      id: "fl-eg",
      slug: "erdgeschoss",
      name: "Erdgeschoss",
      level_order: 1,
      is_archived: false,
      rooms: [
        {
          id: "rm-wz",
          slug: "wohnzimmer",
          name: "Wohnzimmer",
          floor_id: "fl-eg",
          pos_x: 150,
          pos_y: 450,
          health_grade: "MARGINAL",
          best_5ghz_rssi_dbm: -54,
          best_24ghz_rssi_dbm: -52,
          description: "Ground-floor living room",
          is_archived: false,
          devices: [
            {
              id: "dev-wz-root",
              slug: "sonos-wohnzimmer-bookshelf",
              name: "Wohnzimmer_Bookshelf",
              device_role: "SONOS_PLAYER",
              model_name: "SYMFONISK Bookshelf",
              ip_address: "192.168.10.230",
              connection_mode: "ETHERNET_ROOT",
              health_grade: "EXCELLENT",
              ofdm_ani_level: 6,
              noise_floor_dbm: -111,
              phy_error_rate: 12.5,
              stp_path_cost: 0,
              master_volume: 18,
              is_ghost_group: false,
              room_id: "rm-wz",
              is_archived: false,
            },
            {
              id: "dev-wz-esstisch",
              slug: "sonos-wohnzimmer-esstisch",
              name: "Wohnzimmer_Esstisch",
              device_role: "SONOS_PLAYER",
              model_name: "Sonos Play:1",
              ip_address: "192.168.10.160",
              connection_mode: "SONOSNET_MODE",
              health_grade: "CRITICAL",
              ofdm_ani_level: 9,
              noise_floor_dbm: -110,
              phy_error_rate: 789.0,
              stp_path_cost: 200,
              master_volume: 15,
              group_id: "RINCON_347E5C3828B001400:77",
              is_ghost_group: true,
              room_id: "rm-wz",
              is_archived: false,
            },
            {
              id: "dev-beam",
              slug: "sonos-fernsehecke-beam",
              name: "Fernsehecke (LF,RF)",
              device_role: "SONOS_PLAYER",
              model_name: "Sonos Beam",
              ip_address: "192.168.10.241",
              connection_mode: "SONOSNET_MODE",
              health_grade: "EXCELLENT",
              ofdm_ani_level: null,
              noise_floor_dbm: null,
              phy_error_rate: 0.0,
              stp_path_cost: 200,
              master_volume: 28,
              is_ghost_group: false,
              room_id: "rm-wz",
              is_archived: false,
            },
          ],
          switch_ports: [
            {
              id: "sp-13",
              port_number: 13,
              switch_name: "Netgear GS316EP",
              switch_ip: "192.168.55.155",
              pvid: 10,
              untagged_vlans: "10",
              tagged_vlans: "",
              bpdu_policy: "PASS_THROUGH",
              loop_detection_disabled: true,
              patched_room_id: "rm-wz",
              connected_device_label: "Wohnzimmer_Bookshelf (Wired STP Root Bridge)",
              is_archived: false,
            },
          ],
        },
      ],
    },
  ],
  ghost_group_count: 1,
  has_ghost_groups: true,
  ghost_group_zones: ["Wohnzimmer_Esstisch"],
};

describe("T1 & T2 Floor-by-Floor Room Matrix, Sonos Telemetry & Ghost Group Actions", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        const method = init?.method ?? "GET";
        if (url.endsWith("/api/overview") && method === "GET") {
          return new Response(JSON.stringify(mockOverview), { status: 200 });
        }
        if (url.endsWith("/api/actions/poll-now") && method === "POST") {
          return new Response(
            JSON.stringify({
              batch_id: "live-poll-1",
              captured_at: "2026-10-11T12:00:00Z",
              consumer_id: "on-demand",
              designated_stp_root: "9000.542a1b63fe6e (Wohnzimmer_Bookshelf 192.168.10.230)",
              is_root_healthy: true,
              total_players: 14,
              reachable_players: 14,
              ghost_group_count: 1,
              has_ghost_groups: true,
              ghost_group_zones: ["Wohnzimmer_Esstisch"],
              players: [],
              mesh_links: [],
            }),
            { status: 200 }
          );
        }
        if (url.endsWith("/api/actions/flush-ghost-groups") && method === "POST") {
          return new Response(
            JSON.stringify({
              flushed_count: 1,
              flushed_zones: ["Wohnzimmer_Esstisch"],
              results: [
                {
                  zone_name: "Wohnzimmer_Esstisch",
                  rincon_uuid: "RINCON_B8E937E6098401400",
                  ip_address: "192.168.10.160",
                  previous_group_id: "RINCON_347E5C3828B001400:77",
                  new_group_id: "RINCON_B8E937E6098401400:88",
                  status: "SANITIZED",
                },
              ],
              captured_at: "2026-10-11T12:00:05Z",
            }),
            { status: 200 }
          );
        }
        if (url.endsWith("/api/rooms") && method === "POST") {
          const body = JSON.parse(String(init?.body));
          return new Response(
            JSON.stringify({
              id: "rm-new",
              slug: "terrasse",
              is_archived: false,
              ...body,
            }),
            { status: 201 }
          );
        }
        if (url.endsWith("/api/devices") && method === "POST") {
          const body = JSON.parse(String(init?.body));
          return new Response(
            JSON.stringify({
              id: "dev-new",
              slug: "sonos-move",
              is_archived: false,
              ...body,
            }),
            { status: 201 }
          );
        }
        if (method === "DELETE") {
          return new Response(JSON.stringify({ is_archived: true }), { status: 200 });
        }
        return new Response(JSON.stringify({}), { status: 200 });
      })
    );
  });

  it("renders the Floor-by-Floor Room Matrix with STP Root badge, room health grades, and switch ports", async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getAllByText(/Wohnzimmer_Bookshelf/i).length).toBeGreaterThan(0);
    });
    expect(screen.getByText("Dachgeschoss")).toBeInTheDocument();
    expect(screen.getByText("Erdgeschoss")).toBeInTheDocument();
    expect(screen.getByText("Wohnzimmer")).toBeInTheDocument();
    expect(screen.getByText(/Port 13/i)).toBeInTheDocument();
    expect(screen.getByText(/Port 5/i)).toBeInTheDocument();
    expect(screen.getByText(/ETHERNET_ROOT/i)).toBeInTheDocument();
  });

  it("renders Sonos player telemetry (OfdmAniLevel or N/A, NoiseFloorDbm or N/A, PhyErrorRate, StpPathCost, MasterVolume, GhostGroup) and triggers Poll Now & Flush Ghost Groups", async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getAllByText(/Wohnzimmer_Esstisch/i).length).toBeGreaterThan(0);
    });

    // Verify F-02 N/A normalization on Beam alongside numeric telemetry on Wohnzimmer players
    expect(screen.getAllByText(/ANI N\/A/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Noise N\/A/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/-110 dBm/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/789\.0 err\/s/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/STP Cost 200/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Vol 15%/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/GHOST GROUP/i).length).toBeGreaterThan(0);

    // Trigger Poll Live Sonos Now
    const pollBtn = screen.getByRole("button", { name: /Poll Live Sonos Now/i });
    fireEvent.click(pollBtn);
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/actions/poll-now"),
        expect.objectContaining({ method: "POST" })
      );
    });

    // Trigger Flush Ghost Groups
    const flushBtn = screen.getByRole("button", { name: /Flush Ghost Groups/i });
    fireEvent.click(flushBtn);
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/actions/flush-ghost-groups"),
        expect.objectContaining({ method: "POST" })
      );
    });
    expect(await screen.findByText(/Flushed 1 Ghost Group/i)).toBeInTheDocument();
  });

  it("opens the Room & Device Manager CRUD modal and creates a new Room and NetworkDevice", async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText("Wohnzimmer")).toBeInTheDocument();
    });

    const openCrudBtn = screen.getByRole("button", { name: /Manage Inventory|Add Room \/ Device/i });
    fireEvent.click(openCrudBtn);

    const roomNameInput = screen.getByLabelText(/Room Name/i);
    fireEvent.change(roomNameInput, { target: { value: "Terrasse" } });

    const createRoomBtn = screen.getByRole("button", { name: /Save Room/i });
    fireEvent.click(createRoomBtn);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/rooms"),
        expect.objectContaining({ method: "POST" })
      );
    });
  });
});

