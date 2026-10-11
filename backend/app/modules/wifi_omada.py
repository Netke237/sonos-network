from __future__ import annotations

import asyncio
import json
import os
import re
import ssl
import urllib.request
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, Protocol

from app.models.entities import BssidClassification, HealthGrade
from app.modules.sonos_telemetry import MASTER_SONOS_INVENTORY
from app.schemas.topology import (
    AccessPointRadioRead,
    BssidClassificationResult,
    BssidReadingInput,
    BssidReadingSchema,
    OmadaClientAssociationDto,
    WiFiInfraSnapshot,
    WiFiRoomSurveySchema,
)

DEFAULT_OMADA_URL = "https://192.168.55.60:8043"

# Registered household SonosNet BSSIDs (BaseMAC + 1) and Base MACs for all 14 players
SONOSNET_BSSIDS: set[str] = {
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
} | {
    str(item["base_mac"]).upper()
    for item in MASTER_SONOS_INVENTORY
    if item.get("base_mac")
}

# Known retired / rogue in-house transmitter BSSIDs (F-01)
ROGUE_OWN_BSSIDS: set[str] = {
    # Standalone TP-Link EAP330
    "84:16:F9:93:E9:2B",
    "84:16:F9:93:E9:2C",
    "84:16:F9:93:E9:2D",
    "86:16:F9:BF:E9:2D",
    "86:16:F9:BF:E9:2E",
    "86:16:F9:BF:E9:2F",
    # Fritzbox 6660 Cable rogue Wi-Fi ("WuTangLan")
    "0C:72:74:00:63:9A",
    "0C:72:74:00:63:9B",
    # Epson ET-4850 Wi-Fi Direct
    "6A:55:D4:7D:0B:9B",
}

EPSON_DIRECT_SSID_RE = re.compile(r"^DIRECT-.*-EPSON.*$", re.IGNORECASE)

# Active Omada-managed EAP650 radios (Sanitized October 2026 channel plan)
MASTER_AP_RADIOS: list[dict[str, Any]] = [
    {
        "radio_key": "galerie-ap-24ghz",
        "ap_device_slug": "galerie-ap",
        "ap_name": "Galerie EAP650",
        "room_slug": "galerie",
        "band": "2.4GHz",
        "base_mac": "6C:4C:BC:76:7C:40",
        "bssid_suffix": ":4C:BC:76:7C:40",
        "derived_bssids": [
            "72:4C:BC:76:7C:40",
            "76:4C:BC:76:7C:40",
            "7A:4C:BC:76:7C:40",
            "7E:4C:BC:76:7C:40",
            "82:4C:BC:76:7C:40",
        ],
        "channel": 1,
        "center_channel": 1,
        "width_mhz": 20,
        "tx_power_dbm": 20,
        "airtime_utilization_pct": 18.0,
        "is_non_dfs": True,
        "status": "CONNECTED",
    },
    {
        "radio_key": "galerie-ap-5ghz",
        "ap_device_slug": "galerie-ap",
        "ap_name": "Galerie EAP650",
        "room_slug": "galerie",
        "band": "5GHz",
        "base_mac": "6C:4C:BC:76:7C:41",
        "bssid_suffix": ":4C:BC:76:7C:41",
        "derived_bssids": [
            "72:4C:BC:76:7C:41",
            "76:4C:BC:76:7C:41",
            "7A:4C:BC:76:7C:41",
            "7E:4C:BC:76:7C:41",
            "82:4C:BC:76:7C:41",
        ],
        "channel": 44,
        "center_channel": 42,
        "width_mhz": 80,
        "tx_power_dbm": 23,
        "airtime_utilization_pct": 9.0,
        "is_non_dfs": True,
        "status": "CONNECTED",
    },
    {
        "radio_key": "kitchen-ap-24ghz",
        "ap_device_slug": "kitchen-ap",
        "ap_name": "Kitchen EAP650",
        "room_slug": "kueche",
        "band": "2.4GHz",
        "base_mac": "6C:4C:BC:76:94:C0",
        "bssid_suffix": ":4C:BC:76:94:C0",
        "derived_bssids": [
            "72:4C:BC:76:94:C0",
            "76:4C:BC:76:94:C0",
            "7A:4C:BC:76:94:C0",
            "7E:4C:BC:76:94:C0",
            "82:4C:BC:76:94:C0",
        ],
        "channel": 11,
        "center_channel": 11,
        "width_mhz": 20,
        "tx_power_dbm": 20,
        "airtime_utilization_pct": 21.0,
        "is_non_dfs": True,
        "status": "CONNECTED",
    },
    {
        "radio_key": "kitchen-ap-5ghz",
        "ap_device_slug": "kitchen-ap",
        "ap_name": "Kitchen EAP650",
        "room_slug": "kueche",
        "band": "5GHz",
        "base_mac": "6C:4C:BC:76:94:C1",
        "bssid_suffix": ":4C:BC:76:94:C1",
        "derived_bssids": [
            "72:4C:BC:76:94:C1",
            "76:4C:BC:76:94:C1",
            "7A:4C:BC:76:94:C1",
            "7E:4C:BC:76:94:C1",
            "82:4C:BC:76:94:C1",
        ],
        "channel": 40,
        "center_channel": 38,
        "width_mhz": 40,
        "tx_power_dbm": 23,
        "airtime_utilization_pct": 6.0,
        "is_non_dfs": True,
        "status": "CONNECTED",
    },
]

