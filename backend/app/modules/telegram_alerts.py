from __future__ import annotations

import logging
import os
from typing import Protocol
import httpx

from app.modules.watchdog_engine import WatchdogAlert

logger = logging.getLogger("sonos_network.telegram_alerts")


def _escape_md(text: str) -> str:
    """Escapes underscores to prevent Telegram entity parsing errors on zone names / RINCON UUIDs."""
    return text.replace("_", "\\_")


def format_telegram_alert_card(alert: WatchdogAlert) -> str:
    escaped_title = _escape_md(alert.title)
    if alert.cleared:
        header = f"✅ *[RESOLVED] {escaped_title}*"
    elif alert.auto_healed:
        header = f"⚡ *[AUTO-HEALED] {escaped_title}*"
    elif alert.severity == "CRITICAL":
        header = f"🚨 *[CRITICAL] {escaped_title}*"
    elif alert.severity == "MARGINAL":
        header = f"⚠️ *[WARNING] {escaped_title}*"
    else:
        header = f"ℹ️ *[INFO] {escaped_title}*"

    lines = [
        header,
        "",
        f"📍 *Entity:* {_escape_md(alert.entity_id)}",
        f"⏱ *Time:* {alert.detected_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"📝 *Detail:* {_escape_md(alert.description)}",
        f"🛠 *Action:* {_escape_md(alert.action_required)}",
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
            "parse_mode": "Markdown",
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
            elif resp.status_code == 400 and "can't parse entities" in resp.text:
                # Fallback: Retry as plain text without parse_mode if formatting broke
                logger.warning("Telegram parse_mode failed, retrying plain text payload...")
                plain_payload = {"chat_id": self.chat_id, "text": text}
                if self._http_client is not None:
                    resp_retry = await self._http_client.post(url, json=plain_payload, timeout=10.0)
                else:
                    async with httpx.AsyncClient() as client:
                        resp_retry = await client.post(url, json=plain_payload, timeout=10.0)
                if resp_retry.status_code == 200 and resp_retry.json().get("ok") is True:
                    logger.info("Telegram plain text fallback delivered successfully.")
                    return True
                return False
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
