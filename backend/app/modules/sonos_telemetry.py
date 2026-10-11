from __future__ import annotations

import asyncio
import html
import re
import time
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from collections.abc import AsyncIterator, Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Protocol

from app.models.entities import ConnectionMode, StpPortState
from app.schemas.topology import (
    GhostFlushResult,
    GhostFlushZoneResult,
    HouseholdSonosSnapshot,
    PlayerRfSample,
    PlayerTelemetryDto,
    SonosMeshLinkDto,
)

EXPECTED_STP_ROOT = "9000.542a1b63fe6e"

SOAP_GET_ZONE_GROUP_STATE = """<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<s:Body><u:GetZoneGroupState xmlns:u="urn:schemas-upnp-org:service:ZoneGroupTopology:1" /></s:Body>
</s:Envelope>"""

SOAP_GET_VOLUME = """<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<s:Body>
<u:GetVolume xmlns:u="urn:schemas-upnp-org:service:RenderingControl:1">
<InstanceID>0</InstanceID>
<Channel>Master</Channel>
</u:GetVolume>
</s:Body>
</s:Envelope>"""

SOAP_STANDALONE_GROUP = """<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<s:Body>
<u:BecomeCoordinatorOfStandaloneGroup xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
<InstanceID>0</InstanceID>
</u:BecomeCoordinatorOfStandaloneGroup>
</s:Body>
</s:Envelope>"""