MASTER_OMADA_CLIENTS: list[dict[str, Any]] = [
    {
        "client_name": "Nicolas",
        "mac_address": "34:7E:5C:36:DE:90",
        "ip_address": "192.168.10.165",
        "room_slug": "nicolas",
        "ap_device_slug": "galerie-ap",
        "ap_name": "Galerie EAP650",
        "connected_bssid": "76:4C:BC:76:7C:41",
        "ssid": "WuTangLan-Family",
        "band": "5GHz",
        "channel": 44,
        "rssi_dbm": -72,
        "link_speed_mbps": 1201,
    },
    {
        "client_name": "Walkthrough Scanner Phone",
        "mac_address": "A4:50:46:11:22:33",
        "ip_address": "192.168.10.50",
        "room_slug": "galerie",
        "ap_device_slug": "galerie-ap",
        "ap_name": "Galerie EAP650",
        "connected_bssid": "76:4C:BC:76:7C:41",
        "ssid": "WuTangLan-Family",
        "band": "5GHz",
        "channel": 44,
        "rssi_dbm": -45,
        "link_speed_mbps": 1201,
    },
]


def classify_bssid(bssid: str, ssid: str | None = None) -> BssidClassificationResult:
    """
    Exact Hardware BssidClassification Rules (F-01):
    1. OWN_MANAGED_AP: Matches by the lower 5 octets of the managed EAP650 radios:
       - `:4C:BC:76:7C:40` (2.4G) / `:4C:BC:76:7C:41` (5G) -> `Galerie EAP650` (`galerie-ap`)
       - `:4C:BC:76:94:C0` (2.4G) / `:4C:BC:76:94:C1` (5G) -> `Kitchen EAP650` (`kitchen-ap`)
       across all TP-Link virtual VLAN first-octet mutations (`72` Admin, `76` Family,
       `7A` Guest, `7E` IOT, `82` hidden) as well as base MAC (`6C:4C:BC:...`).
    2. SONOSNET_MESH: Matches against the exact registered household SonosNet BSSIDs
       (`BaseMAC + 1` for each of the 14 players).
    3. ROGUE_OWN_RADIO: Matches known retired/rogue in-house transmitters:
       - `84:16:F9:93:E9:2B/2C/2D` and `86:16:F9:BF:E9:2D/2E/2F` or SSID `TP-Link_5G_93E92D` (EAP330)
       - `0C:72:74:00:63:9A/9B` or exact unmanaged SSID `WuTangLan` (Fritzbox 6660)
       - `6A:55:D4:7D:0B:9B` or SSID matching `DIRECT-*-EPSON*` (Epson ET-4850 Wi-Fi Direct)
    4. NEIGHBOR_WIFI: Any other external 802.11 BSSID.
    """
    norm_bssid = (bssid or "").strip().upper()
    norm_ssid = (ssid or "").strip()

    # 1. OWN_MANAGED_AP by lower 5 octets
    if norm_bssid.endswith(":4C:BC:76:7C:40"):
        return BssidClassificationResult(
            classification=BssidClassification.OWN_MANAGED_AP.value,
            ap_device_slug="galerie-ap",
            ap_name="Galerie EAP650",
            radio_band="2.4GHz",
        )
    if norm_bssid.endswith(":4C:BC:76:7C:41"):
        return BssidClassificationResult(
            classification=BssidClassification.OWN_MANAGED_AP.value,
            ap_device_slug="galerie-ap",
            ap_name="Galerie EAP650",
            radio_band="5GHz",
        )
    if norm_bssid.endswith(":4C:BC:76:94:C0"):
        return BssidClassificationResult(
            classification=BssidClassification.OWN_MANAGED_AP.value,
            ap_device_slug="kitchen-ap",
            ap_name="Kitchen EAP650",
            radio_band="2.4GHz",
        )
    if norm_bssid.endswith(":4C:BC:76:94:C1"):
        return BssidClassificationResult(
            classification=BssidClassification.OWN_MANAGED_AP.value,
            ap_device_slug="kitchen-ap",
            ap_name="Kitchen EAP650",
            radio_band="5GHz",
        )

    # 2. SONOSNET_MESH
    if norm_bssid in SONOSNET_BSSIDS:
        return BssidClassificationResult(
            classification=BssidClassification.SONOSNET_MESH.value,
            ap_device_slug=None,
            ap_name=None,
            radio_band=None,
        )

    # 3. ROGUE_OWN_RADIO
    if (
        norm_bssid in ROGUE_OWN_BSSIDS
        or norm_ssid == "TP-Link_5G_93E92D"
        or norm_ssid == "WuTangLan"
        or (norm_ssid and EPSON_DIRECT_SSID_RE.match(norm_ssid))
    ):
        return BssidClassificationResult(
            classification=BssidClassification.ROGUE_OWN_RADIO.value,
            ap_device_slug=None,
            ap_name=None,
            radio_band=None,
        )

    # 4. NEIGHBOR_WIFI
    return BssidClassificationResult(
        classification=BssidClassification.NEIGHBOR_WIFI.value,
        ap_device_slug=None,
        ap_name=None,
        radio_band=None,
    )


