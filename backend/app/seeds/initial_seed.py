from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import (
    AccessPointRadio,
    BssidReading,
    ConnectionMode,
    DeviceRole,
    Floor,
    HealthGrade,
    NetworkDevice,
    Room,
    SonosMeshLink,
    SonosTelemetrySnapshot,
    StpPortState,
    SwitchPort,
    WiFiRoomSurvey,
)
from app.modules.sonos_telemetry import MASTER_SONOS_INVENTORY
from app.modules.wifi_omada import MASTER_AP_RADIOS, build_wifi_room_survey
from app.schemas.topology import BssidReadingInput




SEED_FLOORS = [
    {"slug": "keller", "name": "Keller", "level_order": 0},
    {"slug": "erdgeschoss", "name": "Erdgeschoss", "level_order": 1},
    {"slug": "obergeschoss", "name": "Obergeschoss", "level_order": 2},
    {"slug": "dachgeschoss", "name": "Dachgeschoss", "level_order": 3},
]

SEED_ROOMS = [
    {
        "slug": "keller",
        "name": "Keller",
        "floor_slug": "keller",
        "pos_x": 200.0,
        "pos_y": 700.0,
        "health_grade": HealthGrade.GOOD.value,
        "best_5ghz_rssi_dbm": -68,
        "best_24ghz_rssi_dbm": -63,
        "description": "Basement utility & storage; Play:3 wireless leaf (unplugged from Ethernet to prevent basement root trap).",
    },
    {
        "slug": "wohnzimmer",
        "name": "Wohnzimmer",
        "floor_slug": "erdgeschoss",
        "pos_x": 150.0,
        "pos_y": 450.0,
        "health_grade": HealthGrade.MARGINAL.value,
        "best_5ghz_rssi_dbm": -54,
        "best_24ghz_rssi_dbm": -52,
        "description": "Ground-floor living room; hosts wired STP Root Bridge (Wohnzimmer_Bookshelf .230) and two Play:1 units.",
    },
    {
        "slug": "fernsehecke",
        "name": "Fernsehecke",
        "floor_slug": "erdgeschoss",
        "pos_x": 400.0,
        "pos_y": 450.0,
        "health_grade": HealthGrade.EXCELLENT.value,
        "best_5ghz_rssi_dbm": -55,
        "best_24ghz_rssi_dbm": -58,
        "description": "Home Theater zone; Sonos Beam (Ch 6 + 5 GHz Ch 48 HT master) with LR and bonded RR surrounds.",
    },
    {
        "slug": "kueche",
        "name": "Küche",
        "floor_slug": "erdgeschoss",
        "pos_x": 650.0,
        "pos_y": 450.0,
        "health_grade": HealthGrade.EXCELLENT.value,
        "best_5ghz_rssi_dbm": -55,
        "best_24ghz_rssi_dbm": -55,
        "description": "Ground-floor kitchen; Epson ET-4850 Wi-Fi Direct disabled -> OFDM ANI 0.",
    },
    {
        "slug": "bueroecke",
        "name": "Büroecke",
        "floor_slug": "erdgeschoss",
        "pos_x": 850.0,
        "pos_y": 450.0,
        "health_grade": HealthGrade.EXCELLENT.value,
        "best_5ghz_rssi_dbm": -52,
        "best_24ghz_rssi_dbm": -56,
        "description": "Ground-floor office corner; strong 63 dB SNR link to Beam.",
    },
    {
        "slug": "galerie",
        "name": "Galerie",
        "floor_slug": "obergeschoss",
        "pos_x": 400.0,
        "pos_y": 250.0,
        "health_grade": HealthGrade.EXCELLENT.value,
        "best_5ghz_rssi_dbm": -45,
        "best_24ghz_rssi_dbm": -48,
        "description": "Upper landing hosting primary Galerie EAP650 (2.4G Ch 1, 5G Ch 44 @ 80 MHz).",
    },
    {
        "slug": "elternschlafzimmer",
        "name": "Elternschlafzimmer",
        "floor_slug": "obergeschoss",
        "pos_x": 150.0,
        "pos_y": 250.0,
        "health_grade": HealthGrade.GOOD.value,
        "best_5ghz_rssi_dbm": -52,
        "best_24ghz_rssi_dbm": -55,
        "description": "Master bedroom hosting Sonos zone 'Eltern' (.131).",
    },
    {
        "slug": "elternbad",
        "name": "Elternbad",
        "floor_slug": "obergeschoss",
        "pos_x": 50.0,
        "pos_y": 250.0,
        "health_grade": HealthGrade.GOOD.value,
        "best_5ghz_rssi_dbm": -55,
        "best_24ghz_rssi_dbm": -60,
        "description": "Master bathroom; 1201 Mbps Wi-Fi 6 on Galerie Ch 44; dense 58 dB link to Eltern.",
    },
    {
        "slug": "noemi",
        "name": "Noemi",
        "floor_slug": "obergeschoss",
        "pos_x": 650.0,
        "pos_y": 250.0,
        "health_grade": HealthGrade.MARGINAL.value,
        "best_5ghz_rssi_dbm": -72,
        "best_24ghz_rssi_dbm": -70,
        "description": "Bedroom with wall jack patched to Switch Port 6 (Untagged VLAN 10).",
    },
    {
        "slug": "noah",
        "name": "Noah",
        "floor_slug": "obergeschoss",
        "pos_x": 850.0,
        "pos_y": 250.0,
        "health_grade": HealthGrade.GOOD.value,
        "best_5ghz_rssi_dbm": -57,
        "best_24ghz_rssi_dbm": -60,
        "description": "Bedroom with wall jack patched to Switch Port 7 (Untagged VLAN 10).",
    },
    {
        "slug": "nicolas",
        "name": "Nicolas",
        "floor_slug": "dachgeschoss",
        "pos_x": 500.0,
        "pos_y": 80.0,
        "health_grade": HealthGrade.EXCELLENT.value,
        "best_5ghz_rssi_dbm": -72,
        "best_24ghz_rssi_dbm": -82,
        "description": "Attic bedroom; SYMFONISK on 5 GHz Wi-Fi Ch 44 (ANI 0, 2.3ms) + Wall Jack Port 5 (VLAN 10).",
    },
]

SEED_SWITCH_PORTS = [
    {
        "port_number": 1,
        "pvid": 1,
        "untagged_vlans": "1",
        "tagged_vlans": "10,20,30",
        "room_slug": "keller",
        "connected_device_label": "Firewalla Purple VLAN Trunk Uplink",
    },
    {
        "port_number": 5,
        "pvid": 10,
        "untagged_vlans": "10",
        "tagged_vlans": "",
        "room_slug": "nicolas",
        "connected_device_label": "Nicolas Wall Jack (VLAN 10)",
    },
    {
        "port_number": 6,
        "pvid": 10,
        "untagged_vlans": "10",
        "tagged_vlans": "",
        "room_slug": "noemi",
        "connected_device_label": "Noemi Wall Jack (VLAN 10)",
    },
    {
        "port_number": 7,
        "pvid": 10,
        "untagged_vlans": "10",
        "tagged_vlans": "",
        "room_slug": "noah",
        "connected_device_label": "Noah Wall Jack (VLAN 10)",
    },
    {
        "port_number": 8,
        "pvid": 1,
        "untagged_vlans": "1",
        "tagged_vlans": "",
        "room_slug": "bueroecke",
        "connected_device_label": "Always-On Mini PC (192.168.55.60)",
    },
    {
        "port_number": 11,
        "pvid": 1,
        "untagged_vlans": "1",
        "tagged_vlans": "10,20,30",
        "room_slug": "galerie",
        "connected_device_label": "Galerie EAP650 PoE Trunk",
    },
    {
        "port_number": 12,
        "pvid": 1,
        "untagged_vlans": "1",
        "tagged_vlans": "10,20,30",
        "room_slug": "kueche",
        "connected_device_label": "Kitchen EAP650 PoE Trunk",
    },
    {
        "port_number": 13,
        "pvid": 10,
        "untagged_vlans": "10",
        "tagged_vlans": "",
        "room_slug": "wohnzimmer",
        "connected_device_label": "Wohnzimmer_Bookshelf (Wired STP Root Bridge)",
    },
    {
        "port_number": 14,
        "pvid": 1,
        "untagged_vlans": "1",
        "tagged_vlans": "10,20,30",
        "room_slug": "wohnzimmer",
        "connected_device_label": "Retired EAP330 Port (Powered Off)",
    },
    {
        "port_number": 15,
        "pvid": 1,
        "untagged_vlans": "1",
        "tagged_vlans": "10,20,30",
        "room_slug": "keller",
        "connected_device_label": "Retired Keller AP Port (Powered Off)",
    },
]

