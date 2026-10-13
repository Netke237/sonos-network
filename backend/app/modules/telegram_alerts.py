from __future__ import annotations

import html
import logging
import os
from typing import Protocol
import httpx

from app.modules.watchdog_engine import WatchdogAlert

logger = logging.getLogger("sonos_network.telegram_alerts")


def format_telegram_alert_card(alert: WatchdogAlert) -> str:
    escaped_title = html.escape(alert.title)
    if alert.cleared:
        header = f"✅ <b>[RESOLVED] {escaped_title}</b>"
    elif alert.auto_healed:
        header = f"⚡ <b>[AUTO-HEALED] {escaped_title}</b>"
    elif alert.severity == "CRITICAL":
        header = f"🚨 <b>[CRITICAL] {escaped_title}</b>"
    elif alert.severity == "MARGINAL":
        header = f"⚠️ <b>[WARNING] {escaped_title}</b>"
    else:
        header = f"ℹ️ <b>[INFO] {escaped_title}</b>"

    lines = [
        header,
        "",
        f"📍 <b>Entity:</b> <code>{html.escape(alert.entity_id)}</code>",
        f"⏱ <b>Time:</b> {alert.detected_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"📝 <b>Detail:</b> {html.escape(alert.description)}",
        f"🛠 <b>Action:</b> {html.escape(alert.action_required)}",
    ]
    return "\n".join(lines)


class AlertChannelPort(Protocol):
    def is_configured(self) -> bool: ...

    async def send_alert(self, alert: WatchdogAlert) -> bool: ...

    async def send_raw_message(self, text: str) -> bool: ...


class TelegramAlertAdapter:
    def __init__(
        self,
        bot_token: str | None = None,
        chat_id: str | None = None,
        enabled: bool | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.bot_token = bot_token if bot_token is not None else os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.chat_id = chat_id if chat_id is not None else os.getenv("TELEGRAM_CHAT_ID", "").strip()
        if enabled is not None:
            self.enabled = enabled
        else:
            self.enabled = os.getenv("TELEGRAM_ALERTS_ENABLED", "true").strip().lower() in ("true", "1", "yes")
        self._http_client = http_client

    def is_configured(self) -> bool:
        return bool(self.enabled and self.bot_token and self.chat_id)

    async def send_raw_message(self, text: str) -> bool:
        if not self.is_configured():
            logger.info("Telegram alerting skipped: channel not configured or disabled.")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
        }

        try:
            if self._http_client is not None:
                resp = await self._http_client.post(url, json=payload, timeout=10.0)
            else:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(url, json=payload, timeout=10.0)

            if resp.status_code == 200 and resp.json().get("ok") is True:
                logger.info("Telegram notification card delivered successfully.")
                return True
            else:
                logger.warning(
                    "Telegram API responded with error status %d: %s",
                    resp.status_code,
                    resp.text,
                )
                return False
        except Exception as exc:
            logger.warning("Failed to dispatch Telegram alert card: %s", exc)
            return False

    async def send_alert(self, alert: WatchdogAlert) -> bool:
        card = format_telegram_alert_card(alert)
        return await self.send_raw_message(card)