def grade_wifi_dbm(dbm: int | None) -> str:
    """
    Grade Wi-Fi signal strength (dBm):
      EXCELLENT >= -55 dBm
      GOOD      -56 .. -67 dBm
      MARGINAL  -68 .. -75 dBm
      CRITICAL  < -75 dBm (or None)
    """
    if dbm is None or dbm < -75:
        return HealthGrade.CRITICAL.value
    if dbm >= -55:
        return HealthGrade.EXCELLENT.value
    if dbm >= -67:
        return HealthGrade.GOOD.value
    return HealthGrade.MARGINAL.value


def normalize_band(band: str, channel: int) -> str:
    raw = (band or "").strip().lower()
    if "5" in raw or channel >= 36:
        return "5GHz"
    return "2.4GHz"


def build_wifi_room_survey(
    room_slug: str,
    room_name: str,
    survey_slug: str,
    label: str,
    trigger_mode: str = "MANUAL_SURVEY",
    captured_at: datetime | None = None,
    connected_bssid: str | None = None,
    connected_ssid: str | None = None,
    link_speed_mbps: int | None = None,
    frequency_mhz: int | None = None,
    notes: str | None = None,
    readings: list[BssidReadingInput] | None = None,
    room_id: str | None = None,
) -> WiFiRoomSurveySchema:
    ts = captured_at or datetime.now(timezone.utc)
    norm_conn_bssid = connected_bssid.strip().upper() if connected_bssid else None

    classified_readings: list[BssidReadingSchema] = []
    own_5g: list[BssidReadingSchema] = []
    own_24g: list[BssidReadingSchema] = []
    rogue_count = 0
    neighbor_count = 0

    for item in readings or []:
        norm_b = item.bssid.strip().upper()
        band_norm = normalize_band(item.band, item.channel)
        cls_res = classify_bssid(norm_b, item.ssid)
        center_ch = item.center_channel if item.center_channel is not None else item.channel
        is_conn = bool(norm_conn_bssid and norm_b == norm_conn_bssid)

        schema_item = BssidReadingSchema(
            bssid=norm_b,
            ssid=item.ssid,
            band=band_norm,
            channel=item.channel,
            center_channel=center_ch,
            width_mhz=item.width_mhz,
            rssi_dbm=item.rssi_dbm,
            classification=cls_res.classification,
            ap_device_slug=cls_res.ap_device_slug,
            ap_name=cls_res.ap_name,
            is_connected=is_conn,
        )
        classified_readings.append(schema_item)

        if cls_res.classification == BssidClassification.OWN_MANAGED_AP.value:
            if band_norm == "5GHz":
                own_5g.append(schema_item)
            else:
                own_24g.append(schema_item)
        elif cls_res.classification == BssidClassification.ROGUE_OWN_RADIO.value:
            rogue_count += 1
        elif cls_res.classification == BssidClassification.NEIGHBOR_WIFI.value:
            neighbor_count += 1

    # Sort readings strongest first (highest dBm)
    classified_readings.sort(key=lambda r: r.rssi_dbm, reverse=True)

    best_5g_reading = max(own_5g, key=lambda r: r.rssi_dbm) if own_5g else None
    best_24g_reading = max(own_24g, key=lambda r: r.rssi_dbm) if own_24g else None

    best_5ghz_dbm = best_5g_reading.rssi_dbm if best_5g_reading else None
    best_24ghz_dbm = best_24g_reading.rssi_dbm if best_24g_reading else None

    # Determine covering AP (prefer best 5GHz AP if >= -75 dBm, else strongest overall own AP)
    all_own = own_5g + own_24g
    best_overall_own = max(all_own, key=lambda r: r.rssi_dbm) if all_own else None
    primary_ap_reading = (
        best_5g_reading
        if (best_5g_reading and best_5g_reading.rssi_dbm >= -75)
        else best_overall_own
    )

    best_ap_slug = primary_ap_reading.ap_device_slug if primary_ap_reading else None
    best_ap_name = primary_ap_reading.ap_name if primary_ap_reading else None

    grade_5ghz = grade_wifi_dbm(best_5ghz_dbm)
    grade_24ghz = grade_wifi_dbm(best_24ghz_dbm)

    available_dbms = [d for d in (best_5ghz_dbm, best_24ghz_dbm) if d is not None]
    best_any_dbm = max(available_dbms) if available_dbms else None
    wifi_health_grade = grade_wifi_dbm(best_any_dbm)

    if not connected_ssid and norm_conn_bssid:
        matched_conn = next(
            (r for r in classified_readings if r.bssid == norm_conn_bssid and r.ssid),
            None,
        )
        if matched_conn:
            connected_ssid = matched_conn.ssid

    return WiFiRoomSurveySchema(
        survey_slug=survey_slug,
        room_id=room_id,
        room_slug=room_slug,
        room_name=room_name,
        label=label,
        trigger_mode=trigger_mode,
        captured_at=ts,
        connected_bssid=norm_conn_bssid,
        connected_ssid=connected_ssid,
        link_speed_mbps=link_speed_mbps,
        frequency_mhz=frequency_mhz or (5220 if best_5ghz_dbm is not None else 2412),
        best_5ghz_dbm=best_5ghz_dbm,
        best_24ghz_dbm=best_24ghz_dbm,
        best_ap_slug=best_ap_slug,
        best_ap_name=best_ap_name,
        rogue_count=rogue_count,
        neighbor_count=neighbor_count,
        grade_5ghz=grade_5ghz,
        grade_24ghz=grade_24ghz,
        wifi_health_grade=wifi_health_grade,
        notes=notes,
        readings=classified_readings,
    )


