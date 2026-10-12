import os
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.modules.wifi_omada import (
    FakeWiFiAdapter,
    OmadaAndAdbWiFiAdapter,
    classify_bssid,
    grade_wifi_dbm,
)


def test_bssid_classification_f01_exact_hardware_rules():
    # 1. OWN_MANAGED_AP: Galerie EAP650 (lower 5 octets :4C:BC:76:7C:40 2.4G / :4C:BC:76:7C:41 5G)
    # across all TP-Link virtual VLAN first-octet mutations (6C base, 72 Admin, 76 Family, 7A Guest, 7E IOT, 82 hidden)
    for prefix in ("6C", "72", "76", "7A", "7E", "82"):
        res_24 = classify_bssid(f"{prefix}:4C:BC:76:7C:40", "WuTangLan-Family")
        assert res_24.classification == "OWN_MANAGED_AP"
        assert res_24.ap_device_slug == "galerie-ap"
        assert res_24.ap_name == "Galerie EAP650"
        assert res_24.radio_band == "2.4GHz"

        res_5 = classify_bssid(f"{prefix}:4c:bc:76:7c:41", "Admin")
        assert res_5.classification == "OWN_MANAGED_AP"
        assert res_5.ap_device_slug == "galerie-ap"
        assert res_5.ap_name == "Galerie EAP650"
        assert res_5.radio_band == "5GHz"

    # 2. OWN_MANAGED_AP: Kitchen EAP650 (lower 5 octets :4C:BC:76:94:C0 2.4G / :4C:BC:76:94:C1 5G)
    for prefix in ("6C", "72", "76", "7A", "7E", "82"):
        res_k24 = classify_bssid(f"{prefix}:4C:BC:76:94:C0", "WuTangLan-IOT")
        assert res_k24.classification == "OWN_MANAGED_AP"
        assert res_k24.ap_device_slug == "kitchen-ap"
        assert res_k24.ap_name == "Kitchen EAP650"
        assert res_k24.radio_band == "2.4GHz"

        res_k5 = classify_bssid(f"{prefix}:4C:BC:76:94:C1", "WuTangLan-Guest")
        assert res_k5.classification == "OWN_MANAGED_AP"
        assert res_k5.ap_device_slug == "kitchen-ap"
        assert res_k5.ap_name == "Kitchen EAP650"
        assert res_k5.radio_band == "5GHz"

    # 3. SONOSNET_MESH: All 14 household SonosNet BSSIDs (BaseMAC + 1)
    sonos_bssids = [
        "54:2A:1B:63:FE:6F",
        "B8:E9:37:E6:09:85",
        "B8:E9:37:E5:15:2B",
        "94:9F:3E:C0:EE:A2",
        "5C:AA:FD:49:0C:CB",
        "94:9F:3E:00:29:2F",
        "5C:AA:FD:59:5E:EB",
        "34:7E:5C:38:26:E3",
        "34:7E:5C:35:B0:F5",
        "34:7E:5C:35:B2:C1",
        "54:2A:1B:64:26:81",
        "34:7E:5C:36:DE:91",
        "34:7E:5C:38:28:B1",
        "34:7E:5C:31:CE:29",
    ]
    for sb in sonos_bssids:
        res_s = classify_bssid(sb, None)
        assert res_s.classification == "SONOSNET_MESH"
        assert res_s.ap_device_slug is None

    # 4. ROGUE_OWN_RADIO: Standalone EAP330, Fritzbox 6660 "WuTangLan", Epson ET-4850 Wi-Fi Direct
    eap330_cases = [
        ("84:16:F9:93:E9:2B", None),
        ("84:16:F9:93:E9:2C", "[Hidden SSID]"),
        ("84:16:F9:93:E9:2D", "TP-Link_5G_93E92D"),
        ("86:16:F9:BF:E9:2D", "WuTangLan-Family"),
        ("86:16:F9:BF:E9:2E", "WuTangLan-Guest"),
        ("86:16:F9:BF:E9:2F", "WuTangLan-IOT"),
        ("AA:BB:CC:DD:EE:01", "TP-Link_5G_93E92D"),
    ]
    for bssid, ssid in eap330_cases:
        assert classify_bssid(bssid, ssid).classification == "ROGUE_OWN_RADIO"

    fritz_cases = [
        ("0C:72:74:00:63:9A", "WuTangLan"),
        ("0C:72:74:00:63:9B", "WuTangLan"),
        ("AA:BB:CC:00:11:22", "WuTangLan"),
    ]
    for bssid, ssid in fritz_cases:
        assert classify_bssid(bssid, ssid).classification == "ROGUE_OWN_RADIO"

    epson_cases = [
        ("6A:55:D4:7D:0B:9B", "DIRECT-f1-EPSON-ET-4850"),
        ("12:34:56:78:9A:BC", "DIRECT-ab-EPSON-ET-4850"),
    ]
    for bssid, ssid in epson_cases:
        assert classify_bssid(bssid, ssid).classification == "ROGUE_OWN_RADIO"

    # 5. NEIGHBOR_WIFI: External BSSIDs
    neighbor_cases = [
        ("1C:23:A2:7A:E3:7A", "WLAN-A7C604"),
        ("DC:A6:33:43:EC:0C", "Vodafone-DD14"),
        ("6E:F2:D8:E7:FA:7F", "DIRECT-Ub7F-TS5100series"),
        ("0C:EF:15:5E:97:49", "Tapo_Bulb_9749"),
    ]
    for bssid, ssid in neighbor_cases:
        res_n = classify_bssid(bssid, ssid)
        assert res_n.classification == "NEIGHBOR_WIFI"
        assert res_n.ap_device_slug is None


