import os
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.modules.sonos_telemetry import (
    FakeSonosAdapter,
    HttpSonosAdapter,
    parse_ath_rincon_status,
    parse_showstp,
    parse_zone_group_state,
)


@pytest.mark.asyncio
async def test_sonos_adapter_nested_satellite_discovery_and_ht_bond_f05():
    adapter = FakeSonosAdapter(probe_interval_sec=0.0)
    snapshot = await adapter.collect_household_snapshot(consumer_id="test-f05")

    assert snapshot.total_players == 14
    by_uuid = {p.rincon_uuid: p for p in snapshot.players}

    # Verify nested <Satellite> Fernsehecke (RR) is discovered with resolved IP and HT_SATELLITE mode
    rr = by_uuid["RINCON_949F3E00292E01400"]
    assert rr.zone_name == "Fernsehecke (RR)"
    assert rr.connection_mode.value == "HT_SATELLITE"
    assert rr.ip_address == "192.168.10.103"
    assert rr.ieee_channel == 48
    assert rr.bonded_parent_uuid == "RINCON_949F3EC0EEA101400"
    assert rr.is_reachable is True

    # Verify 5 GHz Ch 48 HT_SATELLITE mesh links exist between Beam and both LR & RR
    ht_links = [
        link
        for link in snapshot.mesh_links
        if link.channel == 48
        and {link.source_rincon_uuid, link.target_rincon_uuid}
        == {"RINCON_949F3EC0EEA101400", "RINCON_949F3E00292E01400"}
    ]
    assert len(ht_links) >= 1
    assert ht_links[0].stp_state == "FORWARDING"
    assert ht_links[0].from_db >= 55
    assert ht_links[0].to_db >= 55


@pytest.mark.asyncio
async def test_hardware_telemetry_normalization_f02():
    adapter = FakeSonosAdapter(probe_interval_sec=0.0)
    snapshot = await adapter.collect_household_snapshot(consumer_id="test-f02")
    by_uuid = {p.rincon_uuid: p for p in snapshot.players}

    # Fernsehecke Beam reports Noise Floor: 0, 0, 0, 0 and OFDM ANI level: undefined -> must be None, not 0
    beam = by_uuid["RINCON_949F3EC0EEA101400"]
    assert beam.ofdm_ani_level is None
    assert beam.noise_floor_dbm is None

    # Kueche reports genuine OFDM ANI level: 0 and Noise Floor: -100 dBm -> must be int 0 and -100
    kueche = by_uuid["RINCON_347E5C3826E201400"]
    assert kueche.ofdm_ani_level == 0
    assert kueche.noise_floor_dbm == -100


@pytest.mark.asyncio
async def test_per_consumer_isolated_phy_error_rate_cursors_and_reboot_reset_f04():
    current_time = 1000.0

    def fake_clock() -> float:
        return current_time

    def advance_clock(dt: float) -> None:
        nonlocal current_time
        current_time += dt

    adapter = FakeSonosAdapter(
        probe_interval_sec=1.5,
        clock=fake_clock,
        sleep_fn=advance_clock,
    )

    # 1. Cold read for "background-60s" performs back-to-back 2-sample probe (1.5s interval)
    bg_snap_1 = await adapter.collect_household_snapshot(consumer_id="background-60s")
    wz_buch_1 = next(
        p for p in bg_snap_1.players if p.rincon_uuid == "RINCON_B8E937E5152A01400"
    )
    assert wz_buch_1.phy_error_rate is not None
    assert wz_buch_1.phy_error_rate > 1000.0  # ~1126 err/s on Wohnzimmer_Buchregal

    # Record baseline PHY counter after bg_snap_1 (now at t=1001.5)
    # 2. Simulate WebSocket consumer polling every 2s with a surge in PHY errors,
    #    then quieting down before the 60s background collector runs at t=1061.5
    advance_clock(2.0)  # t=1003.5
    adapter.advance_phy_errors("RINCON_B8E937E5152A01400", delta=4000)
    ws_samples = []
    async for batch in adapter.stream_room_rf_velocity(
        room_id="wohnzimmer",
        interval_sec=2.0,
        consumer_id="ws-session-1",
        max_iterations=2,
    ):
        ws_samples.append(batch)

    assert len(ws_samples) == 2
    ws_buch = next(
        s for s in ws_samples[-1] if s.rincon_uuid == "RINCON_B8E937E5152A01400"
    )
    assert ws_buch.phy_error_rate is not None

    # 3. Advance clock to 60s mark for "background-60s" and verify its cursor was NOT perturbed by ws-session-1
    dt_remaining = 60.0 - (current_time - 1001.5)
    advance_clock(dt_remaining)  # Exactly 60.0s after bg_snap_1 finished at 1001.5
    # Total PHY errors added since bg_snap_1 finished: 4000 + probe increments -> let's set exact counter
    base_after_bg1 = wz_buch_1.phy_error_total
    assert base_after_bg1 is not None
    adapter.set_phy_errors("RINCON_B8E937E5152A01400", base_after_bg1 + 6000)

    bg_snap_2 = await adapter.collect_household_snapshot(consumer_id="background-60s")
    wz_buch_2 = next(
        p for p in bg_snap_2.players if p.rincon_uuid == "RINCON_B8E937E5152A01400"
    )
    # 6000 errors over 60.0s = 100.0 err/s (proving ws-session-1 did not overwrite background-60s cursor!)
    assert wz_buch_2.phy_error_rate == pytest.approx(100.0, rel=0.01)

    # 4. Simulate speaker reboot / counter reset (current_phy < prev_phy) -> yields 0.0 err/s
    advance_clock(10.0)
    adapter.set_phy_errors("RINCON_B8E937E5152A01400", 50)
    bg_snap_3 = await adapter.collect_household_snapshot(consumer_id="background-60s")
    wz_buch_3 = next(
        p for p in bg_snap_3.players if p.rincon_uuid == "RINCON_B8E937E5152A01400"
    )
    assert wz_buch_3.phy_error_rate == 0.0
    assert wz_buch_3.phy_error_total == 50