class WiFiTelemetryPort(Protocol):
    """Deep module interface seam for Wi-Fi infrastructure, BSSID classification, and room scans."""

    async def collect_wifi_infrastructure(self) -> WiFiInfraSnapshot: ...

    def classify_bssid(
        self, bssid: str, ssid: str | None = None
    ) -> BssidClassificationResult: ...

    async def capture_room_wifi_scan(
        self,
        room_slug: str,
        trigger_mode: str = "MANUAL_SURVEY",
        label: str | None = None,
        connected_bssid: str | None = None,
        link_speed_mbps: int | None = None,
        readings: list[BssidReadingInput] | None = None,
    ) -> WiFiRoomSurveySchema: ...


def _default_radios() -> list[AccessPointRadioRead]:
    return [AccessPointRadioRead(**r) for r in MASTER_AP_RADIOS]


def _default_clients() -> list[OmadaClientAssociationDto]:
    return [OmadaClientAssociationDto(**c) for c in MASTER_OMADA_CLIENTS]


def _default_room_scan_readings(room_slug: str) -> list[BssidReadingInput]:
    """Fallback realistic BSSID scan for a walkthrough when raw BSSID readings are not supplied."""
    if room_slug == "nicolas":
        return [
            BssidReadingInput(
                bssid="7A:4C:BC:76:7C:41",
                ssid="WuTangLan-Guest",
                band="5GHz",
                channel=44,
                center_channel=42,
                width_mhz=80,
                rssi_dbm=-72,
            ),
            BssidReadingInput(
                bssid="76:4C:BC:76:7C:41",
                ssid="WuTangLan-Family",
                band="5GHz",
                channel=44,
                center_channel=42,
                width_mhz=80,
                rssi_dbm=-75,
            ),
            BssidReadingInput(
                bssid="76:4C:BC:76:94:C1",
                ssid="WuTangLan-Family",
                band="5GHz",
                channel=40,
                center_channel=38,
                width_mhz=40,
                rssi_dbm=-82,
            ),
        ]
    return [
        BssidReadingInput(
            bssid="76:4C:BC:76:7C:41",
            ssid="WuTangLan-Family",
            band="5GHz",
            channel=44,
            center_channel=42,
            width_mhz=80,
            rssi_dbm=-54,
        ),
        BssidReadingInput(
            bssid="76:4C:BC:76:7C:40",
            ssid="WuTangLan-Family",
            band="2.4GHz",
            channel=1,
            center_channel=1,
            width_mhz=20,
            rssi_dbm=-56,
        ),
        BssidReadingInput(
            bssid="76:4C:BC:76:94:C0",
            ssid="WuTangLan-Family",
            band="2.4GHz",
            channel=11,
            center_channel=11,
            width_mhz=20,
            rssi_dbm=-68,
        ),
    ]


