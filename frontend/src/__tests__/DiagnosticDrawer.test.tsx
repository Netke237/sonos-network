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
  active_diagnostics_count: 3,
  critical_diagnostics_count: 2,
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
          health_grade: "MARGINAL",
          best_5ghz_rssi_dbm: -72,
          best_24ghz_rssi_dbm: -82,
          best_5ghz_dbm: -72,
          best_24ghz_dbm: -82,
          best_ap_name: "Galerie EAP650",
          link_speed_mbps: 1201,
          rogue_count: 0,
          neighbor_count: 0,
          wifi_health_grade: "MARGINAL",
          sonos_health_grade: "EXCELLENT",
          wired_health_grade: "EXCELLENT",
          active_diagnostics_count: 1,
          top_diagnostic_title: "Weak 5 GHz Wi-Fi Coverage in Nicolas (-72 dBm on Galerie EAP650)",
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
              phy_error_rate: 0.0,
              stp_path_cost: 0,
              ping_rtt_ms: 2.3,
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
          health_grade: "CRITICAL",
          best_5ghz_rssi_dbm: -54,
          best_24ghz_rssi_dbm: -52,
          best_5ghz_dbm: -54,
          best_24ghz_dbm: -52,
          best_ap_name: "Galerie EAP650",
          link_speed_mbps: 1201,
          wifi_health_grade: "EXCELLENT",
          sonos_health_grade: "CRITICAL",
          wired_health_grade: "EXCELLENT",
          active_diagnostics_count: 2,
          top_diagnostic_title:
            "Severe Non-Wi-Fi 2.4 GHz EMI Spike in Wohnzimmer (ANI 9, 1126.0 err/s)",
          description: "Ground-floor living room",
          is_archived: false,
          devices: [],
          switch_ports: [],
        },
      ],
    },
  ],
};

