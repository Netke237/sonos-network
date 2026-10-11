import os
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.models.entities import ConnectionMode
from app.modules.diagnostic_engine import (
    DiagnosticEngine,
    FakeNetworkProbeAdapter,
    grade_sonos_player_link,
    grade_sonos_player_rf,
)
from app.modules.sonos_telemetry import EXPECTED_STP_ROOT, FakeSonosAdapter
from app.schemas.topology import (
    BssidReadingSchema,
    PlayerTelemetryDto,
    SonosMeshLinkDto,
    SwitchPortRead,
    WiFiRoomSurveySchema,
)


def test_connection_mode_scoped_grading_f02():
    # 1. Sonos RF Grading when OfdmAniLevel is present (0..9)
    assert grade_sonos_player_rf(ofdm_ani_level=0, phy_error_rate=0.0, ping_rtt_ms=2.3) in (
        "EXCELLENT",
        "GOOD",
    )
    assert grade_sonos_player_rf(ofdm_ani_level=3, phy_error_rate=15.0, ping_rtt_ms=5.0) == "GOOD"
    assert (
        grade_sonos_player_rf(ofdm_ani_level=5, phy_error_rate=10.0, ping_rtt_ms=8.0)
        == "MARGINAL"
    )
    assert (
        grade_sonos_player_rf(ofdm_ani_level=2, phy_error_rate=45.0, ping_rtt_ms=8.0)
        == "MARGINAL"
    )
    assert (
        grade_sonos_player_rf(ofdm_ani_level=9, phy_error_rate=1126.0, ping_rtt_ms=8.4)
        == "CRITICAL"
    )
    assert (
        grade_sonos_player_rf(ofdm_ani_level=2, phy_error_rate=150.0, ping_rtt_ms=8.4)
        == "CRITICAL"
    )

    # 2. F-02 Hardware Telemetry Normalization: Fernsehecke (LF,RF) Beam has ofdm_ani_level=None
    #    Must grade by phy_error_rate and ping_rtt_ms without false-failing on None
    assert (
        grade_sonos_player_rf(ofdm_ani_level=None, phy_error_rate=0.0, ping_rtt_ms=3.1)
        in ("EXCELLENT", "GOOD")
    )
    assert (
        grade_sonos_player_rf(ofdm_ani_level=None, phy_error_rate=55.0, ping_rtt_ms=12.0)
        == "MARGINAL"
    )
    assert (
        grade_sonos_player_rf(ofdm_ani_level=None, phy_error_rate=250.0, ping_rtt_ms=12.0)
        == "CRITICAL"
    )

    # 3. ETHERNET_ROOT & ETHERNET_NODE link grading
    wz_root = PlayerTelemetryDto(
        rincon_uuid="RINCON_542A1B63FE6E01400",
        zone_name="Wohnzimmer_Bookshelf",
        connection_mode=ConnectionMode.ETHERNET_ROOT,
        ofdm_ani_level=6,
        phy_error_rate=12.5,
        designated_root=EXPECTED_STP_ROOT,
        stp_path_cost=0,
    )
    root_link_grade, _ = grade_sonos_player_link(wz_root, mesh_links=[], best_wifi_dbm=-54)
    assert root_link_grade in ("EXCELLENT", "GOOD")

    usurped_root = wz_root.model_copy(update={"designated_root": "9000.5caafd595eea"})
    usurped_grade, _ = grade_sonos_player_link(usurped_root, mesh_links=[], best_wifi_dbm=-54)
    assert usurped_grade == "CRITICAL"

    # 4. SONOSNET_MODE strictly evaluates active FORWARDING link and ignores STP 00 BLOCKING links
    elternbad = PlayerTelemetryDto(
        rincon_uuid="RINCON_347E5C31CE2801400",
        zone_name="Elternbad",
        connection_mode=ConnectionMode.SONOSNET_MODE,
        ofdm_ani_level=3,
        phy_error_rate=1.8,
        designated_root=EXPECTED_STP_ROOT,
        stp_path_cost=280,
    )
    links = [
        # Active forwarding link to Eltern with strong 57/58 dB SNR
        SonosMeshLinkDto(
            source_rincon_uuid="RINCON_347E5C31CE2801400",
            target_rincon_uuid="RINCON_347E5C3828B001400",
            channel=6,
            from_db=57,
            to_db=58,
            stp_state="FORWARDING",
        ),
        # Blocked backup link to ground floor with poor 11/14 dB SNR — MUST BE IGNORED
        SonosMeshLinkDto(
            source_rincon_uuid="RINCON_347E5C31CE2801400",
            target_rincon_uuid="RINCON_949F3EC0EEA101400",
            channel=6,
            from_db=11,
            to_db=14,
            stp_state="BLOCKING",
        ),
    ]
    eb_link_grade, eb_snr = grade_sonos_player_link(elternbad, mesh_links=links, best_wifi_dbm=-55)
    assert eb_link_grade in ("EXCELLENT", "GOOD")
    assert eb_snr == 57

    # 5. HT_SATELLITE graded on 5 GHz Ch 48 bond SNR to Beam (never penalized for missing 2.4G STP)
    rr_sat = PlayerTelemetryDto(
        rincon_uuid="RINCON_949F3E00292E01400",
        zone_name="Fernsehecke (RR)",
        connection_mode=ConnectionMode.HT_SATELLITE,
        ieee_channel=48,
        ofdm_ani_level=0,
        phy_error_rate=0.0,
        designated_root=EXPECTED_STP_ROOT,
        stp_path_cost=0,
        bonded_parent_uuid="RINCON_949F3EC0EEA101400",
    )
    ht_links = [
        SonosMeshLinkDto(
            source_rincon_uuid="RINCON_949F3E00292E01400",
            target_rincon_uuid="RINCON_949F3EC0EEA101400",
            channel=48,
            from_db=60,
            to_db=66,
            stp_state="FORWARDING",
        )
    ]
    rr_link_grade, rr_snr = grade_sonos_player_link(rr_sat, mesh_links=ht_links, best_wifi_dbm=-55)
    assert rr_link_grade in ("EXCELLENT", "GOOD")
    assert rr_snr == 60

    # 6. STATION_MODE (Nicolas on 5 GHz Ch 44) graded on room Wi-Fi RSSI, ANI, PHY err/s, and RTT
    #    Never penalized for 0 dB SonosNet peer SNR or stp_path_cost == 0
    nicolas = PlayerTelemetryDto(
        rincon_uuid="RINCON_347E5C36DE9001400",
        zone_name="Nicolas",
        connection_mode=ConnectionMode.STATION_MODE,
        ieee_channel=44,
        ofdm_ani_level=0,
        phy_error_rate=0.0,
        designated_root=EXPECTED_STP_ROOT,
        stp_path_cost=0,
        ping_rtt_ms=2.3,
    )
    nic_link_grade, _ = grade_sonos_player_link(nicolas, mesh_links=[], best_wifi_dbm=-72)
    assert nic_link_grade in ("EXCELLENT", "GOOD", "MARGINAL")
    assert nic_link_grade != "CRITICAL"


