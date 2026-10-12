import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { PlainLanguageAdvisorModal } from "../components/PlainLanguageAdvisorModal";
import type { RoomMatrixItem } from "../types/topology";

// Mock the API calls
vi.mock("../api/topologyApi", () => ({
  fetchRoomDiagnostics: vi.fn().mockResolvedValue({
    room_id: "room-noemi",
    room_slug: "noemi",
    room_name: "Noemi",
    health_grade: "CRITICAL",
    active_diagnostics_count: 1,
    critical_count: 1,
    marginal_count: 0,
    top_diagnostic_title: "SonosNet Multi-Hop STP Detour / Weak Upstream Tunnel (Cost 528)",
    wifi_pillar: {
      health_grade: "MARGINAL",
      best_5ghz_rssi_dbm: -72,
      best_24ghz_rssi_dbm: -70,
      covering_ap_name: "Kitchen EAP650",
      link_speed_mbps: 573,
      channel_summary: "Ch 11 (20MHz) / Ch 40 (40MHz)",
      summary_note: "Marginal 5GHz link",
    },
    sonos_pillar: {
      health_grade: "CRITICAL",
      total_players: 1,
      sonosnet_player_count: 1,
      designated_stp_root: "9000.542a1b63fe6e",
      is_stp_root_healthy: true,
      max_stp_path_cost: 528,
      players: [],
      summary_note: "Elevated STP path cost 528",
    },
    wired_pillar: {
      health_grade: "GOOD",
      has_vlan10_wall_jack: true,
      port_numbers: [6],
      stp_root_guard_required: true,
      stp_root_guard_note: "Disable Wi-Fi on secondary wired speaker",
    },
    diagnostics: [
      {
        id: "diag-noemi-stp-detour",
        room_slug: "noemi",
        room_name: "Noemi",
        layer: "SONOS",
        severity: "CRITICAL",
        rule_code: "STP_MULTIHOP_DETOUR",
        title: "SonosNet Multi-Hop STP Detour / Weak Upstream Tunnel (Cost 528)",
        summary: "Noemi routing through an elevated STP path cost (528) to Wohnzimmer_Bookshelf.",
        evidence: {
          max_stp_path_cost: 528,
        },
        solution_proposals: [],
      },
    ],
    solution_proposals: [],
  }),
  flushGhostGroups: vi.fn().mockResolvedValue({
    flushed_count: 0,
    flushed_zones: [],
  }),
  pollLiveSonosNow: vi.fn().mockResolvedValue({
    batch_id: "batch-test",
    reachable_players: 14,
    total_players: 14,
  }),
  runPingSweep: vi.fn().mockResolvedValue({
    reachable_count: 14,
    total_probed: 14,
    max_rtt_ms: 12.5,
    avg_rtt_ms: 4.2,
  }),
}));

const mockRoom: RoomMatrixItem = {
  id: "room-noemi",
  slug: "noemi",
  name: "Noemi",
  floor_id: "floor-og",
  floor_slug: "obergeschoss",
  floor_name: "Obergeschoss",
  health_grade: "CRITICAL",
  wifi_health_grade: "MARGINAL",
  pos_x: 650,
  pos_y: 250,
  is_archived: false,
  best_5ghz_rssi_dbm: -72,
  best_24ghz_rssi_dbm: -70,
  best_ap_name: "Kitchen EAP650",
  link_speed_mbps: 573,
  top_diagnostic_title: "SonosNet Multi-Hop STP Detour / Weak Upstream Tunnel (Cost 528)",
  switch_ports: [
    {
      id: "port-6",
      port_number: 6,
      switch_name: "Netgear GS316EP",
      switch_ip: "192.168.55.155",
      pvid: 10,
      untagged_vlans: "10",
      tagged_vlans: "",
      bpdu_policy: "PASS_THROUGH",
      loop_detection_disabled: true,
      connected_device_label: "Noemi Wall Jack",
      is_archived: false,
    },
  ],
  devices: [],
};

describe("PlainLanguageAdvisorModal Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders modal with room name, health grade, and plain-language root cause explanation", async () => {
    const handleClose = vi.fn();
    render(
      <PlainLanguageAdvisorModal
        isOpen={true}
        room={mockRoom}
        onClose={handleClose}
      />
    );

    // Header elements
    expect(screen.getByText(/Room Health Advisor: Noemi/i)).toBeInTheDocument();
    expect(screen.getByText("CRITICAL")).toBeInTheDocument();

    // Tab buttons
    expect(screen.getByRole("tab", { name: /What is the Root Cause\?/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /How do I Fix It\?/i })).toBeInTheDocument();

    // Plain English Root Cause headline
    await waitFor(() => {
      expect(
        screen.getByText(/Audio Signal Detour Between Floors \(Multi-Hop Wireless Relay\)/i)
      ).toBeInTheDocument();
    });

    // Plain English explanation mentions relaying and zero electrical noise
    expect(screen.getByText(/What is happening in Noemi\?/i)).toBeInTheDocument();
    expect(screen.getByText(/relay \("hop"\) through other upstairs speakers first/i)).toBeInTheDocument();
    expect(screen.getByText(/Clean \(No Electrical Jamming\)/i)).toBeInTheDocument();
  });

  it("switches to 'How do I Fix It?' tab and displays step-by-step checklist with wall jack and Wi-Fi disable instructions", async () => {
    render(
      <PlainLanguageAdvisorModal
        isOpen={true}
        room={mockRoom}
        onClose={vi.fn()}
      />
    );

    // Switch to action tab
    const actionTab = screen.getByRole("tab", { name: /How do I Fix It\?/i });
    fireEvent.click(actionTab);

    // Best Solution Box
    await waitFor(() => {
      expect(screen.getByText(/BEST SOLUTION \(PERMANENT FIX\)/i)).toBeInTheDocument();
    });
    expect(
      screen.getByText(/Plug into Ethernet Wall Socket \+ Turn Off Speaker Wi-Fi/i)
    ).toBeInTheDocument();

    // Mentions pre-wired wall socket (Port 6)
    expect(screen.getByText(/Switch Port 6 \(Noemi Wall Jack\)/i)).toBeInTheDocument();

    // Mentions turning off Wi-Fi in Sonos app
    expect(screen.getByText(/Turn off Wi-Fi on the speaker:/i)).toBeInTheDocument();

    // Mentions wireless alternative
    expect(screen.getByText(/ALTERNATIVE OPTION \(WIRELESS\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Switch Speaker to 5 GHz Home Wi-Fi \(Station Mode\)/i)).toBeInTheDocument();
  });

  it("closes cleanly when clicking the Close button", async () => {
    const handleClose = vi.fn();
    render(
      <PlainLanguageAdvisorModal
        isOpen={true}
        room={mockRoom}
        onClose={handleClose}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Room Health Advisor: Noemi/i)).toBeInTheDocument();
    });

    const closeBtn = screen.getByRole("button", { name: /Close Advisor/i });
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});