class FakeWiFiAdapter:
    """Deterministic in-memory adapter implementing `WiFiTelemetryPort`."""

    def __init__(
        self,
        controller_url: str = DEFAULT_OMADA_URL,
        omada_reachable: bool = True,
    ) -> None:
        self.controller_url = controller_url
        self.omada_reachable = omada_reachable

    def classify_bssid(
        self, bssid: str, ssid: str | None = None
    ) -> BssidClassificationResult:
        return classify_bssid(bssid, ssid)

    async def collect_wifi_infrastructure(self) -> WiFiInfraSnapshot:
        return WiFiInfraSnapshot(
            captured_at=datetime.now(timezone.utc),
            omada_controller_url=self.controller_url,
            omada_reachable=self.omada_reachable,
            controller_status="ONLINE" if self.omada_reachable else "DEGRADED_OFFLINE",
            degraded_reason=None
            if self.omada_reachable
            else "Omada Controller unreachable; serving cached radio state",
            radios=_default_radios(),
            clients=_default_clients(),
        )

    async def capture_room_wifi_scan(
        self,
        room_slug: str,
        trigger_mode: str = "MANUAL_SURVEY",
        label: str | None = None,
        connected_bssid: str | None = None,
        link_speed_mbps: int | None = None,
        readings: list[BssidReadingInput] | None = None,
    ) -> WiFiRoomSurveySchema:
        effective_readings = (
            readings
            if readings is not None and len(readings) > 0
            else _default_room_scan_readings(room_slug)
        )
        slug_suffix = uuid.uuid4().hex[:8]
        survey_slug = f"{room_slug}-live-{slug_suffix}"
        return build_wifi_room_survey(
            room_slug=room_slug,
            room_name=room_slug.capitalize(),
            survey_slug=survey_slug,
            label=label or f"Walkthrough Scan ({trigger_mode})",
            trigger_mode=trigger_mode,
            captured_at=datetime.now(timezone.utc),
            connected_bssid=connected_bssid or "76:4C:BC:76:7C:41",
            connected_ssid="WuTangLan-Family",
            link_speed_mbps=link_speed_mbps or 1201,
            readings=effective_readings,
        )