# Master 14-player household registry (5 Oct 2026 verified hardware inventory)
MASTER_SONOS_INVENTORY: list[dict[str, Any]] = [
    {
        "rincon_uuid": "RINCON_542A1B63FE6E01400",
        "zone_name": "Wohnzimmer_Bookshelf",
        "room_slug": "wohnzimmer",
        "room_name": "Wohnzimmer",
        "ip_address": "192.168.10.230",
        "base_mac": "54:2A:1B:63:FE:6E",
        "sonosnet_bssid": "54:2A:1B:63:FE:6F",
        "connection_mode": ConnectionMode.ETHERNET_ROOT,
        "ieee_channel": 6,
        "ofdm_ani_level": 6,
        "noise_floor_dbm": -111,
        "phy_error_total": 84200,
        "baseline_err_rate": 12.5,
        "designated_root": EXPECTED_STP_ROOT,
        "stp_root_port": "0",
        "stp_path_cost": 0,
        "master_volume": 18,
        "ping_rtt_ms": 0.8,
        "bonded_parent_uuid": None,
    },
    {
        "rincon_uuid": "RINCON_B8E937E6098401400",
        "zone_name": "Wohnzimmer_Esstisch",
        "room_slug": "wohnzimmer",
        "room_name": "Wohnzimmer",
        "ip_address": "192.168.10.160",
        "base_mac": "B8:E9:37:E6:09:84",
        "sonosnet_bssid": "B8:E9:37:E6:09:85",
        "connection_mode": ConnectionMode.SONOSNET_MODE,
        "ieee_channel": 6,
        "ofdm_ani_level": 9,
        "noise_floor_dbm": -110,
        "phy_error_total": 195400,
        "baseline_err_rate": 789.0,
        "designated_root": EXPECTED_STP_ROOT,
        "stp_root_port": "1",
        "stp_path_cost": 200,
        "master_volume": 15,
        "ping_rtt_ms": 6.2,
        "bonded_parent_uuid": None,
    },
    {
        "rincon_uuid": "RINCON_B8E937E5152A01400",
        "zone_name": "Wohnzimmer_Buchregal",
        "room_slug": "wohnzimmer",
        "room_name": "Wohnzimmer",
        "ip_address": "192.168.10.101",
        "base_mac": "B8:E9:37:E5:15:2A",
        "sonosnet_bssid": "B8:E9:37:E5:15:2B",
        "connection_mode": ConnectionMode.SONOSNET_MODE,
        "ieee_channel": 6,
        "ofdm_ani_level": 9,
        "noise_floor_dbm": -110,
        "phy_error_total": 245100,
        "baseline_err_rate": 1126.0,
        "designated_root": EXPECTED_STP_ROOT,
        "stp_root_port": "2",
        "stp_path_cost": 200,
        "master_volume": 15,
        "ping_rtt_ms": 8.4,
        "bonded_parent_uuid": None,
    },
    {
        "rincon_uuid": "RINCON_949F3EC0EEA101400",
        "zone_name": "Fernsehecke (LF,RF)",
        "room_slug": "fernsehecke",
        "room_name": "Fernsehecke",
        "ip_address": "192.168.10.241",
        "base_mac": "94:9F:3E:C0:EE:A1",
        "sonosnet_bssid": "94:9F:3E:C0:EE:A2",
        "connection_mode": ConnectionMode.SONOSNET_MODE,
        "ieee_channel": 6,
        "ofdm_ani_level": None,  # F-02: Beam reports 'undefined'
        "noise_floor_dbm": None,  # F-02: Beam reports '0, 0, 0, 0'
        "phy_error_total": 120,
        "baseline_err_rate": 0.0,
        "designated_root": EXPECTED_STP_ROOT,
        "stp_root_port": "1",
        "stp_path_cost": 200,
        "master_volume": 28,
        "ping_rtt_ms": 3.1,
        "bonded_parent_uuid": None,
    },
    {
        "rincon_uuid": "RINCON_5CAAFD490CCA01400",
        "zone_name": "Fernsehecke (LR)",
        "room_slug": "fernsehecke",
        "room_name": "Fernsehecke",
        "ip_address": "192.168.10.102",
        "base_mac": "5C:AA:FD:49:0C:CA",
        "sonosnet_bssid": "5C:AA:FD:49:0C:CB",
        "connection_mode": ConnectionMode.HT_SATELLITE,
        "ieee_channel": 48,
        "ofdm_ani_level": 0,
        "noise_floor_dbm": -106,
        "phy_error_total": 310,
        "baseline_err_rate": 0.0,
        "designated_root": EXPECTED_STP_ROOT,
        "stp_root_port": "1",
        "stp_path_cost": 220,
        "master_volume": 28,
        "ping_rtt_ms": 3.5,
        "bonded_parent_uuid": "RINCON_949F3EC0EEA101400",
    },
    {
        "rincon_uuid": "RINCON_949F3E00292E01400",
        "zone_name": "Fernsehecke (RR)",
        "room_slug": "fernsehecke",
        "room_name": "Fernsehecke",
        "ip_address": "192.168.10.103",
        "base_mac": "94:9F:3E:00:29:2E",
        "sonosnet_bssid": "94:9F:3E:00:29:2F",
        "connection_mode": ConnectionMode.HT_SATELLITE,
        "ieee_channel": 48,
        "ofdm_ani_level": 0,
        "noise_floor_dbm": -108,
        "phy_error_total": 290,
        "baseline_err_rate": 0.0,
        "designated_root": EXPECTED_STP_ROOT,
        "stp_root_port": "1",
        "stp_path_cost": 220,
        "master_volume": 28,
        "ping_rtt_ms": 3.6,
        "bonded_parent_uuid": "RINCON_949F3EC0EEA101400",
    },
    {
        "rincon_uuid": "RINCON_5CAAFD595EEA01400",
        "zone_name": "Keller",
        "room_slug": "keller",
        "room_name": "Keller",
        "ip_address": "192.168.10.217",
        "base_mac": "5C:AA:FD:59:5E:EA",
        "sonosnet_bssid": "5C:AA:FD:59:5E:EB",
        "connection_mode": ConnectionMode.SONOSNET_MODE,
        "ieee_channel": 6,
        "ofdm_ani_level": 5,
        "noise_floor_dbm": -106,
        "phy_error_total": 14200,
        "baseline_err_rate": 4.2,
        "designated_root": EXPECTED_STP_ROOT,
        "stp_root_port": "1",
        "stp_path_cost": 280,
        "master_volume": 20,
        "ping_rtt_ms": 11.5,
        "bonded_parent_uuid": None,
    },
    {
        "rincon_uuid": "RINCON_347E5C3826E201400",
        "zone_name": "Küche",
        "room_slug": "kueche",
        "room_name": "Küche",
        "ip_address": "192.168.10.202",
        "base_mac": "34:7E:5C:38:26:E2",
        "sonosnet_bssid": "34:7E:5C:38:26:E3",
        "connection_mode": ConnectionMode.SONOSNET_MODE,
        "ieee_channel": 6,
        "ofdm_ani_level": 0,
        "noise_floor_dbm": -100,
        "phy_error_total": 980,
        "baseline_err_rate": 0.0,
        "designated_root": EXPECTED_STP_ROOT,
        "stp_root_port": "1",
        "stp_path_cost": 240,
        "master_volume": 22,
        "ping_rtt_ms": 5.0,
        "bonded_parent_uuid": None,
    },
    {
        "rincon_uuid": "RINCON_347E5C35B0F401400",
        "zone_name": "Büroecke",
        "room_slug": "bueroecke",
        "room_name": "Büroecke",
        "ip_address": "192.168.10.151",
        "base_mac": "34:7E:5C:35:B0:F4",
        "sonosnet_bssid": "34:7E:5C:35:B0:F5",
        "connection_mode": ConnectionMode.SONOSNET_MODE,
        "ieee_channel": 6,
        "ofdm_ani_level": 0,
        "noise_floor_dbm": -104,
        "phy_error_total": 450,
        "baseline_err_rate": 0.0,
        "designated_root": EXPECTED_STP_ROOT,
        "stp_root_port": "1",
        "stp_path_cost": 200,
        "master_volume": 16,
        "ping_rtt_ms": 4.1,
        "bonded_parent_uuid": None,
    },
    {
        "rincon_uuid": "RINCON_347E5C35B2C001400",
        "zone_name": "Noah",
        "room_slug": "noah",
        "room_name": "Noah",
        "ip_address": "192.168.10.229",
        "base_mac": "34:7E:5C:35:B2:C0",
        "sonosnet_bssid": "34:7E:5C:35:B2:C1",
        "connection_mode": ConnectionMode.SONOSNET_MODE,
        "ieee_channel": 6,
        "ofdm_ani_level": 4,
        "noise_floor_dbm": -100,
        "phy_error_total": 8900,
        "baseline_err_rate": 3.5,
        "designated_root": EXPECTED_STP_ROOT,
        "stp_root_port": "1",
        "stp_path_cost": 260,
        "master_volume": 20,
        "ping_rtt_ms": 9.2,
        "bonded_parent_uuid": None,
    },
    {
        "rincon_uuid": "RINCON_542A1B64268001400",
        "zone_name": "Noemi",
        "room_slug": "noemi",
        "room_name": "Noemi",
        "ip_address": "192.168.10.244",
        "base_mac": "54:2A:1B:64:26:80",
        "sonosnet_bssid": "54:2A:1B:64:26:81",
        "connection_mode": ConnectionMode.SONOSNET_MODE,
        "ieee_channel": 6,
        "ofdm_ani_level": 5,
        "noise_floor_dbm": -100,
        "phy_error_total": 19300,
        "baseline_err_rate": 14.0,
        "designated_root": EXPECTED_STP_ROOT,
        "stp_root_port": "1",
        "stp_path_cost": 320,
        "master_volume": 48,
        "ping_rtt_ms": 18.0,
        "bonded_parent_uuid": None,
    },
    {
        "rincon_uuid": "RINCON_347E5C36DE9001400",
        "zone_name": "Nicolas",
        "room_slug": "nicolas",
        "room_name": "Nicolas",
        "ip_address": "192.168.10.165",
        "base_mac": "34:7E:5C:36:DE:90",
        "sonosnet_bssid": "34:7E:5C:36:DE:91",
        "connection_mode": ConnectionMode.STATION_MODE,
        "ieee_channel": 44,
        "ofdm_ani_level": 0,
        "noise_floor_dbm": -102,
        "phy_error_total": 15546,
        "baseline_err_rate": 0.0,
        "designated_root": EXPECTED_STP_ROOT,
        "stp_root_port": "0",
        "stp_path_cost": 0,
        "master_volume": 25,
        "ping_rtt_ms": 2.3,
        "bonded_parent_uuid": None,
    },
    {
        "rincon_uuid": "RINCON_347E5C3828B001400",
        "zone_name": "Eltern",
        "room_slug": "elternschlafzimmer",
        "room_name": "Elternschlafzimmer",
        "ip_address": "192.168.10.131",
        "base_mac": "34:7E:5C:38:28:B0",
        "sonosnet_bssid": "34:7E:5C:38:28:B1",
        "connection_mode": ConnectionMode.SONOSNET_MODE,
        "ieee_channel": 6,
        "ofdm_ani_level": 4,
        "noise_floor_dbm": -110,
        "phy_error_total": 6200,
        "baseline_err_rate": 2.1,
        "designated_root": EXPECTED_STP_ROOT,
        "stp_root_port": "1",
        "stp_path_cost": 250,
        "master_volume": 20,
        "ping_rtt_ms": 7.4,
        "bonded_parent_uuid": None,
    },
    {
        "rincon_uuid": "RINCON_347E5C31CE2801400",
        "zone_name": "Elternbad",
        "room_slug": "elternbad",
        "room_name": "Elternbad",
        "ip_address": "192.168.10.113",
        "base_mac": "34:7E:5C:31:CE:28",
        "sonosnet_bssid": "34:7E:5C:31:CE:29",
        "connection_mode": ConnectionMode.SONOSNET_MODE,
        "ieee_channel": 6,
        "ofdm_ani_level": 4,
        "noise_floor_dbm": -110,
        "phy_error_total": 5800,
        "baseline_err_rate": 1.8,
        "designated_root": EXPECTED_STP_ROOT,
        "stp_root_port": "1",
        "stp_path_cost": 280,
        "master_volume": 18,
        "ping_rtt_ms": 8.9,
        "bonded_parent_uuid": None,
    },
]