SEED_DEVICES = [
    # --- 14 SONOS PLAYERS (5 Oct 2026 Post-Remediation State) ---
    {
        "slug": "sonos-wohnzimmer-bookshelf",
        "name": "Wohnzimmer_Bookshelf",
        "device_role": DeviceRole.SONOS_PLAYER.value,
        "model_name": "SYMFONISK Bookshelf",
        "ip_address": "192.168.10.230",
        "base_mac": "54:2A:1B:63:FE:6E",
        "sonosnet_bssid": "54:2A:1B:63:FE:6F",
        "rincon_uuid": "RINCON_542A1B63FE6E01400",
        "connection_mode": ConnectionMode.ETHERNET_ROOT.value,
        "health_grade": HealthGrade.EXCELLENT.value,
        "ofdm_ani_level": 6,
        "room_slug": "wohnzimmer",
        "port_number": 13,
        "notes": "Active Wired STP Root Bridge (9000.542a1b63fe6e, Cost 0)",
        "is_archived": False,
    },
    {
        "slug": "sonos-wohnzimmer-esstisch",
        "name": "Wohnzimmer_Esstisch",
        "device_role": DeviceRole.SONOS_PLAYER.value,
        "model_name": "Sonos Play:1",
        "ip_address": "192.168.10.160",
        "base_mac": "B8:E9:37:E6:09:84",
        "sonosnet_bssid": "B8:E9:37:E6:09:85",
        "rincon_uuid": "RINCON_B8E937E6098401400",
        "connection_mode": ConnectionMode.SONOSNET_MODE.value,
        "health_grade": HealthGrade.CRITICAL.value,
        "ofdm_ani_level": 9,
        "room_slug": "wohnzimmer",
        "port_number": None,
        "notes": "SonosNet Ch 6 direct to Root; experiences non-Wi-Fi EMI from Galerie above",
        "is_archived": False,
    },
    {
        "slug": "sonos-wohnzimmer-buchregal",
        "name": "Wohnzimmer_Buchregal",
        "device_role": DeviceRole.SONOS_PLAYER.value,
        "model_name": "Sonos Play:1",
        "ip_address": "192.168.10.101",
        "base_mac": "B8:E9:37:E5:15:2A",
        "sonosnet_bssid": "B8:E9:37:E5:15:2B",
        "rincon_uuid": "RINCON_B8E937E5152A01400",
        "connection_mode": ConnectionMode.SONOSNET_MODE.value,
        "health_grade": HealthGrade.CRITICAL.value,
        "ofdm_ani_level": 9,
        "room_slug": "wohnzimmer",
        "port_number": None,
        "notes": "SonosNet Ch 6 direct to Root; experiences non-Wi-Fi EMI from Galerie desk above",
        "is_archived": False,
    },
    {
        "slug": "sonos-fernsehecke-beam",
        "name": "Fernsehecke (LF,RF)",
        "device_role": DeviceRole.SONOS_PLAYER.value,
        "model_name": "Sonos Beam",
        "ip_address": "192.168.10.241",
        "base_mac": "94:9F:3E:C0:EE:A1",
        "sonosnet_bssid": "94:9F:3E:C0:EE:A2",
        "rincon_uuid": "RINCON_949F3EC0EEA101400",
        "connection_mode": ConnectionMode.SONOSNET_MODE.value,
        "health_grade": HealthGrade.EXCELLENT.value,
        "ofdm_ani_level": None,
        "room_slug": "fernsehecke",
        "port_number": None,
        "notes": "SonosNet Ch 6 + 5 GHz HT Master (Ch 48)",
        "is_archived": False,
    },
    {
        "slug": "sonos-fernsehecke-lr",
        "name": "Fernsehecke (LR)",
        "device_role": DeviceRole.SONOS_PLAYER.value,
        "model_name": "Sonos Play:1",
        "ip_address": "192.168.10.102",
        "base_mac": "5C:AA:FD:49:0C:CA",
        "sonosnet_bssid": "5C:AA:FD:49:0C:CB",
        "rincon_uuid": "RINCON_5CAAFD490CCA01400",
        "connection_mode": ConnectionMode.HT_SATELLITE.value,
        "health_grade": HealthGrade.EXCELLENT.value,
        "ofdm_ani_level": 0,
        "room_slug": "fernsehecke",
        "port_number": None,
        "notes": "Home Theater Left Surround Satellite (5 GHz Ch 48 to Beam)",
        "is_archived": False,
    },
    {
        "slug": "sonos-fernsehecke-rr",
        "name": "Fernsehecke (RR)",
        "device_role": DeviceRole.SONOS_PLAYER.value,
        "model_name": "Sonos One / Play:1",
        "ip_address": None,
        "base_mac": "94:9F:3E:00:29:2E",
        "sonosnet_bssid": "94:9F:3E:00:29:2F",
        "rincon_uuid": "RINCON_949F3E00292E01400",
        "connection_mode": ConnectionMode.HT_SATELLITE.value,
        "health_grade": HealthGrade.GOOD.value,
        "ofdm_ani_level": 0,
        "room_slug": "fernsehecke",
        "port_number": None,
        "notes": "Bonded Home Theater Right Surround Satellite (5 GHz Ch 48 to Beam)",
        "is_archived": False,
    },
    {
        "slug": "sonos-keller",
        "name": "Keller",
        "device_role": DeviceRole.SONOS_PLAYER.value,
        "model_name": "Sonos Play:3",
        "ip_address": "192.168.10.217",
        "base_mac": "5C:AA:FD:59:5E:EA",
        "sonosnet_bssid": "5C:AA:FD:59:5E:EB",
        "rincon_uuid": "RINCON_5CAAFD595EEA01400",
        "connection_mode": ConnectionMode.SONOSNET_MODE.value,
        "health_grade": HealthGrade.GOOD.value,
        "ofdm_ani_level": 5,
        "room_slug": "keller",
        "port_number": None,
        "notes": "SonosNet Wireless Leaf (Unplugged from Ethernet to prevent basement root trap)",
        "is_archived": False,
    },
    {
        "slug": "sonos-kueche",
        "name": "Küche",
        "device_role": DeviceRole.SONOS_PLAYER.value,
        "model_name": "SYMFONISK Bookshelf",
        "ip_address": "192.168.10.202",
        "base_mac": "34:7E:5C:38:26:E2",
        "sonosnet_bssid": "34:7E:5C:38:26:E3",
        "rincon_uuid": "RINCON_347E5C3826E201400",
        "connection_mode": ConnectionMode.SONOSNET_MODE.value,
        "health_grade": HealthGrade.EXCELLENT.value,
        "ofdm_ani_level": 0,
        "room_slug": "kueche",
        "port_number": None,
        "notes": "SonosNet Wireless (Ch 6), OFDM ANI 0 after disabling Epson Wi-Fi Direct",
        "is_archived": False,
    },
    {
        "slug": "sonos-bueroecke",
        "name": "Büroecke",
        "device_role": DeviceRole.SONOS_PLAYER.value,
        "model_name": "SYMFONISK Bookshelf",
        "ip_address": "192.168.10.151",
        "base_mac": "34:7E:5C:35:B0:F4",
        "sonosnet_bssid": "34:7E:5C:35:B0:F5",
        "rincon_uuid": "RINCON_347E5C35B0F401400",
        "connection_mode": ConnectionMode.SONOSNET_MODE.value,
        "health_grade": HealthGrade.EXCELLENT.value,
        "ofdm_ani_level": 0,
        "room_slug": "bueroecke",
        "port_number": None,
        "notes": "SonosNet Wireless (Ch 6, Direct to Root/Beam)",
        "is_archived": False,
    },
    {
        "slug": "sonos-noah",
        "name": "Noah",
        "device_role": DeviceRole.SONOS_PLAYER.value,
        "model_name": "SYMFONISK Bookshelf",
        "ip_address": "192.168.10.229",
        "base_mac": "34:7E:5C:35:B2:C0",
        "sonosnet_bssid": "34:7E:5C:35:B2:C1",
        "rincon_uuid": "RINCON_347E5C35B2C001400",
        "connection_mode": ConnectionMode.SONOSNET_MODE.value,
        "health_grade": HealthGrade.GOOD.value,
        "ofdm_ani_level": 4,
        "room_slug": "noah",
        "port_number": 7,
        "notes": "SonosNet Wireless (Ch 6) — Wall port patched to Switch Port 7 (VLAN 10)",
        "is_archived": False,
    },
    {
        "slug": "sonos-noemi",
        "name": "Noemi",
        "device_role": DeviceRole.SONOS_PLAYER.value,
        "model_name": "SYMFONISK Bookshelf",
        "ip_address": "192.168.10.244",
        "base_mac": "54:2A:1B:64:26:80",
        "sonosnet_bssid": "54:2A:1B:64:26:81",
        "rincon_uuid": "RINCON_542A1B64268001400",
        "connection_mode": ConnectionMode.SONOSNET_MODE.value,
        "health_grade": HealthGrade.MARGINAL.value,
        "ofdm_ani_level": 5,
        "room_slug": "noemi",
        "port_number": 6,
        "notes": "SonosNet Wireless (Ch 6) — Wall port patched to Switch Port 6 (VLAN 10)",
        "is_archived": False,
    },
    {
        "slug": "sonos-nicolas",
        "name": "Nicolas",
        "device_role": DeviceRole.SONOS_PLAYER.value,
        "model_name": "SYMFONISK Bookshelf",
        "ip_address": "192.168.10.165",
        "base_mac": "34:7E:5C:36:DE:90",
        "sonosnet_bssid": "34:7E:5C:36:DE:91",
        "rincon_uuid": "RINCON_347E5C36DE9001400",
        "connection_mode": ConnectionMode.STATION_MODE.value,
        "health_grade": HealthGrade.EXCELLENT.value,
        "ofdm_ani_level": 0,
        "room_slug": "nicolas",
        "port_number": 5,
        "notes": "Wi-Fi Station (5 GHz Ch 44) — Wall port patched to Switch Port 5 (VLAN 10)",
        "is_archived": False,
    },
    {
        "slug": "sonos-eltern",
        "name": "Eltern",
        "device_role": DeviceRole.SONOS_PLAYER.value,
        "model_name": "SYMFONISK Bookshelf",
        "ip_address": "192.168.10.131",
        "base_mac": "34:7E:5C:38:28:B0",
        "sonosnet_bssid": "34:7E:5C:38:28:B1",
        "rincon_uuid": "RINCON_347E5C3828B001400",
        "connection_mode": ConnectionMode.SONOSNET_MODE.value,
        "health_grade": HealthGrade.GOOD.value,
        "ofdm_ani_level": 4,
        "room_slug": "elternschlafzimmer",
        "port_number": None,
        "notes": "Sonos zone 'Eltern' mapped to physical room Elternschlafzimmer",
        "is_archived": False,
    },
    {
        "slug": "sonos-elternbad",
        "name": "Elternbad",
        "device_role": DeviceRole.SONOS_PLAYER.value,
        "model_name": "SYMFONISK Bookshelf",
        "ip_address": "192.168.10.113",
        "base_mac": "34:7E:5C:31:CE:28",
        "sonosnet_bssid": "34:7E:5C:31:CE:29",
        "rincon_uuid": "RINCON_347E5C31CE2801400",
        "connection_mode": ConnectionMode.SONOSNET_MODE.value,
        "health_grade": HealthGrade.GOOD.value,
        "ofdm_ani_level": 4,
        "room_slug": "elternbad",
        "port_number": None,
        "notes": "SonosNet Wireless (Ch 6) in Master Bathroom",
        "is_archived": False,
    },
    # --- 2 ACTIVE MANAGED OMADA WIFI APS + 1 RETIRED EAP330 ---
    {
        "slug": "ap-galerie-eap650",
        "name": "Galerie EAP650",
        "device_role": DeviceRole.WIFI_AP.value,
        "model_name": "EAP650(EU) v1.0",
        "ip_address": "192.168.55.79",
        "base_mac": "6C:4C:BC:76:7C:40",
        "sonosnet_bssid": None,
        "rincon_uuid": None,
        "connection_mode": None,
        "health_grade": HealthGrade.EXCELLENT.value,
        "ofdm_ani_level": None,
        "room_slug": "galerie",
        "port_number": 11,
        "notes": "Omada Managed AP — 2.4 GHz Ch 1 (20 MHz) & 5 GHz Ch 44 (80 MHz, non-DFS)",
        "is_archived": False,
    },
    {
        "slug": "ap-kitchen-eap650",
        "name": "Kitchen EAP650",
        "device_role": DeviceRole.WIFI_AP.value,
        "model_name": "EAP650(EU) v1.0",
        "ip_address": "192.168.55.37",
        "base_mac": "6C:4C:BC:76:94:C0",
        "sonosnet_bssid": None,
        "rincon_uuid": None,
        "connection_mode": None,
        "health_grade": HealthGrade.GOOD.value,
        "ofdm_ani_level": None,
        "room_slug": "kueche",
        "port_number": 12,
        "notes": "Omada Managed AP — 2.4 GHz Ch 11 (20 MHz) & 5 GHz Ch 40 (40 MHz)",
        "is_archived": False,
    },
    {
        "slug": "ap-retired-eap330",
        "name": "EAP330",
        "device_role": DeviceRole.WIFI_AP.value,
        "model_name": "EAP330 hw 1.0/2.0",
        "ip_address": None,
        "base_mac": "84:16:F9:93:E9:2B",
        "sonosnet_bssid": None,
        "rincon_uuid": None,
        "connection_mode": None,
        "health_grade": HealthGrade.CRITICAL.value,
        "ofdm_ani_level": None,
        "room_slug": "wohnzimmer",
        "port_number": 14,
        "notes": "Retired standalone AP (TP-Link_5G_93E92D) — powered off to eliminate Ch 11 co-channel interference",
        "is_archived": True,
    },
    # --- CORE WIRED INFRASTRUCTURE (SWITCH & ROUTER) ---
    {
        "slug": "switch-netgear-gs316ep",
        "name": "Netgear GS316EP",
        "device_role": DeviceRole.SWITCH.value,
        "model_name": "NETGEAR GS316EP",
        "ip_address": "192.168.55.155",
        "base_mac": None,
        "sonosnet_bssid": None,
        "rincon_uuid": None,
        "connection_mode": None,
        "health_grade": HealthGrade.EXCELLENT.value,
        "ofdm_ani_level": None,
        "room_slug": "keller",
        "port_number": 1,
        "notes": "16-Port Gigabit PoE+ Smart Managed Plus Switch (BPDU Pass-Through)",
        "is_archived": False,
    },
    {
        "slug": "router-firewalla-purple",
        "name": "Firewalla Purple",
        "device_role": DeviceRole.ROUTER.value,
        "model_name": "Firewalla Purple",
        "ip_address": "192.168.55.1",
        "base_mac": None,
        "sonosnet_bssid": None,
        "rincon_uuid": None,
        "connection_mode": None,
        "health_grade": HealthGrade.EXCELLENT.value,
        "ofdm_ani_level": None,
        "room_slug": "keller",
        "port_number": 1,
        "notes": "L3 VLAN Router (VLAN 1 Admin, VLAN 10 WuTangLan-Family, VLAN 20 Guest, VLAN 30 IOT)",
        "is_archived": False,
    },
]


