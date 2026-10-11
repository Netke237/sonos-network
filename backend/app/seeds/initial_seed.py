from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import (
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
)
from app.modules.sonos_telemetry import MASTER_SONOS_INVENTORY



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

    await session.commit()