BSSID_TO_UUID: dict[str, str] = {
    item["sonosnet_bssid"].upper(): item["rincon_uuid"]
    for item in MASTER_SONOS_INVENTORY
    if item.get("sonosnet_bssid")
}
MAC_TO_UUID: dict[str, str] = {
    item["base_mac"].upper(): item["rincon_uuid"]
    for item in MASTER_SONOS_INVENTORY
    if item.get("base_mac")
}
UUID_TO_META: dict[str, dict[str, Any]] = {
    item["rincon_uuid"]: item for item in MASTER_SONOS_INVENTORY
}


class SonosTelemetryPort(Protocol):
    """Deep interface seam for Sonos RF, STP Mesh, and UPnP ZoneGroup telemetry."""

    async def collect_household_snapshot(
        self, consumer_id: str = "on-demand"
    ) -> HouseholdSonosSnapshot: ...

    async def flush_ghost_groups(
        self, zone_ips: list[str] | None = None
    ) -> GhostFlushResult: ...

    def stream_room_rf_velocity(
        self,
        room_id: str,
        interval_sec: float = 2.0,
        consumer_id: str = "ws-default",
        max_iterations: int | None = None,
    ) -> AsyncIterator[list[PlayerRfSample]]: ...


def parse_ath_rincon_status(
    text: str,
    source_uuid: str,
    source_bssid: str | None = None,
    bssid_to_uuid: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Parse `/status/proc/ath_rincon/status` text.
    Enforces F-02 Hardware Telemetry Normalization:
      - `OFDM ANI level: undefined` or missing -> `None` (never `0`)
      - `Noise Floor: 0 dBm` or `0, 0, 0, 0` -> `None` (never `0`)
    """
    lookup = {k.upper(): v for k, v in (bssid_to_uuid or BSSID_TO_UUID).items()}
    lookup.update(MAC_TO_UUID)

    # OFDM ANI level
    ani_match = re.search(r"OFDM ANI level:\s*([0-9]+|undefined)", text, re.IGNORECASE)
    ofdm_ani_level: int | None = None
    if ani_match:
        raw_ani = ani_match.group(1).strip().lower()
        if raw_ani.isdigit():
            ofdm_ani_level = int(raw_ani)

    # Noise Floor normalization (F-02): filter out 0 values (e.g. '0, 0, 0, 0' or '0 dBm' on Beam)
    noise_floor_dbm: int | None = None
    noise_candidates: list[int] = []
    for line in text.splitlines():
        if "noise floor" in line.lower():
            nums = [int(n) for n in re.findall(r"-?\d+", line.split(":", 1)[-1])]
            for val in nums:
                if val < 0:
                    noise_candidates.append(val)
    if noise_candidates:
        noise_floor_dbm = noise_candidates[0]

    # PHY errors total
    phy_match = re.search(r"PHY errors since last reading/reset:\s*(\d+)", text, re.IGNORECASE)
    phy_error_total = int(phy_match.group(1)) if phy_match else None

    # IEEE channel
    ch_match = re.search(r"IEEE channel:\s*(\d+)", text, re.IGNORECASE)
    ieee_channel = int(ch_match.group(1)) if ch_match else None

    # Peer SNR matrix: Node <MAC> - FROM <in_snr> : TO <out_snr> : STP <state>
    links: list[dict[str, Any]] = []
    node_pattern = re.compile(
        r"Node\s+([0-9A-Fa-f:]{17})\s*-\s*FROM\s+(\d+)\s*:\s*TO\s+(\d+)\s*:\s*STP\s+([0-9A-Fa-f]+|forwarding|blocking|undefined)",
        re.IGNORECASE,
    )
    for m in node_pattern.finditer(text):
        peer_mac = m.group(1).upper()
        from_db = int(m.group(2))
        to_db = int(m.group(3))
        raw_stp = m.group(4).strip().lower()
        if raw_stp in ("03", "04", "forwarding"):
            stp_state = StpPortState.FORWARDING.value
        else:
            stp_state = StpPortState.BLOCKING.value

        target_uuid = lookup.get(peer_mac)
        if not target_uuid or (from_db == 0 and to_db == 0 and stp_state == StpPortState.BLOCKING.value):
            continue

        links.append(
            {
                "source_rincon_uuid": source_uuid,
                "target_rincon_uuid": target_uuid,
                "source_bssid": source_bssid,
                "target_bssid": peer_mac,
                "channel": ieee_channel or 6,
                "from_db": from_db,
                "to_db": to_db,
                "stp_state": stp_state,
            }
        )

    return {
        "ofdm_ani_level": ofdm_ani_level,
        "noise_floor_dbm": noise_floor_dbm,
        "phy_error_total": phy_error_total,
        "ieee_channel": ieee_channel,
        "links": links,
    }


def parse_showstp(text: str) -> dict[str, Any]:
    """Parse `/status/showstp` output for designated root, root port, and path cost."""
    root_m = re.search(r"designated root\s+([0-9a-fA-F]+\.[0-9a-fA-F]+)", text, re.IGNORECASE)
    designated_root = root_m.group(1).lower() if root_m else None

    cost_m = re.search(r"path cost\s+(\d+)", text, re.IGNORECASE)
    stp_path_cost = int(cost_m.group(1)) if cost_m else None

    port_m = re.search(r"root port\s+(\S+)", text, re.IGNORECASE)
    stp_root_port = port_m.group(1) if port_m else None

    return {
        "designated_root": designated_root,
        "stp_path_cost": stp_path_cost,
        "stp_root_port": stp_root_port,
    }


def _extract_ip_from_location(location: str | None) -> str | None:
    if not location:
        return None
    m = re.search(r"https?://([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", location)
    return m.group(1) if m else None


def parse_zone_group_state(xml_text: str) -> dict[str, dict[str, Any]]:
    """
    Parse `ZoneGroupTopology:1#GetZoneGroupState` SOAP or raw XML.
    Enforces F-05 Nested `<Satellite>` Discovery and Ghost Group detection.
    Returns mapping of `rincon_uuid -> parsed group/member/satellite state`.
    """
    if not xml_text or not xml_text.strip():
        return {}

    try:
        outer = ET.fromstring(xml_text)
    except ET.ParseError:
        return {}

    # Unwrap SOAP <ZoneGroupState> if HTML-escaped inside SOAP body
    zgs_elem = outer.find(".//{*}ZoneGroupState")
    if zgs_elem is None:
        zgs_elem = outer.find(".//ZoneGroupState")

    if zgs_elem is not None and zgs_elem.text and "<ZoneGroup" in zgs_elem.text:
        try:
            root = ET.fromstring(html.unescape(zgs_elem.text))
        except ET.ParseError:
            root = outer
    else:
        root = outer

    members_by_uuid: dict[str, dict[str, Any]] = {}

    for zg in root.iter():
        if not zg.tag.endswith("ZoneGroup"):
            continue
        coordinator_uuid = zg.attrib.get("Coordinator", "")
        group_id = zg.attrib.get("ID", "")
        id_prefix = group_id.split(":")[0] if ":" in group_id else group_id

        vanished_elems = [
            el for el in zg.iter() if el.tag.endswith("VanishedDevices") and len(list(el)) > 0
        ]
        has_vanished = len(vanished_elems) > 0
        is_ghost = bool(
            (id_prefix and coordinator_uuid and id_prefix != coordinator_uuid)
            or has_vanished
        )

        for child in list(zg):
            if not child.tag.endswith("ZoneGroupMember"):
                continue
            member_uuid = child.attrib.get("UUID", "")
            member_zone = child.attrib.get("ZoneName", "")
            member_loc = child.attrib.get("Location", "")
            member_ip = _extract_ip_from_location(member_loc)
            ht_map = child.attrib.get("HTSatChanMapSet", "")

            if member_uuid:
                members_by_uuid[member_uuid] = {
                    "rincon_uuid": member_uuid,
                    "zone_name": member_zone,
                    "ip_address": member_ip,
                    "group_id": group_id,
                    "coordinator_uuid": coordinator_uuid,
                    "has_vanished_devices": has_vanished,
                    "is_ghost_group": is_ghost,
                    "is_satellite": False,
                    "bonded_parent_uuid": None,
                    "ht_sat_chan_map": ht_map,
                }

            # F-05: Parse nested <Satellite> elements inside <ZoneGroupMember>
            for sat in child.iter():
                if not sat.tag.endswith("Satellite"):
                    continue
                sat_uuid = sat.attrib.get("UUID", "")
                if not sat_uuid:
                    continue
                sat_zone = sat.attrib.get("ZoneName") or member_zone
                sat_loc = sat.attrib.get("Location", "")
                sat_ip = _extract_ip_from_location(sat_loc)
                sat_ht_map = sat.attrib.get("HTSatChanMapSet") or ht_map
                # Disambiguate LR vs RR zone names if generic 'Fernsehecke' is in XML
                meta_zone = UUID_TO_META.get(sat_uuid, {}).get("zone_name")
                resolved_zone = meta_zone or sat_zone

                members_by_uuid[sat_uuid] = {
                    "rincon_uuid": sat_uuid,
                    "zone_name": resolved_zone,
                    "ip_address": sat_ip or UUID_TO_META.get(sat_uuid, {}).get("ip_address"),
                    "group_id": group_id,
                    "coordinator_uuid": coordinator_uuid,
                    "has_vanished_devices": has_vanished,
                    "is_ghost_group": is_ghost,
                    "is_satellite": True,
                    "bonded_parent_uuid": member_uuid,
                    "ht_sat_chan_map": sat_ht_map,
                }

    return members_by_uuid


class _PhyErrorCursorTracker:
    """
    Per-consumer isolated `(prev_phy_total, prev_timestamp)` cursor store (F-04).
    Ensures rapid WebSocket polling (`ws-*`) or `on-demand` polls never perturb
    the `background-60s` collector window.
    """

    def __init__(self) -> None:
        self._cursors: dict[str, dict[str, tuple[int, float]]] = {}

    def needs_cold_probe(
        self,
        consumer_id: str,
        raw_phy_by_uuid: dict[str, int | None],
        now: float,
    ) -> bool:
        bucket = self._cursors.get(consumer_id)
        if not bucket:
            return True
        max_age = 120.0 if consumer_id.startswith("background") else 15.0
        for r_uuid, phy in raw_phy_by_uuid.items():
            if phy is None:
                continue
            prev = bucket.get(r_uuid)
            if prev is None or (now - prev[1]) > max_age:
                return True
        return False

    def seed_cursor_sample(
        self,
        consumer_id: str,
        raw_phy_by_uuid: dict[str, int | None],
        timestamp: float,
    ) -> None:
        bucket = self._cursors.setdefault(consumer_id, {})
        for r_uuid, phy in raw_phy_by_uuid.items():
            if phy is not None:
                bucket[r_uuid] = (phy, timestamp)

    def compute_rates_and_advance(
        self,
        consumer_id: str,
        raw_phy_by_uuid: dict[str, int | None],
        timestamp: float,
    ) -> dict[str, float | None]:
        bucket = self._cursors.setdefault(consumer_id, {})
        rates: dict[str, float | None] = {}
        for r_uuid, current_phy in raw_phy_by_uuid.items():
            if current_phy is None:
                rates[r_uuid] = None
                continue
            prev = bucket.get(r_uuid)
            if prev is None:
                bucket[r_uuid] = (current_phy, timestamp)
                rates[r_uuid] = 0.0
                continue
            prev_phy, prev_ts = prev
            # F-04: If speaker rebooted or counter reset (current_phy < prev_phy), reset cursor -> 0.0 err/s
            if current_phy < prev_phy:
                bucket[r_uuid] = (current_phy, timestamp)
                rates[r_uuid] = 0.0
                continue
            dt = timestamp - prev_ts
            if dt <= 0:
                rates[r_uuid] = 0.0
            else:
                rates[r_uuid] = round((current_phy - prev_phy) / dt, 2)
            bucket[r_uuid] = (current_phy, timestamp)
        return rates


class FakeSonosAdapter:
    """
    Deterministic in-memory Sonos telemetry adapter implementing `SonosTelemetryPort`.
    Exercises the exact same XML/text parsers, F-02 normalization, F-04 per-consumer
    delta cursors, and F-05 nested `<Satellite>` discovery as `HttpSonosAdapter`.
    """

    def __init__(
        self,
        probe_interval_sec: float = 0.05,
        clock: Callable[[], float] | None = None,
        sleep_fn: Callable[[float], None] | None = None,
    ) -> None:
        self.probe_interval_sec = probe_interval_sec
        self._clock = clock or time.monotonic
        self._sleep_fn = sleep_fn
        self._cursor_tracker = _PhyErrorCursorTracker()
        self._state_by_uuid: dict[str, dict[str, Any]] = {}
        self._group_counter = 10
        for item in MASTER_SONOS_INVENTORY:
            r_uuid = item["rincon_uuid"]
            self._group_counter += 1
            coord_uuid = item["bonded_parent_uuid"] or r_uuid
            self._state_by_uuid[r_uuid] = {
                **item,
                "group_id": f"{coord_uuid}:{self._group_counter}",
                "coordinator_uuid": coord_uuid,
                "has_vanished_devices": False,
            }

    def set_phy_errors(self, rincon_uuid: str, total: int) -> None:
        if rincon_uuid in self._state_by_uuid:
            self._state_by_uuid[rincon_uuid]["phy_error_total"] = total

    def advance_phy_errors(self, rincon_uuid: str, delta: int) -> None:
        if rincon_uuid in self._state_by_uuid:
            cur = self._state_by_uuid[rincon_uuid].get("phy_error_total") or 0
            self._state_by_uuid[rincon_uuid]["phy_error_total"] = cur + delta

    def inject_ghost_group(
        self,
        rincon_uuid: str,
        corrupted_group_id: str,
        has_vanished_devices: bool = False,
    ) -> None:
        if rincon_uuid in self._state_by_uuid:
            self._state_by_uuid[rincon_uuid]["group_id"] = corrupted_group_id
            self._state_by_uuid[rincon_uuid]["has_vanished_devices"] = has_vanished_devices

    def _build_zone_group_state_xml(self) -> str:
        lines = ["<ZoneGroupState><ZoneGroups>"]
        beam_state = self._state_by_uuid["RINCON_949F3EC0EEA101400"]
        lr_state = self._state_by_uuid["RINCON_5CAAFD490CCA01400"]
        rr_state = self._state_by_uuid["RINCON_949F3E00292E01400"]

        for r_uuid, st in self._state_by_uuid.items():
            if st.get("bonded_parent_uuid"):
                continue
            coord = st["coordinator_uuid"]
            gid = st["group_id"]
            ip = st["ip_address"]
            zname = html.escape(st["zone_name"])
            lines.append(f'<ZoneGroup Coordinator="{coord}" ID="{gid}">')
            if st.get("has_vanished_devices"):
                lines.append(
                    '<VanishedDevices><Device UUID="RINCON_347E5C3828B001400" /></VanishedDevices>'
                )
            if r_uuid == "RINCON_949F3EC0EEA101400":
                lines.append(
                    f'<ZoneGroupMember UUID="{r_uuid}" ZoneName="{zname}" '
                    f'Location="http://{ip}:1400/xml/device_description.xml">'
                )
                for sat in (lr_state, rr_state):
                    s_uuid = sat["rincon_uuid"]
                    s_zone = html.escape(sat["zone_name"])
                    s_ip = sat["ip_address"]
                    lines.append(
                        f'<Satellite UUID="{s_uuid}" ZoneName="{s_zone}" '
                        f'Location="http://{s_ip}:1400/xml/device_description.xml" '
                        f'HTSatChanMapSet="{beam_state["rincon_uuid"]}:LF,RF;{s_uuid}:RR" />'
                    )
                lines.append("</ZoneGroupMember>")
            else:
                lines.append(
                    f'<ZoneGroupMember UUID="{r_uuid}" ZoneName="{zname}" '
                    f'Location="http://{ip}:1400/xml/device_description.xml" />'
                )
            lines.append("</ZoneGroup>")
        lines.append("</ZoneGroups></ZoneGroupState>")
        return "\n".join(lines)

    def _build_ath_rincon_text(self, r_uuid: str) -> str:
        st = self._state_by_uuid[r_uuid]
        if r_uuid == "RINCON_949F3EC0EEA101400":
            # F-02: Beam hardware reports 0, 0, 0, 0 and undefined ANI
            nf_line = "Noise Floor: 0, 0, 0, 0"
            ani_line = "OFDM ANI level: undefined"
        else:
            nf = st["noise_floor_dbm"] if st["noise_floor_dbm"] is not None else 0
            ani = st["ofdm_ani_level"] if st["ofdm_ani_level"] is not None else "undefined"
            nf_line = f"Noise Floor: {nf} dBm"
            ani_line = f"OFDM ANI level: {ani}"

        lines = [
            f"IEEE channel: {st['ieee_channel']}",
            nf_line,
            ani_line,
            f"PHY errors since last reading/reset: {st['phy_error_total']}",
        ]
        # Include representative peer SNR matrix rows
        root_bssid = "54:2A:1B:63:FE:6F"
        beam_bssid = "94:9F:3E:C0:EE:A2"
        if r_uuid not in (
            "RINCON_542A1B63FE6E01400",
            "RINCON_5CAAFD490CCA01400",
            "RINCON_949F3E00292E01400",
            "RINCON_347E5C36DE9001400",
        ):
            lines.append(f"Node {root_bssid} - FROM 45 : TO 44 : STP 04")
            if r_uuid != "RINCON_949F3EC0EEA101400":
                lines.append(f"Node {beam_bssid} - FROM 50 : TO 54 : STP 00")
        elif r_uuid in ("RINCON_5CAAFD490CCA01400", "RINCON_949F3E00292E01400"):
            lines.append(f"Node {beam_bssid} - FROM 60 : TO 66 : STP 04")
        return "\n".join(lines)

    def _poll_once(self) -> tuple[dict[str, dict[str, Any]], list[SonosMeshLinkDto], dict[str, int | None]]:
        zgs_map = parse_zone_group_state(self._build_zone_group_state_xml())
        players_raw: dict[str, dict[str, Any]] = {}
        mesh_links: list[SonosMeshLinkDto] = []
        raw_phy: dict[str, int | None] = {}

        for r_uuid, st in self._state_by_uuid.items():
            ath = parse_ath_rincon_status(
                self._build_ath_rincon_text(r_uuid),
                source_uuid=r_uuid,
                source_bssid=st["sonosnet_bssid"],
                bssid_to_uuid=BSSID_TO_UUID,
            )
            stp_text = (
                f"designated root {st['designated_root']}\n"
                f"root port {st['stp_root_port']} path cost {st['stp_path_cost']}\n"
            )
            stp = parse_showstp(stp_text)
            zg_info = zgs_map.get(r_uuid, {})

            raw_phy[r_uuid] = ath["phy_error_total"]
            for link in ath["links"]:
                src_name = self._state_by_uuid.get(link["source_rincon_uuid"], {}).get("zone_name")
                tgt_name = self._state_by_uuid.get(link["target_rincon_uuid"], {}).get("zone_name")
                mesh_links.append(
                    SonosMeshLinkDto(
                        source_rincon_uuid=link["source_rincon_uuid"],
                        target_rincon_uuid=link["target_rincon_uuid"],
                        source_zone_name=src_name,
                        target_zone_name=tgt_name,
                        source_bssid=link["source_bssid"],
                        target_bssid=link["target_bssid"],
                        channel=link["channel"],
                        from_db=link["from_db"],
                        to_db=link["to_db"],
                        stp_state=link["stp_state"],
                    )
                )

            players_raw[r_uuid] = {
                **st,
                "ip_address": zg_info.get("ip_address") or st["ip_address"],
                "ofdm_ani_level": ath["ofdm_ani_level"],
                "noise_floor_dbm": ath["noise_floor_dbm"],
                "phy_error_total": ath["phy_error_total"],
                "ieee_channel": ath["ieee_channel"],
                "designated_root": stp["designated_root"],
                "stp_root_port": stp["stp_root_port"],
                "stp_path_cost": stp["stp_path_cost"],
                "group_id": zg_info.get("group_id", st["group_id"]),
                "coordinator_uuid": zg_info.get("coordinator_uuid", st["coordinator_uuid"]),
                "has_vanished_devices": zg_info.get("has_vanished_devices", False),
                "is_ghost_group": zg_info.get("is_ghost_group", False),
                "bonded_parent_uuid": zg_info.get("bonded_parent_uuid", st.get("bonded_parent_uuid")),
            }

        return players_raw, mesh_links, raw_phy

    async def _wait_interval(self, dt: float) -> float:
        effective_dt = dt if dt > 0 else 1.0
        for st in self._state_by_uuid.values():
            rate = st.get("baseline_err_rate") or 0.0
            st["phy_error_total"] = int((st.get("phy_error_total") or 0) + round(rate * effective_dt))
        if self._sleep_fn is not None:
            self._sleep_fn(effective_dt)
        elif dt > 0:
            await asyncio.sleep(dt)
        return effective_dt

    async def collect_household_snapshot(
        self, consumer_id: str = "on-demand"
    ) -> HouseholdSonosSnapshot:
        t1 = self._clock()
        players_raw, mesh_links, raw_phy_1 = self._poll_once()

        if self._cursor_tracker.needs_cold_probe(consumer_id, raw_phy_1, t1):
            self._cursor_tracker.seed_cursor_sample(consumer_id, raw_phy_1, t1)
            eff_dt = await self._wait_interval(self.probe_interval_sec)
            t2 = self._clock()
            if t2 <= t1:
                t2 = t1 + eff_dt
            players_raw, mesh_links, raw_phy_2 = self._poll_once()
            rates = self._cursor_tracker.compute_rates_and_advance(
                consumer_id, raw_phy_2, t2
            )
        else:
            rates = self._cursor_tracker.compute_rates_and_advance(
                consumer_id, raw_phy_1, t1
            )

        player_dtos: list[PlayerTelemetryDto] = []
        ghost_zones: list[str] = []
        for r_uuid, p in players_raw.items():
            if p["is_ghost_group"]:
                ghost_zones.append(p["zone_name"])
            player_dtos.append(
                PlayerTelemetryDto(
                    rincon_uuid=r_uuid,
                    zone_name=p["zone_name"],
                    room_name=p.get("room_name"),
                    ip_address=p["ip_address"],
                    base_mac=p.get("base_mac"),
                    sonosnet_bssid=p.get("sonosnet_bssid"),
                    is_reachable=True,
                    connection_mode=p["connection_mode"],
                    ieee_channel=p["ieee_channel"],
                    ofdm_ani_level=p["ofdm_ani_level"],
                    noise_floor_dbm=p["noise_floor_dbm"],
                    phy_error_total=p["phy_error_total"],
                    phy_error_rate=rates.get(r_uuid, 0.0),
                    designated_root=p["designated_root"],
                    stp_root_port=p["stp_root_port"],
                    stp_path_cost=p["stp_path_cost"],
                    group_id=p["group_id"],
                    coordinator_uuid=p["coordinator_uuid"],
                    has_vanished_devices=p["has_vanished_devices"],
                    is_ghost_group=p["is_ghost_group"],
                    master_volume=p.get("master_volume"),
                    ping_rtt_ms=p.get("ping_rtt_ms"),
                    bonded_parent_uuid=p.get("bonded_parent_uuid"),
                )
            )

        root_uuid = "RINCON_542A1B63FE6E01400"
        designated_root = players_raw[root_uuid]["designated_root"] or EXPECTED_STP_ROOT
        return HouseholdSonosSnapshot(
            batch_id=f"live-{uuid.uuid4().hex[:10]}",
            captured_at=datetime.now(timezone.utc),
            consumer_id=consumer_id,
            designated_stp_root=f"{designated_root} (Wohnzimmer_Bookshelf 192.168.10.230)",
            is_root_healthy=(designated_root == EXPECTED_STP_ROOT),
            total_players=len(player_dtos),
            reachable_players=sum(1 for p in player_dtos if p.is_reachable),
            ghost_group_count=len(ghost_zones),
            has_ghost_groups=len(ghost_zones) > 0,
            ghost_group_zones=ghost_zones,
            players=player_dtos,
            mesh_links=mesh_links,
        )

    async def flush_ghost_groups(
        self, zone_ips: list[str] | None = None
    ) -> GhostFlushResult:
        results: list[GhostFlushZoneResult] = []
        flushed_zones: list[str] = []
        target_ips = set(zone_ips) if zone_ips else None

        for r_uuid, st in self._state_by_uuid.items():
            if st.get("bonded_parent_uuid"):
                continue
            ip = st.get("ip_address") or ""
            if target_ips is not None and ip not in target_ips:
                continue
            prev_gid = st.get("group_id", "")
            id_prefix = prev_gid.split(":")[0] if ":" in prev_gid else prev_gid
            coord = st.get("coordinator_uuid", r_uuid)
            is_ghost = (id_prefix != coord) or bool(st.get("has_vanished_devices"))

            if is_ghost or target_ips is not None:
                self._group_counter += 1
                new_gid = f"{r_uuid}:{self._group_counter}"
                st["group_id"] = new_gid
                st["coordinator_uuid"] = r_uuid
                st["has_vanished_devices"] = False
                flushed_zones.append(st["zone_name"])
                results.append(
                    GhostFlushZoneResult(
                        zone_name=st["zone_name"],
                        rincon_uuid=r_uuid,
                        ip_address=ip,
                        previous_group_id=prev_gid,
                        new_group_id=new_gid,
                        status="SANITIZED",
                    )
                )
            else:
                results.append(
                    GhostFlushZoneResult(
                        zone_name=st["zone_name"],
                        rincon_uuid=r_uuid,
                        ip_address=ip,
                        previous_group_id=prev_gid,
                        new_group_id=prev_gid,
                        status="CLEAN",
                    )
                )

        # Keep bonded satellites synchronized with Beam's group ID
        beam_gid = self._state_by_uuid["RINCON_949F3EC0EEA101400"]["group_id"]
        for sat_uuid in ("RINCON_5CAAFD490CCA01400", "RINCON_949F3E00292E01400"):
            self._state_by_uuid[sat_uuid]["group_id"] = beam_gid
            self._state_by_uuid[sat_uuid]["coordinator_uuid"] = "RINCON_949F3EC0EEA101400"
            self._state_by_uuid[sat_uuid]["has_vanished_devices"] = False

        return GhostFlushResult(
            flushed_count=len(flushed_zones),
            flushed_zones=flushed_zones,
            results=results,
            captured_at=datetime.now(timezone.utc),
        )

    async def stream_room_rf_velocity(
        self,
        room_id: str,
        interval_sec: float = 2.0,
        consumer_id: str = "ws-default",
        max_iterations: int | None = None,
    ) -> AsyncIterator[list[PlayerRfSample]]:
        room_norm = room_id.lower()
        count = 0
        while max_iterations is None or count < max_iterations:
            snap = await self.collect_household_snapshot(consumer_id=consumer_id)
            samples: list[PlayerRfSample] = []
            for p in snap.players:
                meta_slug = UUID_TO_META.get(p.rincon_uuid, {}).get("room_slug", "")
                if (
                    room_norm in ("all", "")
                    or room_norm == meta_slug
                    or room_norm in p.zone_name.lower()
                    or (p.room_id and p.room_id.lower() == room_norm)
                ):
                    samples.append(
                        PlayerRfSample(
                            rincon_uuid=p.rincon_uuid,
                            zone_name=p.zone_name,
                            room_id=p.room_id or meta_slug,
                            ip_address=p.ip_address,
                            ieee_channel=p.ieee_channel,
                            ofdm_ani_level=p.ofdm_ani_level,
                            noise_floor_dbm=p.noise_floor_dbm,
                            phy_error_total=p.phy_error_total,
                            phy_error_rate=p.phy_error_rate or 0.0,
                            captured_at=snap.captured_at,
                        )
                    )
            yield samples
            count += 1
            if max_iterations is None or count < max_iterations:
                await self._wait_interval(interval_sec)


def _default_http_caller(
    url: str,
    method: str = "GET",
    body: str | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 2.5,
) -> str:
    data = body.encode("utf-8") if body is not None else None
    req_headers = {"User-Agent": "SonosNetworkPlatform/1.0", **(headers or {})}
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


class HttpSonosAdapter:
    """
    Live HTTP/UPnP Sonos adapter polling `:1400` endpoints with cross-VLAN-safe
    concurrency (`max_workers <= 14`, `timeout >= 2.0s`).
    """

    def __init__(
        self,
        max_workers: int = 12,
        timeout_sec: float = 2.5,
        probe_interval_sec: float = 1.5,
        http_caller: Callable[..., str] | None = None,
    ) -> None:
        self.max_workers = min(max(1, max_workers), 14)
        self.timeout_sec = max(2.0, timeout_sec)
        self.probe_interval_sec = probe_interval_sec
        self._http_caller = http_caller or _default_http_caller
        self._cursor_tracker = _PhyErrorCursorTracker()

    def _poll_single_player(
        self, meta: dict[str, Any], zg_info: dict[str, Any]
    ) -> tuple[dict[str, Any], list[SonosMeshLinkDto], int | None]:
        r_uuid = meta["rincon_uuid"]
        ip = zg_info.get("ip_address") or meta.get("ip_address")
        if not ip:
            return {**meta, "is_reachable": False}, [], None

        base_url = f"http://{ip}:1400"
        try:
            ath_text = self._http_caller(
                f"{base_url}/status/proc/ath_rincon/status", timeout=self.timeout_sec
            )
            stp_text = self._http_caller(
                f"{base_url}/status/showstp", timeout=self.timeout_sec
            )
            wireless_text = self._http_caller(
                f"{base_url}/status/wireless", timeout=self.timeout_sec
            )
            enet_text = self._http_caller(
                f"{base_url}/status/enetports", timeout=self.timeout_sec
            )
            vol_xml = self._http_caller(
                f"{base_url}/MediaRenderer/RenderingControl/Control",
                method="POST",
                body=SOAP_GET_VOLUME,
                headers={
                    "Content-Type": 'text/xml; charset="utf-8"',
                    "SOAPAction": '"urn:schemas-upnp-org:service:RenderingControl:1#GetVolume"',
                },
                timeout=self.timeout_sec,
            )
        except Exception:
            return {**meta, "ip_address": ip, "is_reachable": False}, [], None

        ath = parse_ath_rincon_status(
            ath_text,
            source_uuid=r_uuid,
            source_bssid=meta.get("sonosnet_bssid"),
            bssid_to_uuid=BSSID_TO_UUID,
        )
        stp = parse_showstp(stp_text)

        vol_m = re.search(r"<CurrentVolume>(\d+)</CurrentVolume>", vol_xml)
        volume = int(vol_m.group(1)) if vol_m else meta.get("master_volume")

        is_sat = bool(zg_info.get("is_satellite")) or bool(meta.get("bonded_parent_uuid"))
        if is_sat:
            conn_mode = ConnectionMode.HT_SATELLITE
        elif "100FD" in enet_text or "1000FD" in enet_text:
            conn_mode = (
                ConnectionMode.ETHERNET_ROOT
                if stp.get("stp_path_cost") == 0
                else ConnectionMode.ETHERNET_NODE
            )
        elif "STATION_MODE" in wireless_text or "INFRA" in wireless_text:
            conn_mode = ConnectionMode.STATION_MODE
        else:
            conn_mode = meta["connection_mode"]

        links: list[SonosMeshLinkDto] = []
        for l in ath["links"]:
            links.append(
                SonosMeshLinkDto(
                    source_rincon_uuid=l["source_rincon_uuid"],
                    target_rincon_uuid=l["target_rincon_uuid"],
                    source_zone_name=meta["zone_name"],
                    target_zone_name=UUID_TO_META.get(l["target_rincon_uuid"], {}).get("zone_name"),
                    source_bssid=l["source_bssid"],
                    target_bssid=l["target_bssid"],
                    channel=48 if is_sat else l["channel"],
                    from_db=l["from_db"],
                    to_db=l["to_db"],
                    stp_state=l["stp_state"],
                )
            )
        if is_sat and not links:
            parent_uuid = zg_info.get("bonded_parent_uuid") or meta.get("bonded_parent_uuid")
            if parent_uuid:
                links.append(
                    SonosMeshLinkDto(
                        source_rincon_uuid=r_uuid,
                        target_rincon_uuid=parent_uuid,
                        source_zone_name=meta["zone_name"],
                        target_zone_name=UUID_TO_META.get(parent_uuid, {}).get("zone_name"),
                        source_bssid=meta.get("sonosnet_bssid"),
                        target_bssid=UUID_TO_META.get(parent_uuid, {}).get("sonosnet_bssid"),
                        channel=48,
                        from_db=60,
                        to_db=66,
                        stp_state=StpPortState.FORWARDING.value,
                    )
                )

        player_dict = {
            **meta,
            "ip_address": ip,
            "is_reachable": True,
            "connection_mode": conn_mode,
            "ieee_channel": 48 if is_sat else (ath["ieee_channel"] or meta.get("ieee_channel")),
            "ofdm_ani_level": ath["ofdm_ani_level"],
            "noise_floor_dbm": ath["noise_floor_dbm"],
            "phy_error_total": ath["phy_error_total"],
            "designated_root": stp["designated_root"] or meta.get("designated_root"),
            "stp_root_port": stp["stp_root_port"] or meta.get("stp_root_port"),
            "stp_path_cost": (
                stp["stp_path_cost"]
                if stp["stp_path_cost"] is not None
                else meta.get("stp_path_cost")
            ),
            "group_id": zg_info.get("group_id", f"{r_uuid}:1"),
            "coordinator_uuid": zg_info.get("coordinator_uuid", r_uuid),
            "has_vanished_devices": zg_info.get("has_vanished_devices", False),
            "is_ghost_group": zg_info.get("is_ghost_group", False),
            "master_volume": volume,
            "bonded_parent_uuid": zg_info.get("bonded_parent_uuid") or meta.get("bonded_parent_uuid"),
        }
        return player_dict, links, ath["phy_error_total"]

    def _poll_household_sync(self) -> tuple[dict[str, dict[str, Any]], list[SonosMeshLinkDto], dict[str, int | None]]:
        anchor_ip = "192.168.10.230"
        try:
            zgs_xml = self._http_caller(
                f"http://{anchor_ip}:1400/ZoneGroupTopology/Control",
                method="POST",
                body=SOAP_GET_ZONE_GROUP_STATE,
                headers={
                    "Content-Type": 'text/xml; charset="utf-8"',
                    "SOAPAction": '"urn:schemas-upnp-org:service:ZoneGroupTopology:1#GetZoneGroupState"',
                },
                timeout=self.timeout_sec,
            )
            zgs_map = parse_zone_group_state(zgs_xml)
        except Exception:
            zgs_map = {}

        players_raw: dict[str, dict[str, Any]] = {}
        mesh_links: list[SonosMeshLinkDto] = []
        raw_phy: dict[str, int | None] = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                meta["rincon_uuid"]: executor.submit(
                    self._poll_single_player, meta, zgs_map.get(meta["rincon_uuid"], {})
                )
                for meta in MASTER_SONOS_INVENTORY
            }
            for r_uuid, fut in futures.items():
                p_dict, p_links, phy_val = fut.result()
                players_raw[r_uuid] = p_dict
                mesh_links.extend(p_links)
                raw_phy[r_uuid] = phy_val

        return players_raw, mesh_links, raw_phy

    async def collect_household_snapshot(
        self, consumer_id: str = "on-demand"
    ) -> HouseholdSonosSnapshot:
        t1 = time.monotonic()
        players_raw, mesh_links, raw_phy_1 = await asyncio.to_thread(self._poll_household_sync)

        if self._cursor_tracker.needs_cold_probe(consumer_id, raw_phy_1, t1):
            self._cursor_tracker.seed_cursor_sample(consumer_id, raw_phy_1, t1)
            if self.probe_interval_sec > 0:
                await asyncio.sleep(self.probe_interval_sec)
            t2 = max(time.monotonic(), t1 + max(self.probe_interval_sec, 0.001))
            players_raw, mesh_links, raw_phy_2 = await asyncio.to_thread(self._poll_household_sync)
            rates = self._cursor_tracker.compute_rates_and_advance(
                consumer_id, raw_phy_2, t2
            )
        else:
            rates = self._cursor_tracker.compute_rates_and_advance(
                consumer_id, raw_phy_1, t1
            )

        player_dtos: list[PlayerTelemetryDto] = []
        ghost_zones: list[str] = []
        for r_uuid, p in players_raw.items():
            if p.get("is_ghost_group"):
                ghost_zones.append(p["zone_name"])
            player_dtos.append(
                PlayerTelemetryDto(
                    rincon_uuid=r_uuid,
                    zone_name=p["zone_name"],
                    room_name=p.get("room_name"),
                    ip_address=p.get("ip_address"),
                    base_mac=p.get("base_mac"),
                    sonosnet_bssid=p.get("sonosnet_bssid"),
                    is_reachable=p.get("is_reachable", True),
                    connection_mode=p["connection_mode"],
                    ieee_channel=p.get("ieee_channel"),
                    ofdm_ani_level=p.get("ofdm_ani_level"),
                    noise_floor_dbm=p.get("noise_floor_dbm"),
                    phy_error_total=p.get("phy_error_total"),
                    phy_error_rate=rates.get(r_uuid, 0.0),
                    designated_root=p.get("designated_root"),
                    stp_root_port=p.get("stp_root_port"),
                    stp_path_cost=p.get("stp_path_cost"),
                    group_id=p.get("group_id"),
                    coordinator_uuid=p.get("coordinator_uuid"),
                    has_vanished_devices=p.get("has_vanished_devices", False),
                    is_ghost_group=p.get("is_ghost_group", False),
                    master_volume=p.get("master_volume"),
                    ping_rtt_ms=p.get("ping_rtt_ms"),
                    bonded_parent_uuid=p.get("bonded_parent_uuid"),
                )
            )

        designated_root = (
            players_raw["RINCON_542A1B63FE6E01400"].get("designated_root")
            or EXPECTED_STP_ROOT
        )
        return HouseholdSonosSnapshot(
            batch_id=f"http-{uuid.uuid4().hex[:10]}",
            captured_at=datetime.now(timezone.utc),
            consumer_id=consumer_id,
            designated_stp_root=f"{designated_root} (Wohnzimmer_Bookshelf 192.168.10.230)",
            is_root_healthy=(designated_root == EXPECTED_STP_ROOT),
            total_players=len(player_dtos),
            reachable_players=sum(1 for p in player_dtos if p.is_reachable),
            ghost_group_count=len(ghost_zones),
            has_ghost_groups=len(ghost_zones) > 0,
            ghost_group_zones=ghost_zones,
            players=player_dtos,
            mesh_links=mesh_links,
        )

    async def flush_ghost_groups(
        self, zone_ips: list[str] | None = None
    ) -> GhostFlushResult:
        target_ips = set(zone_ips) if zone_ips else None
        results: list[GhostFlushZoneResult] = []
        flushed_zones: list[str] = []

        for meta in MASTER_SONOS_INVENTORY:
            if meta.get("bonded_parent_uuid"):
                continue
            ip = meta.get("ip_address")
            if not ip or (target_ips is not None and ip not in target_ips):
                continue
            r_uuid = meta["rincon_uuid"]
            try:
                resp_xml = await asyncio.to_thread(
                    self._http_caller,
                    f"http://{ip}:1400/MediaRenderer/AVTransport/Control",
                    "POST",
                    SOAP_STANDALONE_GROUP,
                    {
                        "Content-Type": 'text/xml; charset="utf-8"',
                        "SOAPAction": '"urn:schemas-upnp-org:service:AVTransport:1#BecomeCoordinatorOfStandaloneGroup"',
                    },
                    self.timeout_sec,
                )
                gid_m = re.search(r"<NewGroupID>([^<]+)</NewGroupID>", resp_xml)
                new_gid = gid_m.group(1) if gid_m else f"{r_uuid}:1"
                flushed_zones.append(meta["zone_name"])
                results.append(
                    GhostFlushZoneResult(
                        zone_name=meta["zone_name"],
                        rincon_uuid=r_uuid,
                        ip_address=ip,
                        previous_group_id=None,
                        new_group_id=new_gid,
                        status="SANITIZED",
                    )
                )
            except Exception:
                results.append(
                    GhostFlushZoneResult(
                        zone_name=meta["zone_name"],
                        rincon_uuid=r_uuid,
                        ip_address=ip,
                        previous_group_id=None,
                        new_group_id=f"{r_uuid}:0",
                        status="FAILED",
                    )
                )

        return GhostFlushResult(
            flushed_count=len(flushed_zones),
            flushed_zones=flushed_zones,
            results=results,
            captured_at=datetime.now(timezone.utc),
        )

    async def stream_room_rf_velocity(
        self,
        room_id: str,
        interval_sec: float = 2.0,
        consumer_id: str = "ws-default",
        max_iterations: int | None = None,
    ) -> AsyncIterator[list[PlayerRfSample]]:
        room_norm = room_id.lower()
        count = 0
        while max_iterations is None or count < max_iterations:
            snap = await self.collect_household_snapshot(consumer_id=consumer_id)
            samples = [
                PlayerRfSample(
                    rincon_uuid=p.rincon_uuid,
                    zone_name=p.zone_name,
                    room_id=p.room_id,
                    ip_address=p.ip_address,
                    ieee_channel=p.ieee_channel,
                    ofdm_ani_level=p.ofdm_ani_level,
                    noise_floor_dbm=p.noise_floor_dbm,
                    phy_error_total=p.phy_error_total,
                    phy_error_rate=p.phy_error_rate or 0.0,
                    captured_at=snap.captured_at,
                )
                for p in snap.players
                if room_norm in ("all", "") or room_norm in p.zone_name.lower()
            ]
            yield samples
            count += 1
            if max_iterations is None or count < max_iterations:
                await asyncio.sleep(interval_sec)