async def seed_initial_data(session: AsyncSession) -> None:
    """Idempotent insert-if-absent startup seeding that preserves user CRUD modifications."""
    # 1. Seed Floors
    existing_floors_res = await session.execute(select(Floor))
    floors_by_slug = {f.slug: f for f in existing_floors_res.scalars().all()}

    for f_data in SEED_FLOORS:
        if f_data["slug"] not in floors_by_slug:
            floor = Floor(
                slug=f_data["slug"],
                name=f_data["name"],
                level_order=f_data["level_order"],
                is_archived=False,
            )
            session.add(floor)
            floors_by_slug[f_data["slug"]] = floor
    await session.flush()

    # 2. Seed Rooms
    existing_rooms_res = await session.execute(select(Room))
    rooms_by_slug = {r.slug: r for r in existing_rooms_res.scalars().all()}

    for r_data in SEED_ROOMS:
        if r_data["slug"] not in rooms_by_slug:
            floor = floors_by_slug[r_data["floor_slug"]]
            room = Room(
                slug=r_data["slug"],
                name=r_data["name"],
                floor_id=floor.id,
                pos_x=r_data["pos_x"],
                pos_y=r_data["pos_y"],
                health_grade=r_data["health_grade"],
                best_5ghz_rssi_dbm=r_data["best_5ghz_rssi_dbm"],
                best_24ghz_rssi_dbm=r_data["best_24ghz_rssi_dbm"],
                description=r_data["description"],
                is_archived=False,
            )
            session.add(room)
            rooms_by_slug[r_data["slug"]] = room
    await session.flush()

    # 3. Seed SwitchPorts
    existing_ports_res = await session.execute(select(SwitchPort))
    ports_by_number = {p.port_number: p for p in existing_ports_res.scalars().all()}

    for p_data in SEED_SWITCH_PORTS:
        if p_data["port_number"] not in ports_by_number:
            room = rooms_by_slug.get(p_data["room_slug"]) if p_data["room_slug"] else None
            port = SwitchPort(
                port_number=p_data["port_number"],
                switch_name="Netgear GS316EP",
                switch_ip="192.168.55.155",
                pvid=p_data["pvid"],
                untagged_vlans=p_data["untagged_vlans"],
                tagged_vlans=p_data["tagged_vlans"],
                bpdu_policy="PASS_THROUGH",
                loop_detection_disabled=True,
                patched_room_id=room.id if room else None,
                connected_device_label=p_data["connected_device_label"],
                is_archived=False,
            )
            session.add(port)
            ports_by_number[p_data["port_number"]] = port
    await session.flush()

    # 4. Seed NetworkDevices
    existing_devs_res = await session.execute(select(NetworkDevice))
    devs_by_slug = {d.slug: d for d in existing_devs_res.scalars().all()}

    for d_data in SEED_DEVICES:
        if d_data["slug"] not in devs_by_slug:
            room = rooms_by_slug.get(d_data["room_slug"]) if d_data["room_slug"] else None
            port = (
                ports_by_number.get(d_data["port_number"])
                if d_data["port_number"] is not None
                else None
            )
            dev = NetworkDevice(
                slug=d_data["slug"],
                name=d_data["name"],
                device_role=d_data["device_role"],
                model_name=d_data["model_name"],
                ip_address=d_data["ip_address"],
                base_mac=d_data["base_mac"],
                sonosnet_bssid=d_data["sonosnet_bssid"],
                rincon_uuid=d_data["rincon_uuid"],
                connection_mode=d_data["connection_mode"],
                health_grade=d_data["health_grade"],
                ofdm_ani_level=d_data["ofdm_ani_level"],
                room_id=room.id if room else None,
                switch_port_id=port.id if port else None,
                notes=d_data["notes"],
                is_archived=d_data["is_archived"],
            )
            session.add(dev)
            devs_by_slug[d_data["slug"]] = dev
    await session.flush()

    devs_by_uuid = {
        d.rincon_uuid: d for d in devs_by_slug.values() if d.rincon_uuid is not None
    }

    # 5. Seed Historical (19 Sep 2026) and Post-Remediation Baseline (5 Oct 2026) Sonos Snapshots & Mesh Links
    existing_snaps_res = await session.execute(select(SonosTelemetrySnapshot.snapshot_key))
    existing_snap_keys = {k for k in existing_snaps_res.scalars().all() if k is not None}

    existing_links_res = await session.execute(select(SonosMeshLink.link_key))
    existing_link_keys = {k for k in existing_links_res.scalars().all() if k is not None}

    # 5a. Historical 19 Sep 2026 capture (`docs/sonos/network-matrix.md` — Keller was wired STP Root 9000.5caafd595eea)
    sep_batch_id = "hist-2026-09-19"
    sep_ts = datetime(2026, 9, 19, 22, 17, 0, tzinfo=timezone.utc)
    sep_root = "9000.5caafd595eea"
    sep_overrides: dict[str, dict[str, object]] = {
        "RINCON_5CAAFD595EEA01400": {
            "connection_mode": ConnectionMode.ETHERNET_ROOT.value,
            "ofdm_ani_level": 4,
            "noise_floor_dbm": -106,
            "stp_path_cost": 0,
            "phy_error_rate": 45.0,
            "ping_rtt_ms": 1.8,
        },
        "RINCON_542A1B63FE6E01400": {
            "connection_mode": ConnectionMode.SONOSNET_MODE.value,
            "ofdm_ani_level": 4,
            "noise_floor_dbm": -111,
            "stp_path_cost": 350,
            "phy_error_rate": 120.0,
            "ping_rtt_ms": 42.0,
        },
        "RINCON_B8E937E6098401400": {
            "connection_mode": ConnectionMode.SONOSNET_MODE.value,
            "ofdm_ani_level": 6,
            "noise_floor_dbm": -110,
            "stp_path_cost": 350,
            "phy_error_rate": 640.0,
            "ping_rtt_ms": 65.0,
        },
        "RINCON_B8E937E5152A01400": {
            "connection_mode": ConnectionMode.SONOSNET_MODE.value,
            "ofdm_ani_level": 9,
            "noise_floor_dbm": -111,
            "stp_path_cost": 450,
            "phy_error_rate": 1450.0,
            "ping_rtt_ms": 140.0,
        },
        "RINCON_949F3EC0EEA101400": {
            "connection_mode": ConnectionMode.SONOSNET_MODE.value,
            "ofdm_ani_level": None,
            "noise_floor_dbm": None,
            "stp_path_cost": 400,
            "phy_error_rate": 25.0,
            "ping_rtt_ms": 38.0,
        },
        "RINCON_5CAAFD490CCA01400": {
            "connection_mode": ConnectionMode.HT_SATELLITE.value,
            "ofdm_ani_level": 9,
            "noise_floor_dbm": -109,
            "stp_path_cost": 450,
            "phy_error_rate": 890.0,
            "ping_rtt_ms": 85.0,
        },
        "RINCON_949F3E00292E01400": {
            "connection_mode": ConnectionMode.HT_SATELLITE.value,
            "ofdm_ani_level": 8,
            "noise_floor_dbm": -108,
            "stp_path_cost": 450,
            "phy_error_rate": 720.0,
            "ping_rtt_ms": 92.0,
        },
        "RINCON_347E5C3826E201400": {
            "connection_mode": ConnectionMode.SONOSNET_MODE.value,
            "ofdm_ani_level": 0,
            "noise_floor_dbm": -112,
            "stp_path_cost": 250,
            "phy_error_rate": 18.0,
            "ping_rtt_ms": 24.0,
        },
        "RINCON_347E5C35B0F401400": {
            "connection_mode": ConnectionMode.STATION_MODE.value,
            "ofdm_ani_level": 0,
            "noise_floor_dbm": -104,
            "stp_path_cost": None,
            "phy_error_rate": 0.0,
            "ping_rtt_ms": 12.0,
        },
        "RINCON_347E5C35B2C001400": {
            "connection_mode": ConnectionMode.STATION_MODE.value,
            "ofdm_ani_level": 0,
            "noise_floor_dbm": -105,
            "stp_path_cost": None,
            "phy_error_rate": 0.0,
            "ping_rtt_ms": 19.0,
        },
        "RINCON_542A1B64268001400": {
            "connection_mode": ConnectionMode.SONOSNET_MODE.value,
            "ofdm_ani_level": 1,
            "noise_floor_dbm": -100,
            "stp_path_cost": 550,
            "phy_error_rate": 85.0,
            "ping_rtt_ms": 210.0,
        },
        "RINCON_347E5C36DE9001400": {
            "connection_mode": ConnectionMode.SONOSNET_MODE.value,
            "ofdm_ani_level": 5,
            "noise_floor_dbm": -113,
            "phy_error_total": 4987721,
            "stp_path_cost": 600,
            "phy_error_rate": 540.0,
            "ping_rtt_ms": 3900.0,
        },
        "RINCON_347E5C3828B001400": {
            "connection_mode": ConnectionMode.SONOSNET_MODE.value,
            "ofdm_ani_level": 4,
            "noise_floor_dbm": -110,
            "stp_path_cost": 550,
            "phy_error_rate": 62.0,
            "ping_rtt_ms": 120.0,
        },
        "RINCON_347E5C31CE2801400": {
            "connection_mode": ConnectionMode.SONOSNET_MODE.value,
            "ofdm_ani_level": 6,
            "noise_floor_dbm": -110,
            "stp_path_cost": 600,
            "phy_error_rate": 210.0,
            "ping_rtt_ms": 180.0,
        },
    }

    for idx, item in enumerate(MASTER_SONOS_INVENTORY, start=1):
        r_uuid = str(item["rincon_uuid"])
        s_key = f"{sep_batch_id}:{r_uuid}"
        if s_key not in existing_snap_keys:
            dev = devs_by_uuid.get(r_uuid)
            room = rooms_by_slug.get(str(item["room_slug"]))
            ov = sep_overrides.get(r_uuid, {})
            coord_uuid = str(item.get("bonded_parent_uuid") or r_uuid)
            session.add(
                SonosTelemetrySnapshot(
                    snapshot_key=s_key,
                    batch_id=sep_batch_id,
                    captured_at=sep_ts,
                    consumer_id="historical-2026-09-19",
                    device_id=dev.id if dev else None,
                    room_id=room.id if room else None,
                    rincon_uuid=r_uuid,
                    zone_name=str(item["zone_name"]),
                    ip_address=str(item["ip_address"]) if item.get("ip_address") else None,
                    base_mac=str(item["base_mac"]),
                    sonosnet_bssid=str(item["sonosnet_bssid"]),
                    is_reachable=True,
                    connection_mode=str(ov.get("connection_mode", item["connection_mode"].value)),
                    ieee_channel=int(item["ieee_channel"]) if item.get("ieee_channel") else 6,
                    ofdm_ani_level=ov.get("ofdm_ani_level"),  # type: ignore[arg-type]
                    noise_floor_dbm=ov.get("noise_floor_dbm"),  # type: ignore[arg-type]
                    phy_error_total=int(ov.get("phy_error_total", item["phy_error_total"])),  # type: ignore[arg-type]
                    phy_error_rate=float(ov.get("phy_error_rate", 0.0)),  # type: ignore[arg-type]
                    designated_root=sep_root,
                    stp_root_port="1",
                    stp_path_cost=ov.get("stp_path_cost"),  # type: ignore[arg-type]
                    group_id=f"{coord_uuid}:{idx}",
                    coordinator_uuid=coord_uuid,
                    has_vanished_devices=False,
                    is_ghost_group=False,
                    master_volume=int(item["master_volume"]),
                    ping_rtt_ms=float(ov.get("ping_rtt_ms", 15.0)),  # type: ignore[arg-type]
                    bonded_parent_uuid=str(item["bonded_parent_uuid"]) if item.get("bonded_parent_uuid") else None,
                )
            )
            existing_snap_keys.add(s_key)

    sep_links = [
        ("RINCON_542A1B63FE6E01400", "RINCON_5CAAFD595EEA01400", 6, 39, 44, StpPortState.FORWARDING.value),
        ("RINCON_B8E937E6098401400", "RINCON_5CAAFD595EEA01400", 6, 40, 41, StpPortState.FORWARDING.value),
        ("RINCON_347E5C3826E201400", "RINCON_5CAAFD595EEA01400", 6, 35, 38, StpPortState.FORWARDING.value),
        ("RINCON_347E5C31CE2801400", "RINCON_949F3EC0EEA101400", 6, 48, 57, StpPortState.BLOCKING.value),
        ("RINCON_B8E937E5152A01400", "RINCON_949F3EC0EEA101400", 6, 52, 58, StpPortState.BLOCKING.value),
        ("RINCON_5CAAFD490CCA01400", "RINCON_949F3EC0EEA101400", 48, 57, 66, StpPortState.FORWARDING.value),
        ("RINCON_949F3E00292E01400", "RINCON_949F3EC0EEA101400", 48, 60, 66, StpPortState.FORWARDING.value),
    ]
    for src_u, tgt_u, ch, f_db, t_db, stp_st in sep_links:
        l_key = f"{sep_batch_id}:{src_u}->{tgt_u}"
        if l_key not in existing_link_keys:
            session.add(
                SonosMeshLink(
                    link_key=l_key,
                    batch_id=sep_batch_id,
                    captured_at=sep_ts,
                    source_rincon_uuid=src_u,
                    target_rincon_uuid=tgt_u,
                    channel=ch,
                    from_db=f_db,
                    to_db=t_db,
                    stp_state=stp_st,
                )
            )
            existing_link_keys.add(l_key)

    # 5b. Post-Remediation Baseline 5 Oct 2026 (`docs/sonos/devices.md` — Wohnzimmer_Bookshelf Root 9000.542a1b63fe6e)
    oct_batch_id = "baseline-2026-10-05"
    oct_ts = datetime(2026, 10, 5, 19, 6, 0, tzinfo=timezone.utc)
    for idx, item in enumerate(MASTER_SONOS_INVENTORY, start=10):
        r_uuid = str(item["rincon_uuid"])
        s_key = f"{oct_batch_id}:{r_uuid}"
        if s_key not in existing_snap_keys:
            dev = devs_by_uuid.get(r_uuid)
            room = rooms_by_slug.get(str(item["room_slug"]))
            coord_uuid = str(item.get("bonded_parent_uuid") or r_uuid)
            session.add(
                SonosTelemetrySnapshot(
                    snapshot_key=s_key,
                    batch_id=oct_batch_id,
                    captured_at=oct_ts,
                    consumer_id="baseline-2026-10-05",
                    device_id=dev.id if dev else None,
                    room_id=room.id if room else None,
                    rincon_uuid=r_uuid,
                    zone_name=str(item["zone_name"]),
                    ip_address=str(item["ip_address"]) if item.get("ip_address") else None,
                    base_mac=str(item["base_mac"]),
                    sonosnet_bssid=str(item["sonosnet_bssid"]),
                    is_reachable=True,
                    connection_mode=item["connection_mode"].value,
                    ieee_channel=int(item["ieee_channel"]) if item.get("ieee_channel") else 6,
                    ofdm_ani_level=item["ofdm_ani_level"],
                    noise_floor_dbm=item["noise_floor_dbm"],
                    phy_error_total=int(item["phy_error_total"]),
                    phy_error_rate=float(item["baseline_err_rate"]),
                    designated_root=str(item["designated_root"]),
                    stp_root_port=str(item["stp_root_port"]),
                    stp_path_cost=int(item["stp_path_cost"]),
                    group_id=f"{coord_uuid}:{idx}",
                    coordinator_uuid=coord_uuid,
                    has_vanished_devices=False,
                    is_ghost_group=False,
                    master_volume=int(item["master_volume"]),
                    ping_rtt_ms=float(item["ping_rtt_ms"]),
                    bonded_parent_uuid=str(item["bonded_parent_uuid"]) if item.get("bonded_parent_uuid") else None,
                )
            )
            existing_snap_keys.add(s_key)

    oct_links = [
        ("RINCON_B8E937E6098401400", "RINCON_542A1B63FE6E01400", 6, 49, 54, StpPortState.FORWARDING.value),
        ("RINCON_B8E937E5152A01400", "RINCON_542A1B63FE6E01400", 6, 50, 56, StpPortState.FORWARDING.value),
        ("RINCON_949F3EC0EEA101400", "RINCON_542A1B63FE6E01400", 6, 47, 57, StpPortState.FORWARDING.value),
        ("RINCON_347E5C3826E201400", "RINCON_542A1B63FE6E01400", 6, 32, 34, StpPortState.FORWARDING.value),
        ("RINCON_347E5C35B0F401400", "RINCON_542A1B63FE6E01400", 6, 41, 43, StpPortState.FORWARDING.value),
        ("RINCON_5CAAFD595EEA01400", "RINCON_542A1B63FE6E01400", 6, 39, 44, StpPortState.FORWARDING.value),
        ("RINCON_347E5C35B2C001400", "RINCON_542A1B63FE6E01400", 6, 36, 26, StpPortState.FORWARDING.value),
        ("RINCON_542A1B64268001400", "RINCON_542A1B63FE6E01400", 6, 23, 33, StpPortState.FORWARDING.value),
        ("RINCON_347E5C3828B001400", "RINCON_542A1B63FE6E01400", 6, 36, 36, StpPortState.FORWARDING.value),
        ("RINCON_347E5C31CE2801400", "RINCON_347E5C3828B001400", 6, 57, 58, StpPortState.FORWARDING.value),
        ("RINCON_347E5C31CE2801400", "RINCON_949F3EC0EEA101400", 6, 54, 48, StpPortState.BLOCKING.value),
        ("RINCON_5CAAFD490CCA01400", "RINCON_949F3EC0EEA101400", 48, 57, 66, StpPortState.FORWARDING.value),
        ("RINCON_949F3E00292E01400", "RINCON_949F3EC0EEA101400", 48, 60, 66, StpPortState.FORWARDING.value),
    ]
    for src_u, tgt_u, ch, f_db, t_db, stp_st in oct_links:
        l_key = f"{oct_batch_id}:{src_u}->{tgt_u}"
        if l_key not in existing_link_keys:
            session.add(
                SonosMeshLink(
                    link_key=l_key,
                    batch_id=oct_batch_id,
                    captured_at=oct_ts,
                    source_rincon_uuid=src_u,
                    target_rincon_uuid=tgt_u,
                    channel=ch,
                    from_db=f_db,
                    to_db=t_db,
                    stp_state=stp_st,
                )
            )
            existing_link_keys.add(l_key)

    # 6. Seed AccessPointRadio records (Galerie EAP650 & Kitchen EAP650)
    existing_radios_res = await session.execute(select(AccessPointRadio.radio_key))
    existing_radio_keys = {k for k in existing_radios_res.scalars().all() if k is not None}

    ap_dev_map = {
        "galerie-ap": devs_by_slug.get("ap-galerie-eap650"),
        "kitchen-ap": devs_by_slug.get("ap-kitchen-eap650"),
    }
    for r_meta in MASTER_AP_RADIOS:
        r_key = str(r_meta["radio_key"])
        if r_key not in existing_radio_keys:
            ap_dev = ap_dev_map.get(str(r_meta["ap_device_slug"]))
            session.add(
                AccessPointRadio(
                    radio_key=r_key,
                    ap_device_id=ap_dev.id if ap_dev else None,
                    ap_device_slug=str(r_meta["ap_device_slug"]),
                    ap_name=str(r_meta["ap_name"]),
                    room_slug=str(r_meta["room_slug"]),
                    band=str(r_meta["band"]),
                    base_mac=str(r_meta["base_mac"]),
                    bssid_suffix=str(r_meta["bssid_suffix"]),
                    derived_bssids_csv=",".join(r_meta["derived_bssids"]),
                    channel=int(r_meta["channel"]),
                    center_channel=int(r_meta["center_channel"]),
                    width_mhz=int(r_meta["width_mhz"]),
                    tx_power_dbm=int(r_meta["tx_power_dbm"]),
                    airtime_utilization_pct=float(r_meta["airtime_utilization_pct"]),
                    is_non_dfs=bool(r_meta["is_non_dfs"]),
                    status=str(r_meta["status"]),
                )
            )
            existing_radio_keys.add(r_key)

    # 7. Seed 19-21 Sep 2026 Historical Baseline & 4-8 Oct 2026 Post-Remediation Room Surveys across all 11 rooms
    existing_surveys_res = await session.execute(select(WiFiRoomSurvey.survey_slug))
    existing_survey_slugs = {
        s for s in existing_surveys_res.scalars().all() if s is not None
    }

    for s_def in SEED_ROOM_SURVEYS:
        s_slug = str(s_def["survey_slug"])
        if s_slug in existing_survey_slugs:
            continue
        room = rooms_by_slug.get(str(s_def["room_slug"]))
        if not room:
            continue

        inputs = [
            BssidReadingInput(
                bssid=b[0],
                ssid=b[1],
                band=b[2],
                channel=b[3],
                center_channel=b[4],
                width_mhz=b[5],
                rssi_dbm=b[6],
            )
            for b in s_def["readings"]
        ]
        built = build_wifi_room_survey(
            room_slug=room.slug,
            room_name=room.name,
            survey_slug=s_slug,
            label=str(s_def["label"]),
            trigger_mode=str(s_def.get("trigger_mode", "HISTORICAL_SEED")),
            captured_at=s_def["captured_at"],
            connected_bssid=s_def.get("connected_bssid"),
            connected_ssid=s_def.get("connected_ssid"),
            link_speed_mbps=s_def.get("link_speed_mbps"),
            notes=s_def.get("notes"),
            readings=inputs,
            room_id=room.id,
        )
        survey_row = WiFiRoomSurvey(
            survey_slug=built.survey_slug,
            room_id=room.id,
            room_slug=room.slug,
            room_name=room.name,
            label=built.label,
            trigger_mode=built.trigger_mode,
            captured_at=built.captured_at,
            connected_bssid=built.connected_bssid,
            connected_ssid=built.connected_ssid,
            link_speed_mbps=built.link_speed_mbps,
            frequency_mhz=built.frequency_mhz,
            best_5ghz_dbm=built.best_5ghz_dbm,
            best_24ghz_dbm=built.best_24ghz_dbm,
            best_ap_slug=built.best_ap_slug,
            best_ap_name=built.best_ap_name,
            rogue_count=built.rogue_count,
            neighbor_count=built.neighbor_count,
            grade_5ghz=built.grade_5ghz,
            grade_24ghz=built.grade_24ghz,
            wifi_health_grade=built.wifi_health_grade,
            notes=built.notes,
        )
        session.add(survey_row)
        await session.flush()

        for idx, r_item in enumerate(built.readings, start=1):
            session.add(
                BssidReading(
                    reading_key=f"{s_slug}:{idx}:{r_item.bssid}",
                    survey_id=survey_row.id,
                    room_id=room.id,
                    bssid=r_item.bssid,
                    ssid=r_item.ssid,
                    band=r_item.band,
                    channel=r_item.channel,
                    center_channel=r_item.center_channel,
                    width_mhz=r_item.width_mhz,
                    rssi_dbm=r_item.rssi_dbm,
                    classification=r_item.classification,
                    ap_device_slug=r_item.ap_device_slug,
                    ap_name=r_item.ap_name,
                    is_connected=r_item.is_connected,
                )
            )
        existing_survey_slugs.add(s_slug)

    await session.commit()


