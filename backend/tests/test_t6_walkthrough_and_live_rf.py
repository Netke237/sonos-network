import pytest
from httpx import ASGITransport, AsyncClient
from starlette.testclient import TestClient

from app.main import create_app
from app.modules.sonos_telemetry import FakeSonosAdapter
from app.modules.wifi_omada import FakeWiFiAdapter


@pytest.fixture
def test_app():
    app = create_app(
        database_url="sqlite+aiosqlite:///:memory:",
        sonos_adapter=FakeSonosAdapter(),
        wifi_adapter=FakeWiFiAdapter(),
    )
    return app


@pytest.mark.asyncio
async def test_compute_survey_delta_between_baseline_and_sanitized(test_app):
    """T6: GET /api/rooms/{room_slug}/surveys/delta computes structured SurveyComparisonDelta."""
    async with test_app.router.lifespan_context(test_app):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Query delta for room 'nicolas' comparing 19 Sep baseline vs 08 Oct sanitized survey
            resp = await client.get(
                "/api/rooms/nicolas/surveys/delta?baseline_slug=nicolas-19-sep-2026-baseline&target_slug=nicolas-08-oct-2026-sanitized"
            )
            assert resp.status_code == 200, resp.text
            delta = resp.json()

            assert delta["room_slug"] == "nicolas"
            assert delta["baseline_survey_slug"] == "nicolas-19-sep-2026-baseline"
            assert delta["target_survey_slug"] == "nicolas-08-oct-2026-sanitized"

            # Verify Wi-Fi deltas: Galerie EAP650 was -70 dBm in baseline and -72 dBm post-remediation
            assert delta["baseline_5ghz_dbm"] == -70
            assert delta["target_5ghz_dbm"] == -72
            assert delta["delta_5ghz_dbm"] == -2
            assert delta["target_best_ap_name"] == "Galerie EAP650"

            # Verify BSSID diff table has readings with delta_rssi_dbm
            bssid_deltas = delta["bssid_deltas"]
            assert len(bssid_deltas) > 0
            galerie_family_5g = next(
                (b for b in bssid_deltas if b["bssid"] == "76:4C:BC:76:7C:41"),
                None,
            )
            assert galerie_family_5g is not None
            assert galerie_family_5g["delta_rssi_dbm"] == -5

            # Verify rogue EAP330 vanished in sanitized survey
            rogue_eap = next(
                (b for b in bssid_deltas if b["bssid"] == "84:16:F9:93:E9:2D"),
                None,
            )
            assert rogue_eap is not None
            assert rogue_eap["is_vanished"] is True

            # Verify narrative summary is populated
            assert len(delta["summary_narrative"]) > 0


@pytest.mark.asyncio
async def test_compute_survey_delta_default_picks_oldest_and_newest(test_app):
    """T6: If no query params provided, delta compares baseline vs latest survey."""
    async with test_app.router.lifespan_context(test_app):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/api/rooms/wohnzimmer/surveys/delta")
            assert resp.status_code == 200, resp.text
            delta = resp.json()
            assert delta["room_slug"] == "wohnzimmer"
            assert delta["baseline_survey_slug"] is not None
            assert delta["target_survey_slug"] is not None
            assert "summary_narrative" in delta
            assert delta["delta_phy_error_rate"] is not None
            assert delta["delta_phy_error_rate"] < 0
            assert delta["sonos_improved"] is True


def test_websocket_live_rf_streaming_and_isolated_cursor(test_app):
    """T6: WS /api/ws/live-rf streams live samples and maintains isolated consumer_id."""
    with TestClient(test_app) as test_client:
        with test_client.websocket_connect(
            "/api/ws/live-rf?room_slug=all&interval_sec=0.01&max_iterations=2"
        ) as ws:
            frame1 = ws.receive_json()
            assert "consumer_id" in frame1
            assert frame1["consumer_id"].startswith("ws-")
            assert len(frame1["samples"]) == 14

            # Verify sample fields
            first_sample = frame1["samples"][0]
            assert "zone_name" in first_sample
            assert "rincon_uuid" in first_sample
            assert "phy_error_rate" in first_sample

            frame2 = ws.receive_json()
            assert frame2["consumer_id"] == frame1["consumer_id"]
            assert len(frame2["samples"]) == 14
