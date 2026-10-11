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
          best_5ghz_dbm: -72,
          best_24ghz_dbm: -82,
          best_ap_name: "Galerie EAP650",
          link_speed_mbps: 1201,
          wifi_health_grade: "MARGINAL",
          is_archived: false,
          devices: [],
          switch_ports: [],
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
          is_archived: false,
          devices: [],
          switch_ports: [],
        },
      ],
    },
  ],
};

const mockTopologyGraph = {
  layer_filter: "ALL",
  floor_slug: null,
  room_slug: null,
  include_blocking: true,
  designated_stp_root: "9000.542a1b63fe6e (Wohnzimmer_Bookshelf 192.168.10.230)",
  total_nodes: 7,
  total_edges: 6,
  nodes: [
    {
      id: "router-fritzbox-6660",
      slug: "router-fritzbox-6660",
      name: "Fritzbox 6660",
      device_role: "ROUTER",
      model_name: "FRITZ!Box 6660 Cable",
      ip_address: "192.168.178.1",
      room_slug: "keller",
      room_name: "Keller",
      floor_slug: "keller",
      floor_name: "Keller",
      health_grade: "EXCELLENT",
      x: 80,
      y: 720,
      pos_x: 80,
      pos_y: 720,
    },
    {
      id: "router-firewalla-purple",
      slug: "router-firewalla-purple",
      name: "Firewalla Purple",
      device_role: "ROUTER",
      model_name: "Firewalla Purple",
      ip_address: "192.168.55.1",
      room_slug: "keller",
      room_name: "Keller",
      floor_slug: "keller",
      floor_name: "Keller",
      health_grade: "EXCELLENT",
      x: 240,
      y: 720,
      pos_x: 240,
      pos_y: 720,
    },
    {
      id: "switch-netgear-gs316ep",
      slug: "switch-netgear-gs316ep",
      name: "Netgear GS316EP",
      device_role: "SWITCH",
      model_name: "NETGEAR GS316EP",
      ip_address: "192.168.55.155",
      room_slug: "keller",
      room_name: "Keller",
      floor_slug: "keller",
      floor_name: "Keller",
      health_grade: "EXCELLENT",
      x: 420,
      y: 720,
      pos_x: 420,
      pos_y: 720,
    },
    {
      id: "ap-galerie-eap650",
      slug: "ap-galerie-eap650",
      name: "Galerie EAP650",
      device_role: "WIFI_AP",
      model_name: "EAP650(EU) v1.0",
      ip_address: "192.168.55.79",
      room_slug: "galerie",
      room_name: "Galerie",
      floor_slug: "obergeschoss",
      floor_name: "Obergeschoss",
      health_grade: "EXCELLENT",
      ap_channels: "2.4GHz Ch 1 (20MHz) · 5GHz Ch 44 (80MHz)",
      x: 400,
      y: 230,
      pos_x: 400,
      pos_y: 230,
    },
    {
      id: "sonos-wohnzimmer-bookshelf",
      slug: "sonos-wohnzimmer-bookshelf",
      name: "Wohnzimmer_Bookshelf",
      device_role: "SONOS_PLAYER",
      model_name: "SYMFONISK Bookshelf",
      ip_address: "192.168.10.230",
      room_slug: "wohnzimmer",
      room_name: "Wohnzimmer",
      floor_slug: "erdgeschoss",
      floor_name: "Erdgeschoss",
      connection_mode: "ETHERNET_ROOT",
      health_grade: "EXCELLENT",
      ofdm_ani_level: 6,
      phy_error_rate: 12.5,
      stp_path_cost: 0,
      is_stp_root: true,
      x: 110,
      y: 450,
      pos_x: 110,
      pos_y: 450,
    },
    {
      id: "sonos-fernsehecke-beam",
      slug: "sonos-fernsehecke-beam",
      name: "Fernsehecke (LF,RF)",
      device_role: "SONOS_PLAYER",
      model_name: "Sonos Beam",
      ip_address: "192.168.10.241",
      room_slug: "fernsehecke",
      room_name: "Fernsehecke",
      floor_slug: "erdgeschoss",
      floor_name: "Erdgeschoss",
      connection_mode: "SONOSNET_MODE",
      health_grade: "EXCELLENT",
      ofdm_ani_level: null,
      phy_error_rate: 0.0,
      stp_path_cost: 200,
      x: 410,
      y: 450,
      pos_x: 410,
      pos_y: 450,
    },
    {
      id: "sonos-fernsehecke-rr",
      slug: "sonos-fernsehecke-rr",
      name: "Fernsehecke (RR)",
      device_role: "SONOS_PLAYER",
      model_name: "Sonos One / Play:1",
      ip_address: "192.168.10.103",
      room_slug: "fernsehecke",
      room_name: "Fernsehecke",
      floor_slug: "erdgeschoss",
      floor_name: "Erdgeschoss",
      connection_mode: "HT_SATELLITE",
      health_grade: "GOOD",
      ofdm_ani_level: 0,
      phy_error_rate: 0.0,
      stp_path_cost: 220,
      x: 470,
      y: 550,
      pos_x: 470,
      pos_y: 550,
    },
    {
      id: "sonos-elternbad",
      slug: "sonos-elternbad",
      name: "Elternbad",
      device_role: "SONOS_PLAYER",
      model_name: "SYMFONISK Bookshelf",
      ip_address: "192.168.10.113",
      room_slug: "elternbad",
      room_name: "Elternbad",
      floor_slug: "obergeschoss",
      floor_name: "Obergeschoss",
      connection_mode: "SONOSNET_MODE",
      health_grade: "GOOD",
      ofdm_ani_level: 4,
      phy_error_rate: 1.8,
      stp_path_cost: 280,
      x: 50,
      y: 260,
      pos_x: 50,
      pos_y: 260,
    },
    {
      id: "sonos-nicolas",
      slug: "sonos-nicolas",
      name: "Nicolas",
      device_role: "SONOS_PLAYER",
      model_name: "SYMFONISK Bookshelf",
      ip_address: "192.168.10.165",
      room_slug: "nicolas",
      room_name: "Nicolas",
      floor_slug: "dachgeschoss",
      floor_name: "Dachgeschoss",
      connection_mode: "STATION_MODE",
      health_grade: "EXCELLENT",
      ofdm_ani_level: 0,
      phy_error_rate: 0.0,
      stp_path_cost: 0,
      rssi_dbm: -75,
      x: 500,
      y: 80,
      pos_x: 500,
      pos_y: 80,
    },
  ],
  edges: [
    {
      id: "wired-fritzbox-to-firewalla",
      layer: "WIRED_LAN",
      source: "router-fritzbox-6660",
      source_id: "router-fritzbox-6660",
      source_slug: "router-fritzbox-6660",
      source_name: "Fritzbox 6660",
      target: "router-firewalla-purple",
      target_id: "router-firewalla-purple",
      target_slug: "router-firewalla-purple",
      target_name: "Firewalla Purple",
      label: "WAN/Uplink (2.5GbE Cable Bridge)",
      is_forwarding: true,
      line_style: "solid",
      health_grade: "EXCELLENT",
    },
    {
      id: "wired-gs316ep-to-sonos-wohnzimmer-bookshelf",
      layer: "WIRED_LAN",
      source: "switch-netgear-gs316ep",
      source_id: "switch-netgear-gs316ep",
      source_slug: "switch-netgear-gs316ep",
      source_name: "Netgear GS316EP",
      target: "sonos-wohnzimmer-bookshelf",
      target_id: "sonos-wohnzimmer-bookshelf",
      target_slug: "sonos-wohnzimmer-bookshelf",
      target_name: "Wohnzimmer_Bookshelf",
      label: "Port 13 — VLAN 10, 100FD, STP Root Cost 0",
      is_forwarding: true,
      line_style: "solid",
      stp_state: "FORWARDING",
      port_number: 13,
      vlan_label: "VLAN 10",
      link_speed_mbps: 100,
      health_grade: "EXCELLENT",
    },
    {
      id: "wifi-ap-galerie-eap650-to-sonos-nicolas",
      layer: "WIFI_INFRA",
      source: "ap-galerie-eap650",
      source_id: "ap-galerie-eap650",
      source_slug: "ap-galerie-eap650",
      source_name: "Galerie EAP650",
      target: "sonos-nicolas",
      target_id: "sonos-nicolas",
      target_slug: "sonos-nicolas",
      target_name: "Nicolas",
      label: "5GHz Ch 44 -75 dBm (1201 Mbps)",
      is_forwarding: true,
      line_style: "solid",
      band: "5GHz",
      channel: 44,
      rssi_dbm: -75,
      link_speed_mbps: 1201,
      health_grade: "MARGINAL",
    },
    {
      id: "sonos-mesh-root-to-beam",
      layer: "SONOS_MESH",
      source: "sonos-wohnzimmer-bookshelf",
      source_id: "sonos-wohnzimmer-bookshelf",
      source_slug: "sonos-wohnzimmer-bookshelf",
      source_name: "Wohnzimmer_Bookshelf",
      target: "sonos-fernsehecke-beam",
      target_id: "sonos-fernsehecke-beam",
      target_slug: "sonos-fernsehecke-beam",
      target_name: "Fernsehecke (LF,RF)",
      label: "Ch 6 · 47/57 dB (STP FORWARDING)",
      is_forwarding: true,
      line_style: "solid",
      stp_state: "FORWARDING",
      band: "2.4GHz",
      channel: 6,
      from_db: 47,
      to_db: 57,
      health_grade: "EXCELLENT",
    },
    {
      id: "sonos-ht-bond-beam-to-rr",
      layer: "SONOS_MESH",
      source: "sonos-fernsehecke-beam",
      source_id: "sonos-fernsehecke-beam",
      source_slug: "sonos-fernsehecke-beam",
      source_name: "Fernsehecke (LF,RF)",
      target: "sonos-fernsehecke-rr",
      target_id: "sonos-fernsehecke-rr",
      target_slug: "sonos-fernsehecke-rr",
      target_name: "Fernsehecke (RR)",
      label: "5GHz Ch 48 HT Bond · 60/66 dB",
      is_forwarding: true,
      line_style: "solid",
      stp_state: "HT_BOND",
      band: "5GHz",
      channel: 48,
      from_db: 60,
      to_db: 66,
      health_grade: "EXCELLENT",
    },
    {
      id: "sonos-mesh-blocking-beam-to-elternbad",
      layer: "SONOS_MESH",
      source: "sonos-fernsehecke-beam",
      source_id: "sonos-fernsehecke-beam",
      source_slug: "sonos-fernsehecke-beam",
      source_name: "Fernsehecke (LF,RF)",
      target: "sonos-elternbad",
      target_id: "sonos-elternbad",
      target_slug: "sonos-elternbad",
      target_name: "Elternbad",
      label: "Ch 6 · 54/48 dB (STP 00 BLOCKING)",
      is_forwarding: false,
      line_style: "dashed",
      stp_state: "BLOCKING",
      band: "2.4GHz",
      channel: 6,
      from_db: 54,
      to_db: 48,
      health_grade: "EXCELLENT",
    },
  ],
};