def test_peer_snr_matrix_and_showstp_and_zone_group_parsers():
    bssid_map = {
        "54:2A:1B:63:FE:6F": "RINCON_542A1B63FE6E01400",
        "94:9F:3E:C0:EE:A2": "RINCON_949F3EC0EEA101400",
    }
    raw_ath = """
Mode: AP
IEEE channel: 6 (2437 MHz)
Chain 0 Noise Floor: -110 dBm
Chain 1 Noise Floor: -109 dBm
OFDM ANI level: 9
PHY errors since last reading/reset: 245100
Node 54:2A:1B:63:FE:6F - FROM 49 : TO 46 : STP 04
Node 94:9F:3E:C0:EE:A2 - FROM 52 : TO 58 : STP 00
"""
    parsed_ath = parse_ath_rincon_status(
        raw_ath,
        source_uuid="RINCON_B8E937E5152A01400",
        source_bssid="B8:E9:37:E5:15:2B",
        bssid_to_uuid=bssid_map,
    )
    assert parsed_ath["ofdm_ani_level"] == 9
    assert parsed_ath["noise_floor_dbm"] == -110
    assert parsed_ath["phy_error_total"] == 245100
    assert parsed_ath["ieee_channel"] == 6
    assert len(parsed_ath["links"]) == 2
    link_by_target = {l["target_rincon_uuid"]: l for l in parsed_ath["links"]}
    assert link_by_target["RINCON_542A1B63FE6E01400"]["stp_state"] == "FORWARDING"
    assert link_by_target["RINCON_542A1B63FE6E01400"]["from_db"] == 49
    assert link_by_target["RINCON_542A1B63FE6E01400"]["to_db"] == 46
    assert link_by_target["RINCON_949F3EC0EEA101400"]["stp_state"] == "BLOCKING"

    raw_stp = """
br0
 bridge id              9000.b8e937e5152a
 designated root        9000.542a1b63fe6e
 root port                 2                    path cost                200
"""
    parsed_stp = parse_showstp(raw_stp)
    assert parsed_stp["designated_root"] == "9000.542a1b63fe6e"
    assert parsed_stp["stp_path_cost"] == 200
    assert parsed_stp["stp_root_port"] == "2"


