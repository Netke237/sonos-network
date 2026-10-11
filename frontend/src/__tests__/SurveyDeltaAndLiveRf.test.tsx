import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
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
          health_grade: "MARGINAL",
          best_5ghz_dbm: -72,
          best_24ghz_dbm: -82,
          best_ap_name: "Galerie EAP650",
          link_speed_mbps: 1201,
          wifi_health_grade: "MARGINAL",
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
          switch_ports: [],
        },
      ],
    },
  ],
};

const mockNicolasSurveys = [
  {
    id: "surv-nic-2",
    survey_slug: "nicolas-08-oct-2026-sanitized",
    room_slug: "nicolas",
    room_name: "Nicolas",
    label: "8 Oct 2026 Post-Remediation Verification",
    trigger_mode: "HISTORICAL_SEED",
    captured_at: "2026-10-08T22:43:00Z",
    connected_bssid: "76:4C:BC:76:7C:41",
    connected_ssid: "WuTangLan-Family",
    link_speed_mbps: 1201,
    best_5ghz_dbm: -72,
    best_24ghz_dbm: -82,
    best_ap_name: "Galerie EAP650",
    wifi_health_grade: "MARGINAL",
    readings: [],
  },
  {
    id: "surv-nic-1",
    survey_slug: "nicolas-19-sep-2026-baseline",
    room_slug: "nicolas",
    room_name: "Nicolas",
    label: "20 Sep 2026 Historical Baseline",
    trigger_mode: "HISTORICAL_SEED",
    captured_at: "2026-09-20T20:54:00Z",
    connected_bssid: "0C:72:74:00:63:9B",
    connected_ssid: "WuTangLan",
    link_speed_mbps: 2401,
    best_5ghz_dbm: -70,
    best_24ghz_dbm: -67,
    best_ap_name: "Galerie EAP650",
    wifi_health_grade: "MARGINAL",
    readings: [],
  },
];

const mockNicolasDelta = {
  room_id: "rm-nicolas",
  room_slug: "nicolas",
  room_name: "Nicolas",
  baseline_survey_id: "surv-nic-1",
  baseline_survey_slug: "nicolas-19-sep-2026-baseline",
  baseline_label: "20 Sep 2026 Historical Baseline",
  baseline_captured_at: "2026-09-20T20:54:00Z",
  target_survey_id: "surv-nic-2",
  target_survey_slug: "nicolas-08-oct-2026-sanitized",
  target_label: "8 Oct 2026 Post-Remediation Verification",
  target_captured_at: "2026-10-08T22:43:00Z",
  baseline_5ghz_dbm: -70,
  target_5ghz_dbm: -72,
  delta_5ghz_dbm: -2,
  baseline_24ghz_dbm: -67,
  target_24ghz_dbm: -82,
  delta_24ghz_dbm: -15,
  baseline_link_speed_mbps: 2401,
  target_link_speed_mbps: 1201,
  delta_link_speed_mbps: -1200,
  baseline_best_ap_name: "Galerie EAP650",
  target_best_ap_name: "Galerie EAP650",
  baseline_wifi_health_grade: "MARGINAL",
  target_wifi_health_grade: "MARGINAL",
  wifi_improved: false,
  baseline_ofdm_ani_level: 0,
  target_ofdm_ani_level: 0,
  delta_ofdm_ani_level: 0,
  baseline_phy_error_rate: 0.0,
  target_phy_error_rate: 0.0,
  delta_phy_error_rate: 0.0,
  baseline_stp_path_cost: 0,
  target_stp_path_cost: 0,
  delta_stp_path_cost: 0,
  baseline_ping_rtt_ms: 2.3,
  target_ping_rtt_ms: 2.3,
  delta_ping_rtt_ms: 0.0,
  sonos_improved: false,
  overall_improved: false,
  summary_narrative:
    "5 GHz signal shifted by -2 dBm (-70 -> -72 dBm via Galerie EAP650). Rogue EAP330 fully eliminated.",
  bssid_deltas: [
    {
      bssid: "76:4C:BC:76:7C:41",
      ssid: "WuTangLan-Family",
      band: "5GHz",
      channel: 44,
      classification: "OWN_MANAGED_AP",
      baseline_rssi_dbm: -70,
      target_rssi_dbm: -75,
      delta_rssi_dbm: -5,
      is_new: false,
      is_vanished: false,
    },
    {
      bssid: "84:16:F9:93:E9:2D",
      ssid: "TP-Link_5G_93E92D",
      band: "5GHz",
      channel: 44,
      classification: "ROGUE_OWN_RADIO",
      baseline_rssi_dbm: -55,
      target_rssi_dbm: null,
      delta_rssi_dbm: null,
      is_new: false,
      is_vanished: true,
    },
  ],
};