def test_all_eight_deterministic_diagnostic_rules_and_f03_stp_usurpation_guard():
    engine = DiagnosticEngine()

    # --- Case A: Wohnzimmer -> EMI_NON_WIFI_SPIKE + GHOST_GROUP_MISMATCH ---
    wz_survey = WiFiRoomSurveySchema(
        survey_slug="wz-clean-wifi",
        room_slug="wohnzimmer",
        room_name="Wohnzimmer",
        label="Post-Remediation",
        trigger_mode="HISTORICAL_SEED",
        captured_at="2026-10-05T19:00:00Z",
        best_5ghz_dbm=-54,
        best_24ghz_dbm=-52,
        best_ap_slug="galerie-ap",
        best_ap_name="Galerie EAP650",
        rogue_count=0,
        neighbor_count=0,
        grade_5ghz="EXCELLENT",
        grade_24ghz="EXCELLENT",
        wifi_health_grade="EXCELLENT",
        readings=[
            BssidReadingSchema(
                bssid="76:4C:BC:76:7C:41",
                ssid="WuTangLan-Family",
                band="5GHz",
                channel=44,
                center_channel=42,
                width_mhz=80,
                rssi_dbm=-54,
                classification="OWN_MANAGED_AP",
                ap_device_slug="galerie-ap",
                ap_name="Galerie EAP650",
                is_connected=True,
            ),
            BssidReadingSchema(
                bssid="54:2A:1B:63:FE:6F",
                ssid="SonosNet",
                band="2.4GHz",
                channel=6,
                center_channel=6,
                width_mhz=20,
                rssi_dbm=-40,
                classification="SONOSNET_MESH",
            ),
        ],
    )
    wz_players = [
        PlayerTelemetryDto(
            rincon_uuid="RINCON_542A1B63FE6E01400",
            zone_name="Wohnzimmer_Bookshelf",
            ip_address="192.168.10.230",
            connection_mode=ConnectionMode.ETHERNET_ROOT,
            ofdm_ani_level=6,
            phy_error_rate=12.5,
            designated_root=EXPECTED_STP_ROOT,
            stp_path_cost=0,
            ping_rtt_ms=0.8,
        ),
        PlayerTelemetryDto(
            rincon_uuid="RINCON_B8E937E5152A01400",
            zone_name="Wohnzimmer_Buchregal",
            ip_address="192.168.10.101",
            connection_mode=ConnectionMode.SONOSNET_MODE,
            ofdm_ani_level=9,
            phy_error_rate=1126.0,
            designated_root=EXPECTED_STP_ROOT,
            stp_path_cost=200,
            is_ghost_group=True,
            group_id="RINCON_347E5C3828B001400:44",
            coordinator_uuid="RINCON_B8E937E5152A01400",
            ping_rtt_ms=8.4,
        ),
    ]
    wz_links = [
        SonosMeshLinkDto(
            source_rincon_uuid="RINCON_B8E937E5152A01400",
            target_rincon_uuid="RINCON_542A1B63FE6E01400",
            channel=6,
            from_db=50,
            to_db=56,
            stp_state="FORWARDING",
        )
    ]
    wz_summary = engine.evaluate_room(
        room_id="rm-wz",
        room_slug="wohnzimmer",
        room_name="Wohnzimmer",
        floor_slug="erdgeschoss",
        floor_name="Erdgeschoss",
        survey=wz_survey,
        players=wz_players,
        mesh_links=wz_links,
        switch_ports=[],
        household_sonosnet_count=10,
    )
    wz_codes = {d.rule_code for d in wz_summary.diagnostics}
    assert "EMI_NON_WIFI_SPIKE" in wz_codes
    assert "GHOST_GROUP_MISMATCH" in wz_codes

    emi_diag = next(d for d in wz_summary.diagnostics if d.rule_code == "EMI_NON_WIFI_SPIKE")
    assert emi_diag.layer == "SONOS"
    assert emi_diag.severity == "CRITICAL"
    assert "Wohnzimmer_Buchregal" in emi_diag.affected_devices
    assert any(
        p.one_click_action in ("OPEN_LIVE_EMI_CONSOLE", "RUN_PHY_VELOCITY_TEST", "POLL_NOW")
        for p in emi_diag.solution_proposals
    )

    ghost_diag = next(d for d in wz_summary.diagnostics if d.rule_code == "GHOST_GROUP_MISMATCH")
    assert ghost_diag.layer == "SONOS"
    assert ghost_diag.severity == "CRITICAL"
    assert any(
        p.one_click_action == "FLUSH_GHOST_GROUPS" for p in ghost_diag.solution_proposals
    )

    # --- Case B: Nicolas / Noemi -> BASEMENT_ROOT_TRAP, STP_MULTIHOP_DETOUR (F-03 guard),
    #             SONOSNET_AIRTIME_SATURATION, WIFI_WEAK_COVERAGE, CO_CHANNEL_CONTENTION, ROGUE_TRANSMITTER_DETECTED ---
    noemi_survey_with_rogue_and_neighbor = WiFiRoomSurveySchema(
        survey_slug="noemi-test-survey",
        room_slug="noemi",
        room_name="Noemi",
        label="Noemi Contention + Rogue Test",
        trigger_mode="MANUAL_SURVEY",
        captured_at="2026-10-05T20:00:00Z",
        best_5ghz_dbm=-72,
        best_24ghz_dbm=-70,
        best_ap_slug="kitchen-ap",
        best_ap_name="Kitchen EAP650",
        rogue_count=1,
        neighbor_count=1,
        grade_5ghz="MARGINAL",
        grade_24ghz="MARGINAL",
        wifi_health_grade="MARGINAL",
        readings=[
            BssidReadingSchema(
                bssid="76:4C:BC:76:94:C1",
                ssid="WuTangLan-Family",
                band="5GHz",
                channel=40,
                center_channel=38,
                width_mhz=40,
                rssi_dbm=-72,
                classification="OWN_MANAGED_AP",
                ap_device_slug="kitchen-ap",
                ap_name="Kitchen EAP650",
                is_connected=True,
            ),
            BssidReadingSchema(
                bssid="76:4C:BC:76:94:C0",
                ssid="WuTangLan-Family",
                band="2.4GHz",
                channel=11,
                center_channel=11,
                width_mhz=20,
                rssi_dbm=-70,
                classification="OWN_MANAGED_AP",
                ap_device_slug="kitchen-ap",
                ap_name="Kitchen EAP650",
            ),
            BssidReadingSchema(
                bssid="1C:23:A2:7A:E3:7A",
                ssid="WLAN-A7C604",
                band="2.4GHz",
                channel=11,
                center_channel=11,
                width_mhz=20,
                rssi_dbm=-71,
                classification="NEIGHBOR_WIFI",
            ),
            BssidReadingSchema(
                bssid="84:16:F9:93:E9:2D",
                ssid="TP-Link_5G_93E92D",
                band="5GHz",
                channel=44,
                center_channel=42,
                width_mhz=80,
                rssi_dbm=-65,
                classification="ROGUE_OWN_RADIO",
            ),
        ],
    )
    noemi_port6 = SwitchPortRead(
        id="sp-6",
        port_number=6,
        switch_name="Netgear GS316EP",
        switch_ip="192.168.55.155",
        pvid=10,
        untagged_vlans="10",
        tagged_vlans="",
        bpdu_policy="PASS_THROUGH",
        loop_detection_disabled=True,
        patched_room_id="rm-noemi",
        connected_device_label="Noemi Wall Jack (VLAN 10)",
        is_archived=False,
    )
    noemi_detour_player = PlayerTelemetryDto(
        rincon_uuid="RINCON_542A1B64268001400",
        zone_name="Noemi",
        ip_address="192.168.10.244",
        base_mac="54:2A:1B:64:26:80",
        connection_mode=ConnectionMode.SONOSNET_MODE,
        ofdm_ani_level=5,
        phy_error_rate=22.0,
        designated_root="9000.5caafd595eea",  # Keller usurped STP Root!
        stp_path_cost=550,  # Multi-hop detour (> 450 CRITICAL)
        ping_rtt_ms=210.0,  # > 100 ms RTT -> DPC ducking risk
    )
    noemi_links = [
        SonosMeshLinkDto(
            source_rincon_uuid="RINCON_542A1B64268001400",
            target_rincon_uuid="RINCON_542A1B63FE6E01400",
            channel=6,
            from_db=18,
            to_db=19,
            stp_state="FORWARDING",
        )
    ]

    noemi_summary = engine.evaluate_room(
        room_id="rm-noemi",
        room_slug="noemi",
        room_name="Noemi",
        floor_slug="obergeschoss",
        floor_name="Obergeschoss",
        survey=noemi_survey_with_rogue_and_neighbor,
        players=[noemi_detour_player],
        mesh_links=noemi_links,
        switch_ports=[noemi_port6],
        household_sonosnet_count=11,
    )
    noemi_codes = {d.rule_code for d in noemi_summary.diagnostics}
    assert "BASEMENT_ROOT_TRAP" in noemi_codes
    assert "STP_MULTIHOP_DETOUR" in noemi_codes
    assert "SONOSNET_AIRTIME_SATURATION" in noemi_codes
    assert "WIFI_WEAK_COVERAGE" in noemi_codes
    assert "CO_CHANNEL_CONTENTION" in noemi_codes
    assert "ROGUE_TRANSMITTER_DETECTED" in noemi_codes

    # Verify Mandatory F-03 STP Root Usurpation Guard on wired VLAN 10 SolutionProposals
    detour_diag = next(
        d for d in noemi_summary.diagnostics if d.rule_code == "STP_MULTIHOP_DETOUR"
    )
    assert detour_diag.severity == "CRITICAL"
    wired_proposals = [
        p for p in detour_diag.solution_proposals if p.requires_sonosnet_disable_guard
    ]
    assert len(wired_proposals) >= 1
    guard_text = f"{wired_proposals[0].description} {wired_proposals[0].stp_guard_warning or ''}"
    assert "Port 6" in guard_text
    assert "VLAN 10" in guard_text
    assert "disable" in guard_text.lower()
    assert "9000.542a1b63fe6e" in guard_text or "4096" in guard_text