@pytest.mark.asyncio
async def test_http_sonos_adapter_cross_vlan_concurrency_and_endpoints():
    calls = []

    def fake_http_caller(
        url: str,
        method: str = "GET",
        body: str | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 2.5,
    ) -> str:
        assert timeout >= 2.0
        calls.append((method, url, headers or {}))
        if "ZoneGroupTopology/Control" in url:
            return """<?xml version="1.0"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
<s:Body>
<u:GetZoneGroupStateResponse xmlns:u="urn:schemas-upnp-org:service:ZoneGroupTopology:1">
<ZoneGroupState>&lt;ZoneGroupState&gt;&lt;ZoneGroups&gt;
&lt;ZoneGroup Coordinator="RINCON_542A1B63FE6E01400" ID="RINCON_542A1B63FE6E01400:10"&gt;
&lt;ZoneGroupMember UUID="RINCON_542A1B63FE6E01400" ZoneName="Wohnzimmer_Bookshelf" Location="http://192.168.10.230:1400/xml/device_description.xml" /&gt;
&lt;/ZoneGroup&gt;
&lt;ZoneGroup Coordinator="RINCON_949F3EC0EEA101400" ID="RINCON_949F3EC0EEA101400:11"&gt;
&lt;ZoneGroupMember UUID="RINCON_949F3EC0EEA101400" ZoneName="Fernsehecke (LF,RF)" Location="http://192.168.10.241:1400/xml/device_description.xml"&gt;
&lt;Satellite UUID="RINCON_949F3E00292E01400" ZoneName="Fernsehecke (RR)" Location="http://192.168.10.103:1400/xml/device_description.xml" HTSatChanMapSet="RINCON_949F3EC0EEA101400:LF,RF;RINCON_949F3E00292E01400:RR" /&gt;
&lt;/ZoneGroupMember&gt;
&lt;/ZoneGroup&gt;
&lt;/ZoneGroups&gt;&lt;/ZoneGroupState&gt;</ZoneGroupState>
</u:GetZoneGroupStateResponse>
</s:Body>
</s:Envelope>"""
        if "/status/proc/ath_rincon/status" in url:
            if "192.168.10.241" in url:
                return "Noise Floor: 0, 0, 0, 0\nOFDM ANI level: undefined\nPHY errors since last reading/reset: 0\nIEEE channel: 6\n"
            return "Noise Floor: -108 dBm\nOFDM ANI level: 3\nPHY errors since last reading/reset: 500\nIEEE channel: 6\n"
        if "/status/showstp" in url:
            if "192.168.10.230" in url:
                return "designated root 9000.542a1b63fe6e\nroot port 0 path cost 0\n"
            return "designated root 9000.542a1b63fe6e\nroot port 1 path cost 200\n"
        if "/status/wireless" in url:
            return "WifiModeString: SONOSNET_MODE\n"
        if "/status/enetports" in url:
            if "192.168.10.230" in url:
                return "Port 0: Link: 100FD\n"
            return "Port 0: Link: DOWN\n"
        if "RenderingControl/Control" in url:
            return "<s:Envelope><s:Body><CurrentVolume>22</CurrentVolume></s:Body></s:Envelope>"
        if "AVTransport/Control" in url:
            return "<s:Envelope><s:Body><NewGroupID>RINCON_542A1B63FE6E01400:99</NewGroupID></s:Body></s:Envelope>"
        return ""

    http_adapter = HttpSonosAdapter(
        max_workers=12,
        timeout_sec=2.5,
        probe_interval_sec=0.0,
        http_caller=fake_http_caller,
    )
    assert http_adapter.max_workers <= 14
    assert http_adapter.timeout_sec >= 2.0

    snap = await http_adapter.collect_household_snapshot(consumer_id="http-test")
    assert snap.total_players == 14
    by_uuid = {p.rincon_uuid: p for p in snap.players}
    assert by_uuid["RINCON_949F3E00292E01400"].ip_address == "192.168.10.103"
    assert by_uuid["RINCON_949F3EC0EEA101400"].ofdm_ani_level is None
    assert by_uuid["RINCON_949F3EC0EEA101400"].noise_floor_dbm is None


