import os
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.mark.asyncio
async def test_build_unified_graph_all_layers_and_nodes_enriched(tmp_path):
    db_file = tmp_path / "test_t4_graph.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"
    app = create_app(database_url=db_url)

    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/api/topology")
            assert resp.status_code == 200
            graph = resp.json()

            assert graph["layer_filter"] == "ALL"
            assert graph["include_blocking"] is True
            assert graph["designated_stp_root"].startswith("9000.542a1b63fe6e")

            nodes = graph["nodes"]
            by_name = {n["name"]: n for n in nodes}

            # Verify core infrastructure + APs + all 14 Sonos players are present
            expected_infra = {
                "Fritzbox 6660": "ROUTER",
                "Firewalla Purple": "ROUTER",
                "Netgear GS316EP": "SWITCH",
                "Galerie EAP650": "WIFI_AP",
                "Kitchen EAP650": "WIFI_AP",
            }
            for dev_name, expected_role in expected_infra.items():
                assert dev_name in by_name, f"Missing infrastructure node {dev_name}"
                assert by_name[dev_name]["device_role"] == expected_role
                assert isinstance(by_name[dev_name]["x"], (int, float))
                assert isinstance(by_name[dev_name]["y"], (int, float))

            sonos_nodes = [n for n in nodes if n["device_role"] == "SONOS_PLAYER"]
            assert len(sonos_nodes) == 14

            # Check enriched telemetry & spatial fields on key nodes
            wz_root = by_name["Wohnzimmer_Bookshelf"]
            assert wz_root["room_name"] == "Wohnzimmer"
            assert wz_root["floor_slug"] == "erdgeschoss"
            assert wz_root["connection_mode"] == "ETHERNET_ROOT"
            assert wz_root["stp_path_cost"] == 0
            assert wz_root["is_stp_root"] is True
            assert wz_root["ofdm_ani_level"] == 6
            assert wz_root["health_grade"] == "EXCELLENT"

            beam = by_name["Fernsehecke (LF,RF)"]
            assert beam["room_name"] == "Fernsehecke"
            assert beam["floor_slug"] == "erdgeschoss"
            assert beam["connection_mode"] == "SONOSNET_MODE"
            assert beam["ofdm_ani_level"] is None  # F-02 normalization
            assert beam["stp_path_cost"] == 200

            nicolas = by_name["Nicolas"]
            assert nicolas["room_name"] == "Nicolas"
            assert nicolas["floor_slug"] == "dachgeschoss"
            assert nicolas["connection_mode"] == "STATION_MODE"
            assert nicolas["ofdm_ani_level"] == 0
            assert nicolas["phy_error_rate"] == 0.0
            assert nicolas["rssi_dbm"] == -75
            assert nicolas["health_grade"] == "EXCELLENT"

            # Verify all 3 layers are represented in edges
            edges = graph["edges"]
            layers_present = {e["layer"] for e in edges}
            assert layers_present == {"WIRED_LAN", "WIFI_INFRA", "SONOS_MESH"}