@pytest.mark.asyncio
async def test_diagnostics_endpoints_room_3_pillar_and_ping_sweep_api(tmp_path):
    db_file = tmp_path / "test_t5_diag.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"
    sonos_adapter = FakeSonosAdapter(probe_interval_sec=0.0)
    probe_adapter = FakeNetworkProbeAdapter()
    app = create_app(
        database_url=db_url,
        sonos_adapter=sonos_adapter,
        probe_adapter=probe_adapter,
    )

    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # 1. GET /api/diagnostics returns full HouseDiagnosticReportSchema
            diag_resp = await client.get("/api/diagnostics")
            assert diag_resp.status_code == 200
            report = diag_resp.json()
            assert report["designated_stp_root"].startswith("9000.542a1b63fe6e")
            assert report["is_stp_root_healthy"] is True
            assert len(report["rooms"]) == 11

            rooms_by_slug = {r["room_slug"]: r for r in report["rooms"]}

            # Wohnzimmer has EMI_NON_WIFI_SPIKE (Buchregal & Esstisch ANI 9, >700 err/s while Wi-Fi Ch 6 is clean)
            wz = rooms_by_slug["wohnzimmer"]
            assert wz["health_grade"] == "CRITICAL"
            assert wz["wifi_pillar"]["health_grade"] == "EXCELLENT"
            assert wz["sonos_pillar"]["health_grade"] == "CRITICAL"
            assert wz["wired_pillar"]["has_vlan10_wall_jack"] is True
            assert 13 in wz["wired_pillar"]["port_numbers"]
            assert any(d["rule_code"] == "EMI_NON_WIFI_SPIKE" for d in wz["diagnostics"])
            assert len(wz["solution_proposals"]) >= 2

            # Fernsehecke Beam (ofdm_ani_level=None) + LR/RR HT_SATELLITEs grade EXCELLENT/GOOD without false failure
            fe = rooms_by_slug["fernsehecke"]
            assert fe["sonos_pillar"]["health_grade"] in ("EXCELLENT", "GOOD")
            fe_players = {p["zone_name"]: p for p in fe["sonos_pillar"]["players"]}
            assert fe_players["Fernsehecke (LF,RF)"]["ofdm_ani_level"] is None
            assert fe_players["Fernsehecke (LF,RF)"]["overall_grade"] in ("EXCELLENT", "GOOD")
            assert fe_players["Fernsehecke (RR)"]["connection_mode"] == "HT_SATELLITE"
            assert fe_players["Fernsehecke (RR)"]["overall_grade"] in ("EXCELLENT", "GOOD")

            # Nicolas (STATION_MODE on 5GHz Ch 44) grades Sonos pillar EXCELLENT/GOOD, while Wi-Fi pillar flags -72 dBm
            nic = rooms_by_slug["nicolas"]
            assert nic["sonos_pillar"]["health_grade"] in ("EXCELLENT", "GOOD")
            assert nic["wired_pillar"]["has_vlan10_wall_jack"] is True
            assert 5 in nic["wired_pillar"]["port_numbers"]
            assert nic["wired_pillar"]["stp_root_guard_required"] is True
            assert any(d["rule_code"] == "WIFI_WEAK_COVERAGE" for d in nic["diagnostics"])
            assert any(p["requires_sonosnet_disable_guard"] is True for p in nic["solution_proposals"])

            # Noemi has WIFI_WEAK_COVERAGE (-72 dBm) and CO_CHANNEL_CONTENTION (WLAN-A7C604 -71 dBm on Ch 11)
            noemi = rooms_by_slug["noemi"]
            noemi_codes = {d["rule_code"] for d in noemi["diagnostics"]}
            assert "WIFI_WEAK_COVERAGE" in noemi_codes
            assert "CO_CHANNEL_CONTENTION" in noemi_codes

            # 2. GET /api/rooms/{room_slug}/diagnostics returns single-room 3-pillar breakdown
            single_resp = await client.get("/api/rooms/wohnzimmer/diagnostics")
            assert single_resp.status_code == 200
            single_wz = single_resp.json()
            assert single_wz["room_slug"] == "wohnzimmer"
            assert single_wz["wifi_pillar"]["best_5ghz_dbm"] == -54
            assert len(single_wz["sonos_pillar"]["players"]) == 3
            assert any(d["rule_code"] == "EMI_NON_WIFI_SPIKE" for d in single_wz["diagnostics"])

            # 3. POST /api/actions/ping-sweep runs latency sweep and updates ping_rtt_ms
            probe_adapter.set_latency_override("192.168.10.244", rtt_ms=145.5, jitter_ms=18.2)
            sweep_resp = await client.post("/api/actions/ping-sweep")
            assert sweep_resp.status_code == 200
            sweep_data = sweep_resp.json()
            assert sweep_data["total_probed"] == 14
            assert sweep_data["reachable_count"] == 14
            assert "Noemi" in sweep_data["dpc_risk_zones"]
            noemi_probe = next(
                r for r in sweep_data["results"] if r["zone_name"] == "Noemi"
            )
            assert noemi_probe["ping_rtt_ms"] == 145.5
            assert noemi_probe["dpc_ducking_risk"] is True

            # Verify updated ping_rtt_ms is reflected in room diagnostics
            noemi_after = (await client.get("/api/rooms/noemi/diagnostics")).json()
            assert noemi_after["sonos_pillar"]["players"][0]["ping_rtt_ms"] == 145.5
            assert any(
                d["rule_code"] == "SONOSNET_AIRTIME_SATURATION"
                for d in noemi_after["diagnostics"]
            )

            # 4. Verify GET /api/overview is enriched with active_diagnostics_count, top_diagnostic_title, and health_grade
            ov_resp = await client.get("/api/overview")
            assert ov_resp.status_code == 200
            ov = ov_resp.json()
            assert ov["active_diagnostics_count"] >= 1
            eg = next(f for f in ov["floors"] if f["slug"] == "erdgeschoss")
            ov_wz = next(r for r in eg["rooms"] if r["slug"] == "wohnzimmer")
            assert ov_wz["active_diagnostics_count"] >= 1
            assert ov_wz["top_diagnostic_title"] is not None
            assert ov_wz["health_grade"] == "CRITICAL"