describe("T4 Interactive Dual Network Topology Graph View", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/overview")) {
          return new Response(JSON.stringify(mockOverview), { status: 200 });
        }
        if (url.includes("/api/topology")) {
          return new Response(JSON.stringify(mockTopologyGraph), { status: 200 });
        }
        return new Response(JSON.stringify([]), { status: 200 });
      })
    );
  });

  it("switches to the Interactive Network Topology Graph tab, renders nodes & edges across all 3 layers, filters by layer/STP/floor, and opens the Node Detail panel on click", async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText("Dachgeschoss")).toBeInTheDocument();
    });

    // Switch to the Interactive Network Topology Graph view tab
    const graphTabBtn = screen.getByRole("button", {
      name: /Interactive Network Topology Graph/i,
    });
    fireEvent.click(graphTabBtn);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/topology"));
    });

    // Verify nodes from all roles are rendered with telemetry / channels
    expect(await screen.findByText("Fritzbox 6660")).toBeInTheDocument();
    expect(screen.getByText("Firewalla Purple")).toBeInTheDocument();
    expect(screen.getByText("Netgear GS316EP")).toBeInTheDocument();
    expect(screen.getByText("Galerie EAP650")).toBeInTheDocument();
    expect(screen.getByText(/2\.4GHz Ch 1 \(20MHz\) · 5GHz Ch 44 \(80MHz\)/i)).toBeInTheDocument();
    expect(screen.getByText("Wohnzimmer_Bookshelf")).toBeInTheDocument();
    expect(screen.getByText("Fernsehecke (RR)")).toBeInTheDocument();

    // Verify edge labels across WIRED_LAN, WIFI_INFRA, and SONOS_MESH
    expect(screen.getByText(/Port 13 — VLAN 10, 100FD, STP Root Cost 0/i)).toBeInTheDocument();
    expect(screen.getByText(/5GHz Ch 44 -75 dBm \(1201 Mbps\)/i)).toBeInTheDocument();
    expect(screen.getByText(/5GHz Ch 48 HT Bond · 60\/66 dB/i)).toBeInTheDocument();
    expect(screen.getByText(/Ch 6 · 47\/57 dB \(STP FORWARDING\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Ch 6 · 54\/48 dB \(STP 00 BLOCKING\)/i)).toBeInTheDocument();

    // Filter to Wi-Fi & VLAN Layer (WIFI_INFRA + WIRED_LAN) -> hides SONOS_MESH edges
    const wifiLayerBtn = screen.getByRole("button", {
      name: /Wi-Fi & VLAN Layer/i,
    });
    fireEvent.click(wifiLayerBtn);
    expect(screen.queryByText(/Ch 6 · 47\/57 dB \(STP FORWARDING\)/i)).not.toBeInTheDocument();
    expect(screen.getByText(/5GHz Ch 44 -75 dBm \(1201 Mbps\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Port 13 — VLAN 10, 100FD, STP Root Cost 0/i)).toBeInTheDocument();

    // Filter to Sonos Mesh & STP Layer (SONOS_MESH + WIRED_LAN) -> shows SONOS_MESH, hides WIFI_INFRA
    const sonosLayerBtn = screen.getByRole("button", {
      name: /Sonos Mesh & STP Layer/i,
    });
    fireEvent.click(sonosLayerBtn);
    expect(screen.getByText(/Ch 6 · 47\/57 dB \(STP FORWARDING\)/i)).toBeInTheDocument();
    expect(screen.queryByText(/5GHz Ch 44 -75 dBm \(1201 Mbps\)/i)).not.toBeInTheDocument();

    // Toggle Hide Blocked STP Links (STP 00) -> hides BLOCKING edge
    const blockingToggle = screen.getByLabelText(/Show Blocked STP Links/i);
    fireEvent.click(blockingToggle);
    expect(screen.queryByText(/Ch 6 · 54\/48 dB \(STP 00 BLOCKING\)/i)).not.toBeInTheDocument();

    // Restore All Layers
    const allLayersBtn = screen.getByRole("button", { name: /All Layers/i });
    fireEvent.click(allLayersBtn);

    // Click on Wohnzimmer_Bookshelf node -> opens Node Detail Inspector Panel
    const rootNodeCard = screen.getByTestId("topology-node-sonos-wohnzimmer-bookshelf");
    fireEvent.click(rootNodeCard);

    expect(
      await screen.findByRole("region", { name: /Topology Node Detail Panel/i })
    ).toBeInTheDocument();
    expect(screen.getByText(/Connected Edges/i)).toBeInTheDocument();

    // Filter by Floor = Dachgeschoss -> only Nicolas remains visible on canvas
    const floorSelect = screen.getByLabelText(/Floor Filter/i);
    fireEvent.change(floorSelect, { target: { value: "dachgeschoss" } });
    expect(screen.getByTestId("topology-node-sonos-nicolas")).toBeInTheDocument();
    expect(
      screen.queryByTestId("topology-node-sonos-wohnzimmer-bookshelf")
    ).not.toBeInTheDocument();
    // Cross-floor connection renders as explicit Uplink Anchor Badge instead of off-canvas line
    expect(screen.getByText(/▲ Uplink: Galerie EAP650 \(Obergeschoss\)/i)).toBeInTheDocument();
  });
});