// Mock WebSocket
class MockWebSocket {
  url: string;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  readyState = 1;

  constructor(url: string) {
    this.url = url;
    setTimeout(() => {
      if (this.onmessage) {
        this.onmessage({
          data: JSON.stringify({
            timestamp: "2026-10-11T16:00:00Z",
            consumer_id: "ws-mock123",
            room_slug: "all",
            samples: [
              {
                rincon_uuid: "RINCON_B8E937E5152A01400",
                zone_name: "Wohnzimmer_Buchregal",
                room_id: "rm-wz",
                ip_address: "192.168.10.101",
                ieee_channel: 6,
                ofdm_ani_level: 9,
                noise_floor_dbm: -110,
                phy_error_total: 245100,
                phy_error_rate: 1126.0,
                captured_at: "2026-10-11T16:00:00Z",
              },
              {
                rincon_uuid: "RINCON_347E5C36DE9001400",
                zone_name: "Nicolas",
                room_id: "rm-nicolas",
                ip_address: "192.168.10.165",
                ieee_channel: 6,
                ofdm_ani_level: 0,
                noise_floor_dbm: -102,
                phy_error_total: 0,
                phy_error_rate: 0.0,
                captured_at: "2026-10-11T16:00:00Z",
              },
            ],
          }),
        });
      }
    }, 50);
  }

  close() {
    this.readyState = 3;
    if (this.onclose) this.onclose();
  }
}

describe("T6 Room Walkthrough Survey Delta & Live RF Console Slice", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.stubGlobal("WebSocket", MockWebSocket);
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/overview")) {
          return new Response(JSON.stringify(mockOverview), { status: 200 });
        }
        if (url.includes("/api/rooms/nicolas/surveys/delta")) {
          return new Response(JSON.stringify(mockNicolasDelta), { status: 200 });
        }
        if (url.includes("/api/rooms/nicolas/surveys")) {
          return new Response(JSON.stringify(mockNicolasSurveys), { status: 200 });
        }
        return new Response(JSON.stringify([]), { status: 200 });
      })
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("switches to Live RF & EMI Isolation Console tab, receives streaming WebSocket telemetry, and displays EMI spikes", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText("Nicolas").length).toBeGreaterThan(0);
    });

    // Find and click the Live RF & EMI Isolation Console tab
    const emiTab = screen.getByRole("button", {
      name: /Live RF & EMI Isolation Console/i,
    });
    fireEvent.click(emiTab);

    // Verify region is rendered
    const consoleRegion = await screen.findByRole("region", {
      name: /Live RF and EMI Isolation Console/i,
    });
    expect(consoleRegion).toBeInTheDocument();

    // Verify streaming telemetry appears
    await waitFor(() => {
      expect(screen.getByText("Wohnzimmer_Buchregal")).toBeInTheDocument();
      expect(screen.getByText(/1126\.0 err\/s/i)).toBeInTheDocument();
      expect(screen.getByText(/ANI 9/i)).toBeInTheDocument();
    });

    // Verify sequential EMI isolation guidance text is shown
    expect(
      screen.getByText(
        /Unplug USB-C dock or power bricks while watching PHY error rate drop to 0\.0 err\/s/i
      )
    ).toBeInTheDocument();
  });

  it("opens room survey drawer, loads Before/After Survey Delta, and renders BSSID diff table", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText("Nicolas").length).toBeGreaterThan(0);
    });

    // Open Nicolas Wi-Fi survey drawer
    const inspectBtn = screen.getByRole("button", {
      name: /Inspect Room Wi-Fi/i,
    });
    fireEvent.click(inspectBtn);

    // Click "Compare Surveys / View Delta" button inside drawer
    const deltaBtn = await screen.findByRole("button", {
      name: /Compare Surveys \/ View Delta/i,
    });
    fireEvent.click(deltaBtn);

    // Verify Survey Before/After Comparison Delta region appears
    const deltaRegion = await screen.findByRole("region", {
      name: /Survey Before\/After Comparison Delta/i,
    });
    expect(deltaRegion).toBeInTheDocument();

    // Verify delta metrics and narrative
    expect(
      screen.getByText(/Rogue EAP330 fully eliminated/i)
    ).toBeInTheDocument();
    expect(screen.getAllByText(/-2 dBm/i).length).toBeGreaterThan(0);

    // Verify BSSID diff table displays vanished rogue EAP330
    expect(screen.getByText("84:16:F9:93:E9:2D")).toBeInTheDocument();
    expect(screen.getByText(/VANISHED/i)).toBeInTheDocument();
    expect(screen.getByText("76:4C:BC:76:7C:41")).toBeInTheDocument();
  });
});