@pytest.mark.asyncio
async def test_wired_lan_wifi_infra_and_sonos_mesh_edges_and_layer_filtering(tmp_path):
    db_file = tmp_path / "test_t4_layers.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"
    app = create_app(database_url=db_url)

    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # 1. WIRED_LAN layer
            wired_resp = await client.get("/api/topology?layer=WIRED_LAN")
            assert wired_resp.status_code == 200
            wired_edges = wired_resp.json()["edges"]
            assert len(wired_edges) >= 5
            assert all(e["layer"] == "WIRED_LAN" for e in wired_edges)

            wired_pairs = {(e["source_name"], e["target_name"]): e for e in wired_edges}
            assert ("Fritzbox 6660", "Firewalla Purple") in wired_pairs
            assert "WAN/Uplink" in wired_pairs[("Fritzbox 6660", "Firewalla Purple")]["label"]

            assert ("Firewalla Purple", "Netgear GS316EP") in wired_pairs
            fw_sw = wired_pairs[("Firewalla Purple", "Netgear GS316EP")]
            assert "Port 1" in fw_sw["label"]
            assert "1, 10, 20, 30" in fw_sw["label"]

            assert ("Netgear GS316EP", "Galerie EAP650") in wired_pairs
            assert "Port 11" in wired_pairs[("Netgear GS316EP", "Galerie EAP650")]["label"]

            assert ("Netgear GS316EP", "Kitchen EAP650") in wired_pairs
            assert "Port 12" in wired_pairs[("Netgear GS316EP", "Kitchen EAP650")]["label"]

            assert ("Netgear GS316EP", "Wohnzimmer_Bookshelf") in wired_pairs
            sw_root = wired_pairs[("Netgear GS316EP", "Wohnzimmer_Bookshelf")]
            assert "Port 13" in sw_root["label"]
            assert "VLAN 10" in sw_root["label"]
            assert "100FD" in sw_root["label"]

            # 2. WIFI_INFRA layer
            wifi_resp = await client.get("/api/topology?layer=WIFI_INFRA")
            assert wifi_resp.status_code == 200
            wifi_edges = wifi_resp.json()["edges"]
            assert len(wifi_edges) >= 2
            assert all(e["layer"] == "WIFI_INFRA" for e in wifi_edges)

            wifi_pairs = {(e["source_name"], e["target_name"]): e for e in wifi_edges}
            assert ("Galerie EAP650", "Nicolas") in wifi_pairs
            nic_edge = wifi_pairs[("Galerie EAP650", "Nicolas")]
            assert nic_edge["band"] == "5GHz"
            assert nic_edge["channel"] == 44
            assert nic_edge["rssi_dbm"] == -75
            assert nic_edge["link_speed_mbps"] == 1201
            assert nic_edge["health_grade"] in ("EXCELLENT", "GOOD", "MARGINAL")

            # Verify Kitchen EAP650 also has a WIFI_INFRA coverage edge
            assert any(e["source_name"] == "Kitchen EAP650" for e in wifi_edges)

            # 3. SONOS_MESH layer with include_blocking=true
            mesh_resp = await client.get("/api/topology?layer=SONOS_MESH&include_blocking=true")
            assert mesh_resp.status_code == 200
            mesh_edges = mesh_resp.json()["edges"]
            assert all(e["layer"] == "SONOS_MESH" for e in mesh_edges)

            # Verify HT_SATELLITE 5GHz Ch 48 bonds from Beam to LR and RR
            ht_edges = [e for e in mesh_edges if e["stp_state"] == "HT_BOND"]
            assert len(ht_edges) == 2
            ht_targets = {e["target_name"]: e for e in ht_edges}
            assert set(ht_targets.keys()) == {"Fernsehecke (LR)", "Fernsehecke (RR)"}
            for ht_e in ht_edges:
                assert ht_e["source_name"] == "Fernsehecke (LF,RF)"
                assert ht_e["band"] == "5GHz"
                assert ht_e["channel"] == 48
                assert ht_e["is_forwarding"] is True

            # Verify active FORWARDING SonosNet Ch 6 wireless tunnels & SNR HealthGrade rules
            forwarding_ch6 = [
                e
                for e in mesh_edges
                if e["stp_state"] == "FORWARDING" and e["channel"] == 6
            ]
            assert len(forwarding_ch6) >= 10
            fwd_by_target = {e["target_name"]: e for e in forwarding_ch6}

            # min(49, 54) = 49 >= 30 -> GOOD / EXCELLENT
            assert fwd_by_target["Wohnzimmer_Esstisch"]["is_forwarding"] is True
            assert fwd_by_target["Wohnzimmer_Esstisch"]["from_db"] == 49
            assert fwd_by_target["Wohnzimmer_Esstisch"]["to_db"] == 54
            assert fwd_by_target["Wohnzimmer_Esstisch"]["health_grade"] in ("GOOD", "EXCELLENT")

            # min(36, 26) = 26 in 20..29 -> MARGINAL
            assert fwd_by_target["Noah"]["health_grade"] == "MARGINAL"
            # min(23, 33) = 23 in 20..29 -> MARGINAL
            assert fwd_by_target["Noemi"]["health_grade"] == "MARGINAL"

            # Verify BLOCKING (STP 00) backup links present when include_blocking=true
            blocking_edges = [e for e in mesh_edges if e["stp_state"] == "BLOCKING"]
            assert len(blocking_edges) >= 1
            blk = blocking_edges[0]
            assert blk["is_forwarding"] is False
            assert {blk["source_name"], blk["target_name"]} == {
                "Fernsehecke (LF,RF)",
                "Elternbad",
            }

            # 4. SONOS_MESH layer with include_blocking=false omits BLOCKING links
            mesh_no_blk_resp = await client.get(
                "/api/topology?layer=SONOS_MESH&include_blocking=false"
            )
            assert mesh_no_blk_resp.status_code == 200
            mesh_no_blk_edges = mesh_no_blk_resp.json()["edges"]
            assert all(e["stp_state"] != "BLOCKING" for e in mesh_no_blk_edges)
            assert all(e["is_forwarding"] is True for e in mesh_no_blk_edges)