def test_wifi_health_grading_thresholds():
    assert grade_wifi_dbm(-45) == "EXCELLENT"
    assert grade_wifi_dbm(-55) == "EXCELLENT"
    assert grade_wifi_dbm(-56) == "GOOD"
    assert grade_wifi_dbm(-67) == "GOOD"
    assert grade_wifi_dbm(-68) == "MARGINAL"
    assert grade_wifi_dbm(-75) == "MARGINAL"
    assert grade_wifi_dbm(-76) == "CRITICAL"
    assert grade_wifi_dbm(None) == "CRITICAL"


@pytest.mark.asyncio
async def test_omada_adapter_online_and_graceful_degradation():
    # 1. FakeWiFiAdapter returns active Galerie EAP650 (Ch 1 @ 20MHz, Ch 44 @ 80MHz)
    #    and Kitchen EAP650 (Ch 11 @ 20MHz, Ch 40 @ 40MHz) + client association for Nicolas
    fake = FakeWiFiAdapter()
    snap = await fake.collect_wifi_infrastructure()
    assert snap.omada_reachable is True
    assert len(snap.radios) == 4
    by_key = {r.radio_key: r for r in snap.radios}
    assert by_key["galerie-ap-24ghz"].channel == 1
    assert by_key["galerie-ap-24ghz"].width_mhz == 20
    assert by_key["galerie-ap-5ghz"].channel == 44
    assert by_key["galerie-ap-5ghz"].width_mhz == 80
    assert by_key["kitchen-ap-24ghz"].channel == 11
    assert by_key["kitchen-ap-24ghz"].width_mhz == 20
    assert by_key["kitchen-ap-5ghz"].channel == 40
    assert by_key["kitchen-ap-5ghz"].width_mhz == 40
    assert any(c.room_slug == "nicolas" and c.channel == 44 for c in snap.clients)

    # 2. OmadaAndAdbWiFiAdapter degrades gracefully when :8043 raises ConnectionError / Timeout
    def offline_http_caller(url: str, timeout: float = 2.0) -> str:
        raise OSError("Connection refused to https://192.168.55.60:8043")

    offline_adapter = OmadaAndAdbWiFiAdapter(
        controller_url="https://192.168.55.60:8043",
        http_caller=offline_http_caller,
    )
    degraded_snap = await offline_adapter.collect_wifi_infrastructure()
    assert degraded_snap.omada_reachable is False
    assert degraded_snap.controller_status == "DEGRADED_OFFLINE"
    assert len(degraded_snap.radios) == 4