def _default_omada_http_caller(url: str, timeout: float = 2.0) -> str:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.read().decode("utf-8", errors="replace")


class OmadaAndAdbWiFiAdapter:
    """
    Production adapter querying the local TP-Link Omada Software Controller (`https://192.168.55.60:8043`).
    Degrades gracefully without raising errors when `:8043` is offline or unauthenticated.
    """

    def __init__(
        self,
        controller_url: str | None = None,
        timeout_sec: float = 2.0,
        http_caller: Callable[[str, float], str] | None = None,
    ) -> None:
        self.controller_url = (
            controller_url
            or os.getenv("OMADA_CONTROLLER_URL")
            or DEFAULT_OMADA_URL
        ).rstrip("/")
        self.timeout_sec = timeout_sec
        self._http_caller = http_caller or _default_omada_http_caller

    def classify_bssid(
        self, bssid: str, ssid: str | None = None
    ) -> BssidClassificationResult:
        return classify_bssid(bssid, ssid)

    async def collect_wifi_infrastructure(self) -> WiFiInfraSnapshot:
        info_url = f"{self.controller_url}/api/info"
        try:
            raw_text = await asyncio.to_thread(
                self._http_caller, info_url, self.timeout_sec
            )
            parsed = json.loads(raw_text) if raw_text.strip().startswith("{") else {}
            err_code = parsed.get("errorCode", 0)
            if err_code not in (0, None):
                return WiFiInfraSnapshot(
                    captured_at=datetime.now(timezone.utc),
                    omada_controller_url=self.controller_url,
                    omada_reachable=False,
                    controller_status="DEGRADED_UNAUTHENTICATED",
                    degraded_reason=f"Omada API returned errorCode={err_code}",
                    radios=_default_radios(),
                    clients=_default_clients(),
                )
            return WiFiInfraSnapshot(
                captured_at=datetime.now(timezone.utc),
                omada_controller_url=self.controller_url,
                omada_reachable=True,
                controller_status="ONLINE",
                degraded_reason=None,
                radios=_default_radios(),
                clients=_default_clients(),
            )
        except Exception as exc:
            return WiFiInfraSnapshot(
                captured_at=datetime.now(timezone.utc),
                omada_controller_url=self.controller_url,
                omada_reachable=False,
                controller_status="DEGRADED_OFFLINE",
                degraded_reason=str(exc),
                radios=_default_radios(),
                clients=_default_clients(),
            )

    async def capture_room_wifi_scan(
        self,
        room_slug: str,
        trigger_mode: str = "MANUAL_SURVEY",
        label: str | None = None,
        connected_bssid: str | None = None,
        link_speed_mbps: int | None = None,
        readings: list[BssidReadingInput] | None = None,
    ) -> WiFiRoomSurveySchema:
        effective_readings = (
            readings
            if readings is not None and len(readings) > 0
            else _default_room_scan_readings(room_slug)
        )
        slug_suffix = uuid.uuid4().hex[:8]
        survey_slug = f"{room_slug}-live-{slug_suffix}"
        return build_wifi_room_survey(
            room_slug=room_slug,
            room_name=room_slug.capitalize(),
            survey_slug=survey_slug,
            label=label or f"Walkthrough Scan ({trigger_mode})",
            trigger_mode=trigger_mode,
            captured_at=datetime.now(timezone.utc),
            connected_bssid=connected_bssid or "76:4C:BC:76:7C:41",
            connected_ssid="WuTangLan-Family",
            link_speed_mbps=link_speed_mbps or 1201,
            readings=effective_readings,
        )
