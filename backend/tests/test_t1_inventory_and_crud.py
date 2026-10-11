import os
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
async def client(tmp_path):
    db_file = tmp_path / "test_sonos.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"
    app = create_app(database_url=db_url)
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            yield ac


@pytest.mark.asyncio
async def test_seeded_house_inventory_and_domain_mappings(client: AsyncClient):
    # 1. Verify 4 Floors seeded in order
    floors_resp = await client.get("/api/floors")
    assert floors_resp.status_code == 200
    floors = floors_resp.json()
    assert len(floors) == 4
    assert [f["name"] for f in floors] == [
        "Keller",
        "Erdgeschoss",
        "Obergeschoss",
        "Dachgeschoss",
    ]

    # 2. Verify 11 physical Rooms seeded
    rooms_resp = await client.get("/api/rooms")
    assert rooms_resp.status_code == 200
    rooms = rooms_resp.json()
    assert len(rooms) == 11
    room_by_name = {r["name"]: r for r in rooms}
    expected_rooms = {
        "Keller",
        "Wohnzimmer",
        "Fernsehecke",
        "Küche",
        "Büroecke",
        "Galerie",
        "Elternschlafzimmer",
        "Elternbad",
        "Noemi",
        "Noah",
        "Nicolas",
    }
    assert set(room_by_name.keys()) == expected_rooms

    # 3. Verify SwitchPort mappings on Netgear GS316EP (Ports 1, 5, 6, 7, 8, 11, 12, 13, 14, 15)
    ports_resp = await client.get("/api/switch-ports")
    assert ports_resp.status_code == 200
    ports = ports_resp.json()
    port_numbers = {p["port_number"] for p in ports}
    assert {1, 5, 6, 7, 8, 11, 12, 13, 14, 15}.issubset(port_numbers)
    port_by_num = {p["port_number"]: p for p in ports}
    assert port_by_num[13]["patched_room_id"] == room_by_name["Wohnzimmer"]["id"]
    assert port_by_num[13]["pvid"] == 10
    assert port_by_num[5]["patched_room_id"] == room_by_name["Nicolas"]["id"]
    assert port_by_num[6]["patched_room_id"] == room_by_name["Noemi"]["id"]
    assert port_by_num[7]["patched_room_id"] == room_by_name["Noah"]["id"]

    # 4. Verify active NetworkDevices (14 SONOS_PLAYER + 2 active WIFI_AP + 1 SWITCH + 1 ROUTER = 18)
    devices_resp = await client.get("/api/devices")
    assert devices_resp.status_code == 200
    devices = devices_resp.json()
    sonos_players = [d for d in devices if d["device_role"] == "SONOS_PLAYER"]
    assert len(sonos_players) == 14

    by_name = {d["name"]: d for d in devices}
    # Wohnzimmer 3-player mapping & STP Root Bridge invariant
    assert by_name["Wohnzimmer_Bookshelf"]["room_id"] == room_by_name["Wohnzimmer"]["id"]
    assert by_name["Wohnzimmer_Bookshelf"]["connection_mode"] == "ETHERNET_ROOT"
    assert by_name["Wohnzimmer_Bookshelf"]["ip_address"] == "192.168.10.230"
    assert by_name["Wohnzimmer_Bookshelf"]["rincon_uuid"] == "RINCON_542A1B63FE6E01400"
    assert by_name["Wohnzimmer_Esstisch"]["room_id"] == room_by_name["Wohnzimmer"]["id"]
    assert by_name["Wohnzimmer_Buchregal"]["room_id"] == room_by_name["Wohnzimmer"]["id"]

    # Fernsehecke 3-player mapping including bonded RR satellite
    assert by_name["Fernsehecke (LF,RF)"]["room_id"] == room_by_name["Fernsehecke"]["id"]
    assert by_name["Fernsehecke (LR)"]["room_id"] == room_by_name["Fernsehecke"]["id"]
    assert by_name["Fernsehecke (LR)"]["connection_mode"] == "HT_SATELLITE"
    assert by_name["Fernsehecke (RR)"]["room_id"] == room_by_name["Fernsehecke"]["id"]
    assert by_name["Fernsehecke (RR)"]["rincon_uuid"] == "RINCON_949F3E00292E01400"
    assert by_name["Fernsehecke (RR)"]["connection_mode"] == "HT_SATELLITE"

    # Eltern -> Elternschlafzimmer mapping
    assert by_name["Eltern"]["room_id"] == room_by_name["Elternschlafzimmer"]["id"]
    assert by_name["Eltern"]["ip_address"] == "192.168.10.131"

    # Keller wireless leaf invariant & Nicolas 5 GHz STATION_MODE
    assert by_name["Keller"]["connection_mode"] == "SONOSNET_MODE"
    assert by_name["Nicolas"]["connection_mode"] == "STATION_MODE"

    # Managed APs, Switch, Router
    assert by_name["Galerie EAP650"]["device_role"] == "WIFI_AP"
    assert by_name["Kitchen EAP650"]["device_role"] == "WIFI_AP"
    assert by_name["Netgear GS316EP"]["device_role"] == "SWITCH"
    assert by_name["Firewalla Purple"]["device_role"] == "ROUTER"
    assert "EAP330" not in by_name

    # Verify archived EAP330 appears when include_archived=true
    all_devices_resp = await client.get("/api/devices?include_archived=true")
    assert all_devices_resp.status_code == 200
    all_by_name = {d["name"]: d for d in all_devices_resp.json()}
    assert "EAP330" in all_by_name
    assert all_by_name["EAP330"]["is_archived"] is True