@pytest.mark.asyncio
async def test_wifi_infrastructure_and_room_surveys_api_and_post_ingestion(tmp_path):
    db_file = tmp_path / "test_t3_wifi.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"
    wifi_adapter = FakeWiFiAdapter()
    app = create_app(database_url=db_url, wifi_adapter=wifi_adapter)

    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # 1. GET /api/wifi/infrastructure
            infra_resp = await client.get("/api/wifi/infrastructure")
            assert infra_resp.status_code == 200
            infra = infra_resp.json()
            assert infra["omada_reachable"] is True
            assert len(infra["radios"]) == 4

            # 2. GET /api/rooms/nicolas/surveys returns both Oct 8 sanitized and Sep 19 baseline surveys
            nic_resp = await client.get("/api/rooms/nicolas/surveys")
            assert nic_resp.status_code == 200
            nic_surveys = nic_resp.json()
            assert len(nic_surveys) >= 2
            latest_nic = nic_surveys[0]
            baseline_nic = nic_surveys[-1]
            assert "08-oct-2026-sanitized" in latest_nic["survey_slug"]
            assert latest_nic["best_5ghz_dbm"] == -72
            assert latest_nic["best_ap_name"] == "Galerie EAP650"
            assert latest_nic["rogue_count"] == 0
            assert latest_nic["neighbor_count"] == 0
            assert latest_nic["grade_5ghz"] == "MARGINAL"
            assert len(latest_nic["readings"]) == 8

            assert "19-sep-2026-baseline" in baseline_nic["survey_slug"]
            assert baseline_nic["rogue_count"] >= 3
            assert any(
                r["ssid"] == "TP-Link_5G_93E92D"
                and r["classification"] == "ROGUE_OWN_RADIO"
                for r in baseline_nic["readings"]
            )

            # 3. POST /api/rooms/noemi/surveys ingests a new survey, classifies BSSIDs, and updates overview
            post_payload = {
                "label": "Post-AP Relocation Walkthrough",
                "trigger_mode": "MANUAL_SURVEY",
                "connected_bssid": "76:4C:BC:76:7C:41",
                "link_speed_mbps": 1201,
                "readings": [
                    {
                        "bssid": "76:4C:BC:76:7C:41",
                        "ssid": "WuTangLan-Family",
                        "band": "5GHz",
                        "channel": 44,
                        "center_channel": 42,
                        "width_mhz": 80,
                        "rssi_dbm": -53,
                    },
                    {
                        "bssid": "76:4C:BC:76:94:C0",
                        "ssid": "WuTangLan-Family",
                        "band": "2.4GHz",
                        "channel": 11,
                        "center_channel": 11,
                        "width_mhz": 20,
                        "rssi_dbm": -62,
                    },
                    {
                        "bssid": "54:2A:1B:64:26:81",
                        "ssid": "SonosNet",
                        "band": "2.4GHz",
                        "channel": 6,
                        "center_channel": 6,
                        "width_mhz": 20,
                        "rssi_dbm": -46,
                    },
                    {
                        "bssid": "1C:23:A2:7A:E3:7A",
                        "ssid": "WLAN-A7C604",
                        "band": "2.4GHz",
                        "channel": 11,
                        "center_channel": 11,
                        "width_mhz": 20,
                        "rssi_dbm": -71,
                    },
                ],
            }
            post_resp = await client.post("/api/rooms/noemi/surveys", json=post_payload)
            assert post_resp.status_code == 201
            created = post_resp.json()
            assert created["room_slug"] == "noemi"
            assert created["best_5ghz_dbm"] == -53
            assert created["best_24ghz_dbm"] == -62
            assert created["best_ap_name"] == "Galerie EAP650"
            assert created["grade_5ghz"] == "EXCELLENT"
            assert created["grade_24ghz"] == "GOOD"
            assert created["wifi_health_grade"] == "EXCELLENT"
            assert created["rogue_count"] == 0
            assert created["neighbor_count"] == 1
            classifications = {r["bssid"]: r["classification"] for r in created["readings"]}
            assert classifications["76:4C:BC:76:7C:41"] == "OWN_MANAGED_AP"
            assert classifications["76:4C:BC:76:94:C0"] == "OWN_MANAGED_AP"
            assert classifications["54:2A:1B:64:26:81"] == "SONOSNET_MESH"
            assert classifications["1C:23:A2:7A:E3:7A"] == "NEIGHBOR_WIFI"

            # 3b. Verify offline store-and-forward captured_at timestamp preservation
            historical_ts = "2026-10-12T19:30:00Z"
            survey_offline_payload = {
                "label": "Offline Store-and-Forward Basement Survey",
                "trigger_mode": "STORE_AND_FORWARD",
                "captured_at": historical_ts,
                "readings": [
                    {
                        "bssid": "76:4C:BC:76:94:C0",
                        "ssid": "WuTangLan-Family",
                        "band": "2.4GHz",
                        "channel": 11,
                        "rssi_dbm": -68,
                    }
                ],
            }
            resp_off = await client.post("/api/rooms/noemi/surveys", json=survey_offline_payload)
            assert resp_off.status_code == 201
            created_off = resp_off.json()
            assert created_off["captured_at"].startswith("2026-10-12T19:30:00")
            assert created_off["trigger_mode"] == "STORE_AND_FORWARD"

            # 4. Verify GET /api/overview reflects the enriched Wi-Fi survey fields on Noemi and Nicolas
            ov_resp = await client.get("/api/overview")
            assert ov_resp.status_code == 200
            ov = ov_resp.json()
            og = next(f for f in ov["floors"] if f["slug"] == "obergeschoss")
            noemi_room = next(r for r in og["rooms"] if r["slug"] == "noemi")
            assert noemi_room["best_5ghz_dbm"] == -53
            assert noemi_room["best_24ghz_dbm"] == -62
            assert noemi_room["best_ap_name"] == "Galerie EAP650"
            assert noemi_room["link_speed_mbps"] == 1201
            assert noemi_room["rogue_count"] == 0
            assert noemi_room["neighbor_count"] == 1
            assert noemi_room["wifi_health_grade"] == "EXCELLENT"


@pytest.mark.asyncio
async def test_all_11_rooms_seeded_idempotently_in_live_postgres():
    pg_url = os.getenv(
        "TEST_POSTGRES_URL",
        "postgresql+asyncpg://sonos:sonos_network_pw@192.168.55.60:5434/sonos_network",
    )
    app = create_app(database_url=pg_url)
    expected_rooms = [
        "elternbad",
        "elternschlafzimmer",
        "noemi",
        "noah",
        "nicolas",
        "galerie",
        "bueroecke",
        "wohnzimmer",
        "fernsehecke",
        "kueche",
        "keller",
    ]
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            for room_slug in expected_rooms:
                resp = await client.get(f"/api/rooms/{room_slug}/surveys")
                assert resp.status_code == 200, f"Failed for {room_slug}"
                surveys = resp.json()
                slugs = [s["survey_slug"] for s in surveys]
                assert any("19-sep-2026-baseline" in s for s in slugs), f"Missing Sep baseline for {room_slug}"
                assert any(
                    "04-oct-2026-sanitized" in s or "08-oct-2026-sanitized" in s
                    for s in slugs
                ), f"Missing Oct sanitized for {room_slug}"