@pytest.mark.asyncio
async def test_floor_and_room_filtering_and_dynamic_wired_sonos_node(tmp_path):
    db_file = tmp_path / "test_t4_filters.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"
    app = create_app(database_url=db_url)

    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # 1. Filter by floor_slug=dachgeschoss
            dg_resp = await client.get("/api/topology?floor_slug=dachgeschoss")
            assert dg_resp.status_code == 200
            dg_graph = dg_resp.json()
            assert len(dg_graph["nodes"]) == 1
            assert dg_graph["nodes"][0]["name"] == "Nicolas"
            assert dg_graph["nodes"][0]["floor_slug"] == "dachgeschoss"
            assert any(e["target_name"] == "Nicolas" for e in dg_graph["edges"])

            # 2. Filter by room_slug=fernsehecke
            fe_resp = await client.get("/api/topology?room_slug=fernsehecke")
            assert fe_resp.status_code == 200
            fe_graph = fe_resp.json()
            assert {n["name"] for n in fe_graph["nodes"]} == {
                "Fernsehecke (LF,RF)",
                "Fernsehecke (LR)",
                "Fernsehecke (RR)",
            }
            assert any(e["stp_state"] == "HT_BOND" for e in fe_graph["edges"])

            # 3. Dynamically switch Noemi to ETHERNET_NODE -> verify WIRED_LAN edge created on Port 6
            devices = (await client.get("/api/devices")).json()
            noemi = next(d for d in devices if d["name"] == "Noemi")
            upd_resp = await client.put(
                f"/api/devices/{noemi['id']}",
                json={"connection_mode": "ETHERNET_NODE"},
            )
            assert upd_resp.status_code == 200

            wired_after = (await client.get("/api/topology?layer=WIRED_LAN")).json()["edges"]
            noemi_wired = [
                e
                for e in wired_after
                if e["source_name"] == "Netgear GS316EP" and e["target_name"] == "Noemi"
            ]
            assert len(noemi_wired) == 1
            assert "Port 6" in noemi_wired[0]["label"]


@pytest.mark.asyncio
async def test_live_postgres_topology_graph_verification():
    pg_url = os.getenv(
        "TEST_POSTGRES_URL",
        "postgresql+asyncpg://sonos:sonos_network_pw@192.168.55.60:5434/sonos_network",
    )
    app = create_app(database_url=pg_url)
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/api/topology")
            assert resp.status_code == 200
            data = resp.json()
            node_names = {n["name"] for n in data["nodes"]}
            assert "Fritzbox 6660" in node_names
            assert "Firewalla Purple" in node_names
            assert "Netgear GS316EP" in node_names
            assert "Galerie EAP650" in node_names
            assert "Kitchen EAP650" in node_names
            assert "Wohnzimmer_Bookshelf" in node_names
            assert "Fernsehecke (RR)" in node_names
            assert "Nicolas" in node_names
            layers = {e["layer"] for e in data["edges"]}
            assert layers == {"WIRED_LAN", "WIFI_INFRA", "SONOS_MESH"}