const mockNicolasRoomDiagnostics = {
  room_id: "rm-nicolas",
  room_slug: "nicolas",
  room_name: "Nicolas",
  floor_slug: "dachgeschoss",
  floor_name: "Dachgeschoss",
  health_grade: "MARGINAL",
  active_diagnostics_count: 2,
  critical_count: 1,
  marginal_count: 1,
  top_diagnostic_title: "Weak 5 GHz Wi-Fi Coverage in Nicolas (-72 dBm on Galerie EAP650)",
  wifi_pillar: {
    health_grade: "MARGINAL",
    best_5ghz_dbm: -72,
    best_24ghz_dbm: -82,
    covering_ap_name: "Galerie EAP650",
    covering_ap_slug: "galerie-ap",
    link_speed_mbps: 1201,
    rogue_count: 0,
    neighbor_count: 0,
    co_channel_neighbors: [],
    has_channel_6_high_power_wifi: false,
    summary_note: "5 GHz: -72 dBm (MARGINAL) via Galerie EAP650",
  },
  sonos_pillar: {
    health_grade: "EXCELLENT",
    total_players: 1,
    sonosnet_player_count: 0,
    station_mode_player_count: 1,
    ht_satellite_player_count: 0,
    wired_player_count: 0,
    designated_stp_root: "9000.542a1b63fe6e (Wohnzimmer_Bookshelf 192.168.10.230)",
    is_stp_root_healthy: true,
    max_phy_error_rate: 0.0,
    max_stp_path_cost: 0,
    ghost_group_zones: [],
    summary_note: "1 player(s) in room — worst grade EXCELLENT",
    players: [
      {
        rincon_uuid: "RINCON_347E5C36DE9001400",
        zone_name: "Nicolas",
        ip_address: "192.168.10.165",
        connection_mode: "STATION_MODE",
        ofdm_ani_level: 0,
        noise_floor_dbm: -102,
        phy_error_rate: 0.0,
        designated_root: "9000.542a1b63fe6e",
        stp_path_cost: 0,
        active_forwarding_snr_db: null,
        ping_rtt_ms: 2.3,
        group_id: "RINCON_347E5C36DE9001400:1",
        is_ghost_group: false,
        rf_grade: "EXCELLENT",
        link_grade: "EXCELLENT",
        overall_grade: "EXCELLENT",
        grading_rationale:
          "5 GHz STATION_MODE client (RSSI -72 dBm, ANI 0, 0.0 PHY err/s, RTT 2.3 ms)",
      },
    ],
  },
  wired_pillar: {
    health_grade: "EXCELLENT",
    has_vlan10_wall_jack: true,
    port_numbers: [5],
    pvid_list: [10],
    bpdu_policy: "PASS_THROUGH",
    stp_root_guard_required: true,
    stp_guard_note:
      "Wall jack Port 5 (Untagged VLAN 10) available on Netgear GS316EP. MANDATORY F-03 STP GUARD: Disable Wi-Fi/SonosNet on any secondary wired speaker so lower-MAC speakers never usurp Wohnzimmer_Bookshelf (9000.542a1b63fe6e) as STP Root.",
  },
  diagnostics: [
    {
      id: "diag-nicolas-wifi-weak-coverage",
      room_slug: "nicolas",
      room_name: "Nicolas",
      layer: "WIFI",
      severity: "MARGINAL",
      rule_code: "WIFI_WEAK_COVERAGE",
      title: "Weak 5 GHz Wi-Fi Coverage in Nicolas (-72 dBm on Galerie EAP650)",
      summary:
        "Strongest managed 5 GHz BSSID in Nicolas is -72 dBm (< -70 dBm threshold) via Galerie EAP650.",
      evidence: { best_5ghz_dbm: -72, has_vlan10_wall_jack: true },
      affected_devices: ["Nicolas"],
      solution_proposals: [],
    },
    {
      id: "diag-nicolas-ghost-group",
      room_slug: "nicolas",
      room_name: "Nicolas",
      layer: "SONOS",
      severity: "CRITICAL",
      rule_code: "GHOST_GROUP_MISMATCH",
      title: "Orphaned Sonos S2 Ghost Group ID on Nicolas",
      summary: "Nicolas bound to departed Coordinator UUID.",
      evidence: {},
      affected_devices: ["Nicolas"],
      solution_proposals: [],
    },
  ],
  solution_proposals: [
    {
      id: "prop-nicolas-wifi-weak-1",
      rank: 1,
      rule_code: "WIFI_WEAK_COVERAGE",
      title: "Use Wired Wall Jack (Port 5, Untagged VLAN 10) with F-03 STP Root Guard",
      description:
        "Room Nicolas has Port 5 patched to Netgear GS316EP on Untagged VLAN 10. You MUST disable its Wi-Fi/SonosNet radio so it does not usurp DesignatedRoot (9000.542a1b63fe6e).",
      action_type: "GUIDED_PHYSICAL",
      requires_sonosnet_disable_guard: true,
      stp_guard_warning:
        "MANDATORY F-03 STP ROOT USURPATION GUARD: Disable Wi-Fi/SonosNet on secondary wired speaker (or set switch STP priority to 4096) so 9000.542a1b63fe6e remains STP Root.",
      target_room_slug: "nicolas",
    },
    {
      id: "prop-nicolas-ghost-1",
      rank: 2,
      rule_code: "GHOST_GROUP_MISMATCH",
      title: "1-Click Flush Ghost Groups Across All Zones",
      description: "Execute UPnP BecomeCoordinatorOfStandaloneGroup.",
      action_type: "ONE_CLICK",
      one_click_action: "FLUSH_GHOST_GROUPS",
      requires_sonosnet_disable_guard: false,
      target_room_slug: "nicolas",
    },
    {
      id: "prop-nicolas-ping-1",
      rank: 3,
      rule_code: "WIFI_WEAK_COVERAGE",
      title: "Run Room Ping/Jitter Sweep",
      description: "Measure ICMP/HTTP latency and jitter across all 14 players.",
      action_type: "ONE_CLICK",
      one_click_action: "RUN_PING_JITTER_SWEEP",
      requires_sonosnet_disable_guard: false,
      target_room_slug: "nicolas",
    },
  ],
};