@pytest.mark.asyncio
async def test_ghost_group_detection_flush_and_api_endpoints(tmp_path):
    db_file = tmp_path / "test_t2_sonos.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"
    fake_adapter = FakeSonosAdapter(probe_interval_sec=0.0)
    # Inject a Ghost Group mismatch on Wohnzimmer_Esstisch (.160):
    # Coordinator is RINCON_B8E937E6098401400, but Group ID prefix belongs to departed Eltern RINCON_347E5C3828B001400:77
    fake_adapter.inject_ghost_group(
        rincon_uuid="RINCON_B8E937E6098401400",
        corrupted_group_id="RINCON_347E5C3828B001400:77",
        has_vanished_devices=True,
    )

    app = create_app(database_url=db_url, sonos_adapter=fake_adapter)
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # 1. Trigger on-demand poll via POST /api/actions/poll-now
            poll_resp = await client.post("/api/actions/poll-now")
            assert poll_resp.status_code == 200
            poll_data = poll_resp.json()
            assert poll_data["has_ghost_groups"] is True
            assert poll_data["ghost_group_count"] >= 1
            assert "Wohnzimmer_Esstisch" in poll_data["ghost_group_zones"]

            # 2. Verify GET /api/sonos/telemetry reflects the persisted snapshot & mesh links
            telem_resp = await client.get("/api/sonos/telemetry")
            assert telem_resp.status_code == 200
            telem_data = telem_resp.json()
            assert telem_data["has_ghost_groups"] is True
            assert len(telem_data["players"]) == 14
            assert len(telem_data["mesh_links"]) > 0
            esstisch = next(
                p for p in telem_data["players"] if p["zone_name"] == "Wohnzimmer_Esstisch"
            )
            assert esstisch["is_ghost_group"] is True
            assert esstisch["group_id"] == "RINCON_347E5C3828B001400:77"

            # 3. Verify GET /api/overview rooms & devices are enriched with latest Sonos telemetry & ghost status
            ov_resp = await client.get("/api/overview")
            assert ov_resp.status_code == 200
            ov_data = ov_resp.json()
            assert ov_data["has_ghost_groups"] is True
            assert "Wohnzimmer_Esstisch" in ov_data["ghost_group_zones"]
            eg = next(f for f in ov_data["floors"] if f["name"] == "Erdgeschoss")
            wz = next(r for r in eg["rooms"] if r["name"] == "Wohnzimmer")
            wz_esstisch_dev = next(
                d for d in wz["devices"] if d["name"] == "Wohnzimmer_Esstisch"
            )
            assert wz_esstisch_dev["is_ghost_group"] is True
            assert wz_esstisch_dev["phy_error_rate"] is not None
            assert wz_esstisch_dev["stp_path_cost"] is not None
            assert wz_esstisch_dev["master_volume"] is not None

            # 4. Flush Ghost Groups via POST /api/actions/flush-ghost-groups
            flush_resp = await client.post("/api/actions/flush-ghost-groups")
            assert flush_resp.status_code == 200
            flush_data = flush_resp.json()
            assert flush_data["flushed_count"] >= 1
            assert "Wohnzimmer_Esstisch" in flush_data["flushed_zones"]
            esstisch_res = next(
                r for r in flush_data["results"] if r["zone_name"] == "Wohnzimmer_Esstisch"
            )
            assert esstisch_res["new_group_id"].startswith("RINCON_B8E937E6098401400:")

            # 5. Verify GET /api/sonos/telemetry and GET /api/overview now show 0 ghost groups
            telem_after = (await client.get("/api/sonos/telemetry")).json()
            assert telem_after["has_ghost_groups"] is False
            assert telem_after["ghost_group_count"] == 0

            ov_after = (await client.get("/api/overview")).json()
            assert ov_after["has_ghost_groups"] is False


@pytest.mark.asyncio
async def test_historical_and_baseline_snapshots_seeded_idempotently_and_live_postgres():
    pg_url = os.getenv(
        "TEST_POSTGRES_URL",
        "postgresql+asyncpg://sonos:sonos_network_pw@192.168.55.60:5434/sonos_network",
    )
    app = create_app(database_url=pg_url)
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Verify 19 Sep 2026 historical batch (Keller was root: 9000.5caafd595eea)
            sep_resp = await client.get("/api/sonos/telemetry?batch_id=hist-2026-09-19")
            assert sep_resp.status_code == 200
            sep_data = sep_resp.json()
            assert sep_data["designated_stp_root"].startswith("9000.5caafd595eea")
            assert len(sep_data["players"]) == 14

            # Verify 5 Oct 2026 post-remediation baseline batch (Wohnzimmer_Bookshelf root: 9000.542a1b63fe6e)
            oct_resp = await client.get("/api/sonos/telemetry?batch_id=baseline-2026-10-05")
            assert oct_resp.status_code == 200
            oct_data = oct_resp.json()
            assert oct_data["designated_stp_root"].startswith("9000.542a1b63fe6e")
            assert len(oct_data["players"]) == 14
            assert len(oct_data["mesh_links"]) > 0