@pytest.mark.asyncio
async def test_crud_soft_archive_and_non_destructive_reseed(tmp_path):
    db_file = tmp_path / "test_crud_reseed.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"
    app = create_app(database_url=db_url)

    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # 1. Floor CRUD
            new_floor_resp = await client.post(
                "/api/floors",
                json={"name": "Gartenebene", "slug": "gartenebene", "level_order": -1},
            )
            assert new_floor_resp.status_code == 201
            new_floor = new_floor_resp.json()

            upd_floor_resp = await client.put(
                f"/api/floors/{new_floor['id']}",
                json={"name": "Garten & Terrasse", "level_order": -1},
            )
            assert upd_floor_resp.status_code == 200
            assert upd_floor_resp.json()["name"] == "Garten & Terrasse"

            # 2. Room CRUD (create + update seeded room Wohnzimmer)
            new_room_resp = await client.post(
                "/api/rooms",
                json={
                    "name": "Terrasse",
                    "slug": "terrasse",
                    "floor_id": new_floor["id"],
                    "pos_x": 310.0,
                    "pos_y": 520.0,
                    "health_grade": "GOOD",
                    "description": "Outdoor patio zone",
                },
            )
            assert new_room_resp.status_code == 201
            terrasse = new_room_resp.json()

            rooms = (await client.get("/api/rooms")).json()
            wohnzimmer = next(r for r in rooms if r["name"] == "Wohnzimmer")
            upd_wz_resp = await client.put(
                f"/api/rooms/{wohnzimmer['id']}",
                json={"pos_x": 222.5, "pos_y": 333.5, "health_grade": "EXCELLENT"},
            )
            assert upd_wz_resp.status_code == 200
            assert upd_wz_resp.json()["pos_x"] == 222.5
            assert upd_wz_resp.json()["health_grade"] == "EXCELLENT"

            # 3. SwitchPort CRUD
            new_port_resp = await client.post(
                "/api/switch-ports",
                json={
                    "port_number": 9,
                    "pvid": 10,
                    "untagged_vlans": "10",
                    "tagged_vlans": "",
                    "patched_room_id": terrasse["id"],
                    "connected_device_label": "Terrasse Outdoor Jack",
                },
            )
            assert new_port_resp.status_code == 201
            port9 = new_port_resp.json()

            upd_port_resp = await client.put(
                f"/api/switch-ports/{port9['id']}",
                json={"connected_device_label": "Terrasse PoE Run"},
            )
            assert upd_port_resp.status_code == 200
            assert upd_port_resp.json()["connected_device_label"] == "Terrasse PoE Run"

            # 4. NetworkDevice CRUD (create new + update existing seeded device Noemi + soft-archive)
            new_dev_resp = await client.post(
                "/api/devices",
                json={
                    "name": "Terrasse Move",
                    "slug": "sonos-terrasse-move",
                    "device_role": "SONOS_PLAYER",
                    "model_name": "Sonos Move 2",
                    "ip_address": "192.168.10.250",
                    "connection_mode": "STATION_MODE",
                    "health_grade": "EXCELLENT",
                    "room_id": terrasse["id"],
                },
            )
            assert new_dev_resp.status_code == 201
            move_dev = new_dev_resp.json()

            devices = (await client.get("/api/devices")).json()
            noemi_dev = next(d for d in devices if d["name"] == "Noemi")
            upd_noemi_resp = await client.put(
                f"/api/devices/{noemi_dev['id']}",
                json={"connection_mode": "ETHERNET_NODE", "health_grade": "EXCELLENT"},
            )
            assert upd_noemi_resp.status_code == 200
            assert upd_noemi_resp.json()["connection_mode"] == "ETHERNET_NODE"

            # Soft-archive the newly created device, port, room, and floor
            del_dev = await client.delete(f"/api/devices/{move_dev['id']}")
            assert del_dev.status_code == 200
            assert del_dev.json()["is_archived"] is True

            del_port = await client.delete(f"/api/switch-ports/{port9['id']}")
            assert del_port.status_code == 200
            assert del_port.json()["is_archived"] is True

            del_room = await client.delete(f"/api/rooms/{terrasse['id']}")
            assert del_room.status_code == 200
            assert del_room.json()["is_archived"] is True

            del_floor = await client.delete(f"/api/floors/{new_floor['id']}")
            assert del_floor.status_code == 200
            assert del_floor.json()["is_archived"] is True

            # Default GET excludes archived items; ?include_archived=true returns them
            active_rooms = (await client.get("/api/rooms")).json()
            assert all(r["id"] != terrasse["id"] for r in active_rooms)
            all_rooms = (await client.get("/api/rooms?include_archived=true")).json()
            assert any(r["id"] == terrasse["id"] and r["is_archived"] is True for r in all_rooms)

    # 5. Restart app on the SAME database and verify startup seeding does NOT overwrite user edits!
    app_restarted = create_app(database_url=db_url)
    async with app_restarted.router.lifespan_context(app_restarted):
        transport = ASGITransport(app=app_restarted)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client2:
            rooms_after = (await client2.get("/api/rooms")).json()
            wz_after = next(r for r in rooms_after if r["name"] == "Wohnzimmer")
            assert wz_after["pos_x"] == 222.5
            assert wz_after["health_grade"] == "EXCELLENT"

            devices_after = (await client2.get("/api/devices")).json()
            noemi_after = next(d for d in devices_after if d["name"] == "Noemi")
            assert noemi_after["connection_mode"] == "ETHERNET_NODE"
            assert noemi_after["health_grade"] == "EXCELLENT"