# Format of each reading tuple: (bssid, ssid, band, channel, center_channel, width_mhz, rssi_dbm)
SEED_ROOM_SURVEYS: list[dict[str, Any]] = [
    # 1. Elternbad
    {
        "survey_slug": "elternbad-19-sep-2026-baseline",
        "room_slug": "elternbad",
        "label": "19 Sep 2026 Historical Baseline (Epson -42 dBm Rogue)",
        "captured_at": datetime(2026, 9, 19, 21, 14, 0, tzinfo=timezone.utc),
        "connected_bssid": "76:4C:BC:76:7C:41",
        "connected_ssid": "WuTangLan-Family",
        "link_speed_mbps": 1201,
        "notes": "Netlog_Elternbad.jpg — Epson ET-4850 Wi-Fi Direct blasting at -42 dBm on Ch 11.",
        "readings": [
            ("6A:55:D4:7D:0B:9B", "DIRECT-f1-EPSON-ET-4850", "2.4GHz", 11, 11, 20, -42),
            ("72:4C:BC:76:7C:41", "Admin", "5GHz", 44, 42, 80, -50),
            ("76:4C:BC:76:7C:41", "WuTangLan-Family", "5GHz", 44, 42, 80, -51),
            ("7A:4C:BC:76:7C:40", "WuTangLan-Guest", "2.4GHz", 11, 11, 20, -56),
            ("DC:A6:33:43:EC:0C", "Vodafone-DD14", "2.4GHz", 11, 11, 20, -60),
            ("84:16:F9:93:E9:2D", "TP-Link_5G_93E92D", "5GHz", 36, 42, 80, -69),
            ("86:16:F9:BF:E9:2D", "WuTangLan-Family", "2.4GHz", 1, 1, 20, -72),
            ("76:4C:BC:76:94:C0", "WuTangLan-Family", "2.4GHz", 1, 1, 20, -76),
            ("76:4C:BC:76:94:C1", "WuTangLan-Family", "5GHz", 48, 42, 80, -84),
        ],
    },
    {
        "survey_slug": "elternbad-04-oct-2026-sanitized",
        "room_slug": "elternbad",
        "label": "4 Oct 2026 Post-Remediation (Epson & EAP330 Eliminated)",
        "captured_at": datetime(2026, 10, 4, 22, 19, 0, tzinfo=timezone.utc),
        "connected_bssid": "76:4C:BC:76:7C:41",
        "connected_ssid": "WuTangLan-Family",
        "link_speed_mbps": 1201,
        "notes": "4 Oct 2026 22:19 NetX scan — 1201 Mbps Wi-Fi 6 on Galerie Ch 44 (-55 dBm); Epson -42 dBm 100% eliminated.",
        "readings": [
            ("72:4C:BC:76:7C:41", "Admin", "5GHz", 44, 42, 80, -55),
            ("76:4C:BC:76:7C:41", "WuTangLan-Family", "5GHz", 44, 42, 80, -55),
            ("76:4C:BC:76:7C:40", "WuTangLan-Family", "2.4GHz", 1, 1, 20, -60),
            ("72:4C:BC:76:7C:40", "Admin", "2.4GHz", 1, 1, 20, -61),
            ("38:10:D5:8B:10:56", "WLAN-A7C604", "2.4GHz", 11, 11, 20, -84),
            ("76:4C:BC:76:94:C0", "WuTangLan-Family", "2.4GHz", 11, 11, 20, -85),
            ("DC:A6:33:43:EC:0C", "Vodafone-DD14", "2.4GHz", 11, 11, 20, -87),
            ("DE:A6:33:43:EC:0E", "Vodafone Hotspot", "2.4GHz", 11, 11, 20, -88),
            ("7E:4C:BC:76:94:C1", "WuTangLan-IOT", "5GHz", 40, 38, 40, -91),
            ("76:4C:BC:76:94:C1", "WuTangLan-Family", "5GHz", 40, 38, 40, -92),
        ],
    },
    # 2. Elternschlafzimmer
    {
        "survey_slug": "elternschlafzimmer-19-sep-2026-baseline",
        "room_slug": "elternschlafzimmer",
        "label": "19 Sep 2026 Historical Baseline",
        "captured_at": datetime(2026, 9, 19, 19, 42, 0, tzinfo=timezone.utc),
        "connected_bssid": "76:4C:BC:76:7C:41",
        "connected_ssid": "WuTangLan-Family",
        "link_speed_mbps": 1201,
        "notes": "Netlog_elternschlafzimmer.jpg — 2.4GHz drifted from -57 to -79 dBm; EAP330 on Ch 6.",
        "readings": [
            ("72:4C:BC:76:7C:41", "Admin", "5GHz", 44, 42, 80, -54),
            ("76:4C:BC:76:7C:41", "WuTangLan-Family", "5GHz", 44, 42, 80, -54),
            ("7A:4C:BC:76:7C:40", "WuTangLan-Guest", "2.4GHz", 11, 11, 20, -57),
            ("84:16:F9:93:E9:2C", "[Hidden SSID]", "2.4GHz", 6, 6, 20, -78),
            ("86:16:F9:BF:E9:2F", "WuTangLan-IOT", "2.4GHz", 6, 6, 20, -80),
            ("38:10:D5:BA:88:B3", "FRITZ!Box 7490", "2.4GHz", 6, 6, 20, -80),
            ("76:4C:BC:76:94:C1", "WuTangLan-Family", "5GHz", 48, 42, 80, -87),
        ],
    },
    {
        "survey_slug": "elternschlafzimmer-04-oct-2026-sanitized",
        "room_slug": "elternschlafzimmer",
        "label": "4 Oct 2026 Post-Remediation",
        "captured_at": datetime(2026, 10, 4, 19, 6, 0, tzinfo=timezone.utc),
        "connected_bssid": "76:4C:BC:76:7C:41",
        "connected_ssid": "WuTangLan-Family",
        "link_speed_mbps": 1201,
        "notes": "Galerie Ch 44 at -52 dBm & Ch 1 at -55 dBm; rogue EAP330 eliminated.",
        "readings": [
            ("34:7E:5C:38:28:B1", "SonosNet", "2.4GHz", 6, 6, 20, -48),
            ("76:4C:BC:76:7C:41", "WuTangLan-Family", "5GHz", 44, 42, 80, -52),
            ("76:4C:BC:76:7C:40", "WuTangLan-Family", "2.4GHz", 1, 1, 20, -55),
        ],
    },
    # 3. Noemi
    {
        "survey_slug": "noemi-19-sep-2026-baseline",
        "room_slug": "noemi",
        "label": "19 Sep 2026 Historical Baseline",
        "captured_at": datetime(2026, 9, 19, 21, 8, 0, tzinfo=timezone.utc),
        "connected_bssid": "76:4C:BC:76:7C:41",
        "connected_ssid": "WuTangLan-Family",
        "link_speed_mbps": 1201,
        "notes": "Netlog_Noemi.jpg — AP-1 on Ch 11 (-56 dBm) & Ch 44 (-59 dBm).",
        "readings": [
            ("76:4C:BC:76:7C:40", "WuTangLan-Family", "2.4GHz", 11, 11, 20, -56),
            ("72:4C:BC:76:7C:41", "Admin", "5GHz", 44, 42, 80, -59),
            ("76:4C:BC:76:7C:41", "WuTangLan-Family", "5GHz", 44, 42, 80, -61),
            ("84:16:F9:93:E9:2D", "TP-Link_5G_93E92D", "5GHz", 44, 42, 80, -78),
        ],
    },
    {
        "survey_slug": "noemi-04-oct-2026-sanitized",
        "room_slug": "noemi",
        "label": "4 Oct 2026 Post-Remediation (Kitchen AP Ch 40/11)",
        "captured_at": datetime(2026, 10, 4, 20, 41, 0, tzinfo=timezone.utc),
        "connected_bssid": "76:4C:BC:76:94:C1",
        "connected_ssid": "WuTangLan-Family",
        "link_speed_mbps": 573,
        "notes": "4 Oct 2026 20:41 NetX scan — Kitchen AP Ch 40 (-72 dBm) & Ch 11 (-70 dBm); neighbor WLAN-A7C604 at -71 dBm on Ch 11.",
        "readings": [
            ("76:4C:BC:76:94:C0", "WuTangLan-Family", "2.4GHz", 11, 11, 20, -70),
            ("1C:23:A2:7A:E3:7A", "WLAN-A7C604", "2.4GHz", 11, 11, 20, -71),
            ("76:4C:BC:76:94:C1", "WuTangLan-Family", "5GHz", 40, 38, 40, -72),
            ("76:4C:BC:76:7C:40", "WuTangLan-Family", "2.4GHz", 1, 1, 20, -80),
            ("1C:23:A2:7A:E3:7B", "WLAN-A7C604", "5GHz", 52, 50, 80, -81),
            ("76:4C:BC:76:7C:41", "WuTangLan-Family", "5GHz", 44, 42, 80, -84),
        ],
    },
    # 4. Noah
    {
        "survey_slug": "noah-19-sep-2026-baseline",
        "room_slug": "noah",
        "label": "19 Sep 2026 Historical Baseline (2.4 GHz Hole)",
        "captured_at": datetime(2026, 9, 19, 21, 4, 0, tzinfo=timezone.utc),
        "connected_bssid": "76:4C:BC:76:7C:41",
        "connected_ssid": "WuTangLan-Family",
        "link_speed_mbps": 1201,
        "notes": "Netlog_Noah.jpg — No 2.4 GHz AP present in live scan; 5 GHz at -61 dBm.",
        "readings": [
            ("72:4C:BC:76:7C:41", "Admin", "5GHz", 44, 42, 80, -61),
            ("76:4C:BC:76:7C:41", "WuTangLan-Family", "5GHz", 44, 42, 80, -61),
            ("76:4C:BC:76:94:C1", "WuTangLan-Family", "5GHz", 48, 42, 80, -67),
            ("86:16:F9:BF:E9:2E", "WuTangLan-Guest", "2.4GHz", 6, 6, 20, -85),
        ],
    },
    {
        "survey_slug": "noah-04-oct-2026-sanitized",
        "room_slug": "noah",
        "label": "4 Oct 2026 Post-Remediation",
        "captured_at": datetime(2026, 10, 4, 19, 6, 0, tzinfo=timezone.utc),
        "connected_bssid": "76:4C:BC:76:7C:41",
        "connected_ssid": "WuTangLan-Family",
        "link_speed_mbps": 1201,
        "notes": "Galerie AP relocated -> 5 GHz Ch 44 at -57 dBm & 2.4 GHz Ch 1 at -60 dBm restored.",
        "readings": [
            ("34:7E:5C:35:B2:C1", "SonosNet", "2.4GHz", 6, 6, 20, -50),
            ("76:4C:BC:76:7C:41", "WuTangLan-Family", "5GHz", 44, 42, 80, -57),
            ("76:4C:BC:76:7C:40", "WuTangLan-Family", "2.4GHz", 1, 1, 20, -60),
        ],
    },
    # 5. Nicolas
    {
        "survey_slug": "nicolas-19-sep-2026-baseline",
        "room_slug": "nicolas",
        "label": "20 Sep 2026 Historical Baseline (Fritzbox 2401 Mbps & EAP330 -55 dBm)",
        "captured_at": datetime(2026, 9, 20, 20, 54, 0, tzinfo=timezone.utc),
        "connected_bssid": "0C:72:74:00:63:9B",
        "connected_ssid": "WuTangLan",
        "link_speed_mbps": 2401,
        "notes": "Netlog_Nicolas.jpg — Phone hijacked by rogue Fritzbox 6660 (WuTangLan) and EAP330 (TP-Link_5G_93E92D -55 dBm).",
        "readings": [
            ("84:16:F9:93:E9:2D", "TP-Link_5G_93E92D", "5GHz", 44, 42, 80, -55),
            ("0C:72:74:00:63:9B", "WuTangLan", "5GHz", 36, 50, 160, -58),
            ("1C:23:A2:7A:E3:7A", "WLAN-A7C604", "2.4GHz", 6, 6, 20, -61),
            ("86:16:F9:BF:E9:2D", "WuTangLan-Family", "2.4GHz", 6, 6, 20, -64),
            ("86:16:F9:BF:E9:2F", "WuTangLan-IOT", "2.4GHz", 6, 6, 20, -66),
            ("76:4C:BC:76:7C:40", "WuTangLan-Family", "2.4GHz", 11, 11, 20, -67),
            ("76:4C:BC:76:7C:41", "WuTangLan-Family", "5GHz", 44, 42, 80, -70),
            ("76:4C:BC:76:94:C1", "WuTangLan-Family", "5GHz", 48, 42, 80, -77),
        ],
    },
    {
        "survey_slug": "nicolas-08-oct-2026-sanitized",
        "room_slug": "nicolas",
        "label": "8 Oct 2026 Post-Remediation Verification (Zero Rogue / 1201 Mbps)",
        "captured_at": datetime(2026, 10, 8, 22, 43, 0, tzinfo=timezone.utc),
        "connected_bssid": "76:4C:BC:76:7C:41",
        "connected_ssid": "WuTangLan-Family",
        "link_speed_mbps": 1201,
        "notes": "8 Oct 2026 22:43 NetX scan — Rogue EAP330 & Fritzbox 100% eliminated; Galerie Ch 44 @ -72 dBm (1201 Mbps).",
        "readings": [
            ("7A:4C:BC:76:7C:41", "WuTangLan-Guest", "5GHz", 44, 42, 80, -72),
            ("72:4C:BC:76:7C:41", "Admin", "5GHz", 44, 42, 80, -73),
            ("7E:4C:BC:76:7C:41", "WuTangLan-IOT", "5GHz", 44, 42, 80, -73),
            ("76:4C:BC:76:7C:41", "WuTangLan-Family", "5GHz", 44, 42, 80, -75),
            ("72:4C:BC:76:94:C1", "Admin", "5GHz", 40, 38, 40, -82),
            ("76:4C:BC:76:94:C1", "WuTangLan-Family", "5GHz", 40, 38, 40, -82),
            ("7A:4C:BC:76:94:C1", "WuTangLan-Guest", "5GHz", 40, 38, 40, -83),
            ("7E:4C:BC:76:94:C1", "WuTangLan-IOT", "5GHz", 40, 38, 40, -83),
        ],
    },
    # 6. Galerie
    {
        "survey_slug": "galerie-19-sep-2026-baseline",
        "room_slug": "galerie",
        "label": "19 Sep 2026 Historical Baseline",
        "captured_at": datetime(2026, 9, 19, 21, 11, 0, tzinfo=timezone.utc),
        "connected_bssid": "76:4C:BC:76:7C:41",
        "connected_ssid": "WuTangLan-Family",
        "link_speed_mbps": 1201,
        "notes": "Netlog_Galerie.jpg — AP-1 at -53 dBm on both bands; Epson at -68 dBm.",
        "readings": [
            ("0C:EF:15:5E:97:49", "Tapo_Bulb_9749", "2.4GHz", 6, 6, 20, -52),
            ("76:4C:BC:76:7C:41", "WuTangLan-Family", "5GHz", 44, 42, 80, -53),
            ("76:4C:BC:76:7C:40", "WuTangLan-Family", "2.4GHz", 11, 11, 20, -53),
            ("72:4C:BC:76:94:C0", "Admin", "2.4GHz", 1, 1, 20, -55),
            ("DC:A6:33:43:EC:0C", "Vodafone-DD14", "2.4GHz", 11, 11, 20, -64),
            ("6A:55:D4:7D:0B:9B", "DIRECT-f1-EPSON-ET-4850", "2.4GHz", 11, 11, 20, -68),
        ],
    },
    {
        "survey_slug": "galerie-04-oct-2026-sanitized",
        "room_slug": "galerie",
        "label": "4 Oct 2026 Post-Relocation & Sanitization",
        "captured_at": datetime(2026, 10, 4, 17, 0, 0, tzinfo=timezone.utc),
        "connected_bssid": "76:4C:BC:76:7C:41",
        "connected_ssid": "WuTangLan-Family",
        "link_speed_mbps": 1201,
        "notes": "Galerie EAP650 relocated into open: -45 dBm on 5 GHz Ch 44 (80 MHz) & -48 dBm on 2.4 GHz Ch 1.",
        "readings": [
            ("76:4C:BC:76:7C:41", "WuTangLan-Family", "5GHz", 44, 42, 80, -45),
            ("76:4C:BC:76:7C:40", "WuTangLan-Family", "2.4GHz", 1, 1, 20, -48),
            ("76:4C:BC:76:94:C1", "WuTangLan-Family", "5GHz", 40, 38, 40, -75),
        ],
    },
    # 7. Büroecke
    {
        "survey_slug": "bueroecke-19-sep-2026-baseline",
        "room_slug": "bueroecke",
        "label": "20 Sep 2026 Historical Baseline (EAP330 40MHz Ch 11 Collision)",
        "captured_at": datetime(2026, 9, 20, 22, 45, 0, tzinfo=timezone.utc),
        "connected_bssid": "76:4C:BC:76:7C:41",
        "connected_ssid": "WuTangLan-Family",
        "link_speed_mbps": 1201,
        "notes": "Büroecke 22:45 scan — EAP330 wandered onto Ch 11 (9) @ 40 MHz alongside Epson (-64 dBm).",
        "readings": [
            ("7E:4C:BC:76:7C:40", "WuTangLan-IOT", "2.4GHz", 11, 11, 20, -52),
            ("76:4C:BC:76:7C:41", "WuTangLan-Family", "5GHz", 44, 42, 80, -54),
            ("DE:A6:33:43:EC:10", "Vodafone Homespot", "2.4GHz", 1, 1, 20, -57),
            ("84:16:F9:93:E9:2D", "TP-Link_5G_93E92D", "5GHz", 44, 42, 80, -63),
            ("6A:55:D4:7D:0B:9B", "DIRECT-f1-EPSON-ET-4850", "2.4GHz", 11, 11, 20, -64),
            ("86:16:F9:BF:E9:2D", "WuTangLan-Family", "2.4GHz", 11, 9, 40, -72),
            ("76:4C:BC:76:94:C0", "WuTangLan-Family", "2.4GHz", 1, 1, 20, -83),
            ("76:4C:BC:76:94:C1", "WuTangLan-Family", "5GHz", 48, 42, 80, -92),
        ],
    },
    {
        "survey_slug": "bueroecke-04-oct-2026-sanitized",
        "room_slug": "bueroecke",
        "label": "4 Oct 2026 Post-Remediation",
        "captured_at": datetime(2026, 10, 4, 19, 1, 0, tzinfo=timezone.utc),
        "connected_bssid": "76:4C:BC:76:7C:41",
        "connected_ssid": "WuTangLan-Family",
        "link_speed_mbps": 1201,
        "notes": "Galerie Ch 44 (-52 dBm) & Ch 1 (-56 dBm); Epson & EAP330 eliminated.",
        "readings": [
            ("34:7E:5C:35:B0:F5", "SonosNet", "2.4GHz", 6, 6, 20, -44),
            ("76:4C:BC:76:7C:41", "WuTangLan-Family", "5GHz", 44, 42, 80, -52),
            ("76:4C:BC:76:7C:40", "WuTangLan-Family", "2.4GHz", 1, 1, 20, -56),
            ("76:4C:BC:76:94:C0", "WuTangLan-Family", "2.4GHz", 11, 11, 20, -70),
            ("76:4C:BC:76:94:C1", "WuTangLan-Family", "5GHz", 40, 38, 40, -75),
        ],
    },
    # 8. Wohnzimmer
    {
        "survey_slug": "wohnzimmer-19-sep-2026-baseline",
        "room_slug": "wohnzimmer",
        "label": "19 Sep 2026 Historical Baseline (EAP330 Co-Channel on Ch 44)",
        "captured_at": datetime(2026, 9, 19, 21, 0, 0, tzinfo=timezone.utc),
        "connected_bssid": "76:4C:BC:76:7C:41",
        "connected_ssid": "WuTangLan-Family",
        "link_speed_mbps": 1201,
        "notes": "Netlog_Wohnzimmer.jpg — TP-Link_5G_93E92D (-56 dBm) colliding on Ch 44 with AP-1 (-55 dBm).",
        "readings": [
            ("76:4C:BC:76:7C:40", "WuTangLan-Family", "2.4GHz", 11, 11, 20, -52),
            ("76:4C:BC:76:7C:41", "WuTangLan-Family", "5GHz", 44, 42, 80, -55),
            ("84:16:F9:93:E9:2D", "TP-Link_5G_93E92D", "5GHz", 44, 42, 80, -56),
            ("6A:55:D4:7D:0B:9B", "DIRECT-f1-EPSON-ET-4850", "2.4GHz", 11, 11, 20, -59),
            ("DE:A6:33:43:EC:10", "Vodafone Homespot", "2.4GHz", 11, 11, 20, -67),
            ("72:4C:BC:76:94:C1", "Admin", "5GHz", 48, 42, 80, -75),
            ("0C:72:74:00:63:9B", "WuTangLan", "5GHz", 36, 50, 160, -86),
        ],
    },
    {
        "survey_slug": "wohnzimmer-04-oct-2026-sanitized",
        "room_slug": "wohnzimmer",
        "label": "4 Oct 2026 Post-Remediation",
        "captured_at": datetime(2026, 10, 4, 19, 6, 0, tzinfo=timezone.utc),
        "connected_bssid": "76:4C:BC:76:7C:41",
        "connected_ssid": "WuTangLan-Family",
        "link_speed_mbps": 1201,
        "notes": "EAP330 powered off; Galerie Ch 44 (-54 dBm) & Ch 1 (-52 dBm) clean.",
        "readings": [
            ("54:2A:1B:63:FE:6F", "SonosNet", "2.4GHz", 6, 6, 20, -40),
            ("B8:E9:37:E6:09:85", "SonosNet", "2.4GHz", 6, 6, 20, -45),
            ("76:4C:BC:76:7C:40", "WuTangLan-Family", "2.4GHz", 1, 1, 20, -52),
            ("76:4C:BC:76:7C:41", "WuTangLan-Family", "5GHz", 44, 42, 80, -54),
        ],
    },
    # 9. Fernsehecke
    {
        "survey_slug": "fernsehecke-19-sep-2026-baseline",
        "room_slug": "fernsehecke",
        "label": "20 Sep 2026 Historical Baseline (Fritzbox -40 dBm & Epson -48 dBm)",
        "captured_at": datetime(2026, 9, 20, 22, 5, 0, tzinfo=timezone.utc),
        "connected_bssid": "76:4C:BC:76:7C:41",
        "connected_ssid": "WuTangLan-Family",
        "link_speed_mbps": 1201,
        "notes": "Fernsehecke 22:05 scan — Fritzbox WuTangLan at -40 dBm & Epson at -48 dBm.",
        "readings": [
            ("0C:72:74:00:63:9B", "WuTangLan", "5GHz", 116, 114, 160, -40),
            ("6A:55:D4:7D:0B:9B", "DIRECT-f1-EPSON-ET-4850", "2.4GHz", 11, 11, 20, -48),
            ("76:4C:BC:76:7C:41", "WuTangLan-Family", "5GHz", 44, 42, 80, -53),
            ("76:4C:BC:76:7C:40", "WuTangLan-Family", "2.4GHz", 11, 11, 20, -55),
            ("DE:A6:33:43:EC:10", "Vodafone Homespot", "2.4GHz", 1, 1, 20, -57),
            ("76:4C:BC:76:94:C0", "WuTangLan-Family", "2.4GHz", 1, 1, 20, -64),
            ("86:16:F9:BF:E9:2D", "WuTangLan-Family", "2.4GHz", 6, 6, 20, -68),
            ("84:16:F9:93:E9:2D", "TP-Link_5G_93E92D", "5GHz", 44, 42, 80, -72),
            ("76:4C:BC:76:94:C1", "WuTangLan-Family", "5GHz", 48, 42, 80, -78),
        ],
    },
    {
        "survey_slug": "fernsehecke-04-oct-2026-sanitized",
        "room_slug": "fernsehecke",
        "label": "4 Oct 2026 Post-Remediation",
        "captured_at": datetime(2026, 10, 4, 19, 6, 0, tzinfo=timezone.utc),
        "connected_bssid": "76:4C:BC:76:7C:41",
        "connected_ssid": "WuTangLan-Family",
        "link_speed_mbps": 1201,
        "notes": "Fritzbox & Epson disabled; Galerie Ch 44 (-55 dBm) & Ch 1 (-58 dBm); HT 5 GHz Ch 48 clean (ANI 0).",
        "readings": [
            ("94:9F:3E:C0:EE:A2", "SonosHT-5G", "5GHz", 48, 46, 80, -42),
            ("76:4C:BC:76:7C:41", "WuTangLan-Family", "5GHz", 44, 42, 80, -55),
            ("76:4C:BC:76:7C:40", "WuTangLan-Family", "2.4GHz", 1, 1, 20, -58),
            ("76:4C:BC:76:94:C0", "WuTangLan-Family", "2.4GHz", 11, 11, 20, -68),
        ],
    },
    # 10. Küche
    {
        "survey_slug": "kueche-19-sep-2026-baseline",
        "room_slug": "kueche",
        "label": "20 Sep 2026 Historical Baseline (Epson -47 dBm in Kitchen)",
        "captured_at": datetime(2026, 9, 20, 22, 17, 0, tzinfo=timezone.utc),
        "connected_bssid": "76:4C:BC:76:7C:41",
        "connected_ssid": "WuTangLan-Family",
        "link_speed_mbps": 1201,
        "notes": "küche_2 22:17 scan — Epson Wi-Fi Direct at -47 dBm on Ch 11; Kitchen AP offline in scan.",
        "readings": [
            ("6A:55:D4:7D:0B:9B", "DIRECT-f1-EPSON-ET-4850", "2.4GHz", 11, 11, 20, -47),
            ("76:4C:BC:76:7C:41", "WuTangLan-Family", "5GHz", 44, 42, 80, -55),
            ("DE:A6:33:43:EC:0E", "Vodafone Hotspot", "2.4GHz", 1, 1, 20, -55),
            ("76:4C:BC:76:7C:40", "WuTangLan-Family", "2.4GHz", 11, 11, 20, -60),
            ("84:16:F9:93:E9:2D", "TP-Link_5G_93E92D", "5GHz", 44, 42, 80, -67),
            ("86:16:F9:BF:E9:2D", "WuTangLan-Family", "2.4GHz", 6, 6, 20, -84),
        ],
    },
    {
        "survey_slug": "kueche-04-oct-2026-sanitized",
        "room_slug": "kueche",
        "label": "4 Oct 2026 Post-Remediation (Epson Disabled -> ANI 0)",
        "captured_at": datetime(2026, 10, 4, 19, 6, 0, tzinfo=timezone.utc),
        "connected_bssid": "76:4C:BC:76:7C:41",
        "connected_ssid": "WuTangLan-Family",
        "link_speed_mbps": 1201,
        "notes": "Epson ET-4850 Wi-Fi Direct disabled -> Küche SYMFONISK OFDM ANI dropped to 0.",
        "readings": [
            ("34:7E:5C:38:26:E3", "SonosNet", "2.4GHz", 6, 6, 20, -45),
            ("76:4C:BC:76:7C:41", "WuTangLan-Family", "5GHz", 44, 42, 80, -55),
            ("76:4C:BC:76:94:C0", "WuTangLan-Family", "2.4GHz", 11, 11, 20, -55),
            ("76:4C:BC:76:94:C1", "WuTangLan-Family", "5GHz", 40, 38, 40, -58),
        ],
    },
    # 11. Keller
    {
        "survey_slug": "keller-19-sep-2026-baseline",
        "room_slug": "keller",
        "label": "20 Sep 2026 Historical Baseline (Fritzbox -39 dBm @ 40 MHz)",
        "captured_at": datetime(2026, 9, 20, 22, 1, 0, tzinfo=timezone.utc),
        "connected_bssid": "76:4C:BC:76:94:C1",
        "connected_ssid": "WuTangLan-Family",
        "link_speed_mbps": 1201,
        "notes": "Keller 22:01 scan — Fritzbox 6660 running 40 MHz wide 2.4 GHz on Ch 11 (9) at -39 dBm.",
        "readings": [
            ("0C:72:74:00:63:9A", "WuTangLan", "2.4GHz", 11, 9, 40, -39),
            ("76:4C:BC:76:94:C0", "WuTangLan-Family", "2.4GHz", 1, 1, 20, -63),
            ("1C:23:A2:7A:E3:7A", "WLAN-A7C604", "2.4GHz", 1, 1, 20, -66),
            ("76:4C:BC:76:94:C1", "WuTangLan-Family", "5GHz", 48, 42, 80, -68),
            ("1C:23:A2:7A:E3:7B", "WLAN-A7C604", "5GHz", 52, 50, 80, -75),
            ("84:16:F9:93:E9:2D", "TP-Link_5G_93E92D", "5GHz", 44, 42, 80, -76),
            ("86:16:F9:BF:E9:2F", "WuTangLan-IOT", "2.4GHz", 6, 6, 20, -82),
        ],
    },
    {
        "survey_slug": "keller-04-oct-2026-sanitized",
        "room_slug": "keller",
        "label": "4 Oct 2026 Post-Remediation (Fritzbox Wi-Fi Disabled)",
        "captured_at": datetime(2026, 10, 4, 19, 0, 0, tzinfo=timezone.utc),
        "connected_bssid": "76:4C:BC:76:94:C1",
        "connected_ssid": "WuTangLan-Family",
        "link_speed_mbps": 1201,
        "notes": "Fritzbox 6660 rogue 40 MHz Wi-Fi disabled; Kitchen AP Ch 11 (-63 dBm) & Ch 40 (-68 dBm).",
        "readings": [
            ("76:4C:BC:76:94:C0", "WuTangLan-Family", "2.4GHz", 11, 11, 20, -63),
            ("1C:23:A2:7A:E3:7A", "WLAN-A7C604", "2.4GHz", 1, 1, 20, -66),
            ("76:4C:BC:76:94:C1", "WuTangLan-Family", "5GHz", 40, 38, 40, -68),
        ],
    },
]


