from datetime import datetime, timezone
import pytest
from httpx import AsyncClient, ASGITransport
import httpx
import json

from app.main import app
from app.modules.watchdog_engine import WatchdogAlert, WatchdogAnomalyType
from app.modules.telegram_alerts import TelegramAlertAdapter, format_telegram_alert_card


def test_format_telegram_alert_card():
    now = datetime(2026, 10, 13, 14, 0, 0, tzinfo=timezone.utc)
    alert = WatchdogAlert(
        incident_key="STP_ROOT_USURPED:household",
        anomaly_type=WatchdogAnomalyType.STP_ROOT_USURPED,
        severity="CRITICAL",
        title="STP Root Bridge Usurped: 9000.5caafd595eea",
        description="Observed STP Designated Root usurped Wohnzimmer_Bookshelf.",
        action_required="Unplug Ethernet from Keller Play:3.",
        entity_id="household",
        detected_at=now,
    )

    card = format_telegram_alert_card(alert)
    assert "🚨 <b>[CRITICAL] STP Root Bridge Usurped: 9000.5caafd595eea</b>" in card
    assert "📍 <b>Entity:</b> <code>household</code>" in card
    assert "📝 <b>Detail:</b> Observed STP Designated Root usurped Wohnzimmer_Bookshelf." in card
    assert "🛠 <b>Action:</b> Unplug Ethernet from Keller Play:3." in card


def test_format_telegram_alert_card_with_underscores_and_html_special_chars():
    now = datetime(2026, 10, 13, 14, 0, 0, tzinfo=timezone.utc)
    alert = WatchdogAlert(
        incident_key="EMI_BURST:Wohnzimmer_Buchregal",
        anomaly_type=WatchdogAnomalyType.EMI_BURST,
        severity="CRITICAL",
        title="Severe 2.4 GHz EMI Burst on Wohnzimmer_Buchregal",
        description="Player 'Wohnzimmer_Buchregal' recorded OFDM ANI 9 and 1126.0 PHY err/s <high>",
        action_required="Inspect dock & power supplies; relocate speaker.",
        entity_id="Wohnzimmer_Buchregal",
        detected_at=now,
    )

    card = format_telegram_alert_card(alert)
    # Underscores are preserved, HTML tags escaped
    assert "<code>Wohnzimmer_Buchregal</code>" in card
    assert "&lt;high&gt;" in card
    assert "dock &amp; power supplies" in card


@pytest.mark.asyncio
async def test_telegram_adapter_unconfigured_graceful_degradation():
    adapter = TelegramAlertAdapter(bot_token="", chat_id="", enabled=True)
    assert adapter.is_configured() is False

    alert = WatchdogAlert(
        incident_key="GHOST_GROUP:Küche",
        anomaly_type=WatchdogAnomalyType.GHOST_GROUP,
        severity="CRITICAL",
        title="Ghost Group on Küche",
        description="Ghost group detected",
        action_required="Flush group",
        entity_id="Küche",
    )

    # Must return False and not raise any exception
    sent = await adapter.send_alert(alert)
    assert sent is False


@pytest.mark.asyncio
async def test_telegram_adapter_send_success():
    bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    chat_id = "987654321"

    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = json.loads(request.content.decode("utf-8"))
        assert payload["parse_mode"] == "HTML"
        assert payload["chat_id"] == chat_id
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 42}})

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = TelegramAlertAdapter(
            bot_token=bot_token,
            chat_id=chat_id,
            enabled=True,
            http_client=client,
        )
        assert adapter.is_configured() is True

        alert = WatchdogAlert(
            incident_key="GHOST_GROUP:Wohnzimmer_Bookshelf",
            anomaly_type=WatchdogAnomalyType.GHOST_GROUP,
            severity="CRITICAL",
            title="Ghost Group on Wohnzimmer_Bookshelf",
            description="Ghost group detected",
            action_required="Flush group",
            entity_id="Wohnzimmer_Bookshelf",
        )

        sent = await adapter.send_alert(alert)
        assert sent is True


@pytest.mark.asyncio
async def test_telegram_adapter_http_error_graceful_degradation():
    bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    chat_id = "987654321"

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"ok": False, "description": "Internal Server Error"})

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = TelegramAlertAdapter(
            bot_token=bot_token,
            chat_id=chat_id,
            enabled=True,
            http_client=client,
        )
        alert = WatchdogAlert(
            incident_key="GHOST_GROUP:Küche",
            anomaly_type=WatchdogAnomalyType.GHOST_GROUP,
            severity="CRITICAL",
            title="Ghost Group on Küche",
            description="Ghost group detected",
            action_required="Flush group",
            entity_id="Küche",
        )

        sent = await adapter.send_alert(alert)
        assert sent is False


@pytest.mark.asyncio
async def test_watchdog_fastapi_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. GET /api/watchdog/status
        res = await client.get("/api/watchdog/status")
        assert res.status_code == 200
        data = res.json()
        assert "is_healthy" in data
        assert "active_incidents_count" in data
        assert "auto_heal_enabled" in data
        assert "telegram_configured" in data

        # 2. POST /api/watchdog/toggle-auto-heal
        toggle_res = await client.post("/api/watchdog/toggle-auto-heal?enabled=false")
        assert toggle_res.status_code == 200
        assert toggle_res.json()["auto_heal_enabled"] is False

        toggle_res2 = await client.post("/api/watchdog/toggle-auto-heal?enabled=true")
        assert toggle_res2.status_code == 200
        assert toggle_res2.json()["auto_heal_enabled"] is True

        # 3. POST /api/watchdog/test-alert
        test_res = await client.post("/api/watchdog/test-alert")
        assert test_res.status_code == 200
        test_data = test_res.json()
        assert test_data["status"] == "ok"
        assert "delivered" in test_data