@pytest.mark.asyncio
async def test_overview_matrix_endpoint(client: AsyncClient):
    resp = await client.get("/api/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_rooms"] == 11
    assert data["total_sonos_players"] == 14
    assert len(data["floors"]) == 4
    # Verify Wohnzimmer inside Erdgeschoss has 3 Sonos players attached
    eg = next(f for f in data["floors"] if f["name"] == "Erdgeschoss")
    wz = next(r for r in eg["rooms"] if r["name"] == "Wohnzimmer")
    assert len(wz["devices"]) == 3


@pytest.mark.asyncio
async def test_live_postgres_seed_verification():
    pg_url = os.getenv(
        "TEST_POSTGRES_URL",
        "postgresql+asyncpg://sonos:sonos_network_pw@192.168.55.60:5434/sonos_network",
    )
    app = create_app(database_url=pg_url)
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            floors = (await client.get("/api/floors")).json()
            rooms = (await client.get("/api/rooms")).json()
            devices = (await client.get("/api/devices")).json()
            assert len(floors) >= 4
            assert len(rooms) >= 11
            sonos_players = [d for d in devices if d["device_role"] == "SONOS_PLAYER"]
            assert len(sonos_players) >= 14


@pytest.mark.asyncio
async def test_overview_and_diagnostics_with_unprofiled_player(client: AsyncClient):
    # Regression test for GATE-01: verify adding a player with no prior telemetry snapshot does not crash overview or diagnostics
    rooms_resp = await client.get("/api/rooms")
    room_id = rooms_resp.json()[0]["id"]
    create_payload = {
        "slug": "test-unprofiled-sonos-speaker",
        "name": "Test Unprofiled Sonos",
        "device_role": "SONOS_PLAYER",
        "model_name": "One SL",
        "ip_address": "192.168.10.99",
        "base_mac": "94:9f:3e:aa:bb:cc",
        "sonosnet_bssid": "94:9f:3e:aa:bb:cd",
        "rincon_uuid": "RINCON_949F3EAABBCC01400",
        "connection_mode": "SONOSNET_MODE",
        "room_id": room_id,
    }
    dev_resp = await client.post("/api/devices", json=create_payload)
    assert dev_resp.status_code == 201

    overview_resp = await client.get("/api/overview")
    assert overview_resp.status_code == 200

    diag_resp = await client.get("/api/diagnostics")
    assert diag_resp.status_code == 200