@pytest.mark.asyncio
async def test_live_postgres_diagnostics_verification():
    pg_url = os.getenv(
        "TEST_POSTGRES_URL",
        "postgresql+asyncpg://sonos:sonos_network_pw@192.168.55.60:5434/sonos_network",
    )
    app = create_app(database_url=pg_url)
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/api/diagnostics")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["rooms"]) >= 11
            by_slug = {r["room_slug"]: r for r in data["rooms"]}
            assert "wohnzimmer" in by_slug
            assert "nicolas" in by_slug
            assert "noemi" in by_slug

            wz_diag = await client.get("/api/rooms/wohnzimmer/diagnostics")
            assert wz_diag.status_code == 200
            assert any(
                d["rule_code"] == "EMI_NON_WIFI_SPIKE"
                for d in wz_diag.json()["diagnostics"]
            )

            sweep = await client.post("/api/actions/ping-sweep")
            assert sweep.status_code == 200
            assert sweep.json()["total_probed"] >= 14


@pytest.mark.asyncio
async def test_code_audit_gate_fixes_cf01_cf02_cf03():
    """Verify CF-01, CF-02, and CF-03 fixes: unpolled player fallback, connection_mode preservation, and pillar DTO contracts."""
    app = create_app(
        database_url="sqlite+aiosqlite:///:memory:",
        sonos_adapter=FakeSonosAdapter(),
        probe_adapter=FakeNetworkProbeAdapter(),
    )
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Check Nicolas diagnostics has pillar summary notes, total_players, and stp_guard_note
            res = await client.get("/api/rooms/nicolas/diagnostics")
            assert res.status_code == 200
            data = res.json()
            wp = data["wifi_pillar"]
            sp = data["sonos_pillar"]
            wired = data["wired_pillar"]

            assert "summary_note" in wp
            assert wp["summary_note"] == wp["channel_summary"]
            assert "total_players" in sp
            assert sp["total_players"] == sp["player_count"]
            assert "summary_note" in sp
            assert "stp_guard_note" in wired
            assert wired["stp_guard_note"] == wired["stp_root_guard_note"]
            assert wired["stp_root_guard_required"] is True
            assert "F-03 STP Root Preservation Guard" in wired["stp_guard_note"]

            # CF-01 & CF-02: Add an unpolled player with connection_mode=None to test fallback mapping without AttributeError
            rooms_res = await client.get("/api/rooms")
            keller_room = next(r for r in rooms_res.json() if r["slug"] == "keller")
            dev_create = {
                "name": "Keller_Test_Unpolled",
                "slug": "keller-test-unpolled",
                "device_role": "SONOS_PLAYER",
                "model_name": "One SL",
                "ip_address": "192.168.10.222",
                "base_mac": "34:7E:5C:99:99:99",
                "sonosnet_bssid": "34:7E:5C:99:99:9A",
                "rincon_uuid": "RINCON_347E5C99999901400",
                "connection_mode": None,
                "room_id": keller_room["id"],
            }
            create_res = await client.post("/api/devices", json=dev_create)
            assert create_res.status_code == 201

            # Overview must succeed without AttributeError ('mac_address' or 'bssid')
            ov_res = await client.get("/api/overview")
            assert ov_res.status_code == 200