describe("T5 Room 3-Pillar Diagnostic Drawer & Ranked SolutionProposal Slice", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        const method = init?.method ?? "GET";
        if (url.includes("/api/overview") && method === "GET") {
          return new Response(JSON.stringify(mockOverview), { status: 200 });
        }
        if (url.includes("/api/rooms/nicolas/diagnostics") && method === "GET") {
          return new Response(JSON.stringify(mockNicolasRoomDiagnostics), {
            status: 200,
          });
        }
        if (url.endsWith("/api/actions/ping-sweep") && method === "POST") {
          return new Response(
            JSON.stringify({
              swept_at: "2026-10-11T14:00:00Z",
              total_probed: 14,
              reachable_count: 14,
              max_rtt_ms: 8.9,
              avg_rtt_ms: 4.1,
              dpc_risk_zones: [],
              results: [],
            }),
            { status: 200 }
          );
        }
        if (url.endsWith("/api/actions/flush-ghost-groups") && method === "POST") {
          return new Response(
            JSON.stringify({
              flushed_count: 1,
              flushed_zones: ["Nicolas"],
              results: [],
              captured_at: "2026-10-11T14:00:05Z",
            }),
            { status: 200 }
          );
        }
        return new Response(JSON.stringify([]), { status: 200 });
      })
    );
  });

  it("renders room diagnostic badges, opens the Room 3-Pillar Diagnostic Drawer, shows all 3 pillars + F-03 STP Root Guard warning, and executes 1-click SolutionProposal actions", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText("Nicolas").length).toBeGreaterThan(0);
    });

    // Verify top diagnostic title is visible on the room card
    expect(
      screen.getByText(
        /Severe Non-Wi-Fi 2\.4 GHz EMI Spike in Wohnzimmer/i
      )
    ).toBeInTheDocument();

    // Click "Diagnose Room / 3-Pillar Analysis" on Nicolas room card
    const diagnoseBtns = screen.getAllByRole("button", {
      name: /Diagnose Room \/ 3-Pillar Analysis/i,
    });
    expect(diagnoseBtns.length).toBeGreaterThan(0);
    fireEvent.click(diagnoseBtns[0]);

    // Verify GET /api/rooms/nicolas/diagnostics was called and 3-Pillar Diagnostic Drawer opened
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/rooms/nicolas/diagnostics")
      );
    });

    const drawer = await screen.findByRole("region", {
      name: /Room 3-Pillar Diagnostic Drawer/i,
    });
    expect(drawer).toBeInTheDocument();

    // Verify Pillar 1 (Wi-Fi Situation), Pillar 2 (Sonos Situation), and Pillar 3 (Wired / Switch VLAN Situation)
    expect(screen.getByText(/Pillar 1 — Wi-Fi Situation/i)).toBeInTheDocument();
    expect(screen.getByText(/Pillar 2 — Sonos Situation/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Pillar 3 — Wired \/ Switch VLAN Situation/i)
    ).toBeInTheDocument();

    // Verify ConnectionMode-scoped rationale & F-03 STP Root Usurpation Guard warning
    expect(
      screen.getByText(/5 GHz STATION_MODE client/i)
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/MANDATORY F-03 STP ROOT USURPATION GUARD/i).length
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/9000\.542a1b63fe6e/i).length
    ).toBeGreaterThan(0);

    // Verify active RoomDiagnostic rule codes & Ranked SolutionProposals
    expect(screen.getAllByText(/WIFI_WEAK_COVERAGE/i).length).toBeGreaterThan(0);
    expect(
      screen.getByText(
        /Use Wired Wall Jack \(Port 5, Untagged VLAN 10\) with F-03 STP Root Guard/i
      )
    ).toBeInTheDocument();

    // Click 1-click "Run Room Ping/Jitter Sweep" proposal action button inside drawer
    const pingBtn = screen.getByRole("button", {
      name: /Execute: Run Room Ping\/Jitter Sweep/i,
    });
    fireEvent.click(pingBtn);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/actions/ping-sweep"),
        expect.objectContaining({ method: "POST" })
      );
    });

    // Click 1-click "1-Click Flush Ghost Groups Across All Zones" proposal action button
    const flushProposalBtn = screen.getByRole("button", {
      name: /Execute: 1-Click Flush Ghost Groups Across All Zones/i,
    });
    fireEvent.click(flushProposalBtn);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/actions/flush-ghost-groups"),
        expect.objectContaining({ method: "POST" })
      );
    });
  });
});
