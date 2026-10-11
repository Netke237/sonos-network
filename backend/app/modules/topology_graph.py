from __future__ import annotations

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
    SwitchPort,
    WiFiRoomSurvey,
)
from app.modules.sonos_telemetry import EXPECTED_STP_ROOT
from app.modules.wifi_omada import grade_wifi_dbm
from app.schemas.topology import (
    DeviceConnectionEdgeSchema,
    HouseholdSonosSnapshot,
    PlayerTelemetryDto,
    TopologyGraphResponse,
    TopologyNodeSchema,
)


def grade_sonos_snr_db(from_db: int | None, to_db: int | None) -> str:
    """
    Grade SonosNet / HT wireless peer link SNR (dB):
      - min(from_db, to_db) >= 45 -> EXCELLENT
      - min(from_db, to_db) >= 30 -> GOOD
      - min(from_db, to_db) in 20..29 -> MARGINAL
      - min(from_db, to_db) < 20 -> CRITICAL
    """
    if from_db is None or to_db is None:
        return HealthGrade.CRITICAL.value
    min_snr = min(from_db, to_db)
    if min_snr >= 45:
        return HealthGrade.EXCELLENT.value
    if min_snr >= 30:
        return HealthGrade.GOOD.value
    if min_snr >= 20:
        return HealthGrade.MARGINAL.value
    return HealthGrade.CRITICAL.value


def _resolve_allowed_layers(layer_filter: str) -> set[str]:
    norm = (layer_filter or "ALL").strip().upper()
    if norm in ("ALL", "UNIFIED", "*"):
        return {"WIRED_LAN", "WIFI_INFRA", "SONOS_MESH"}
    if norm in ("WIFI_VLAN", "WIFI_AND_VLAN"):
        return {"WIFI_INFRA", "WIRED_LAN"}
    if norm in ("SONOS_STP", "SONOS_AND_STP"):
        return {"SONOS_MESH", "WIRED_LAN"}
    if "," in norm:
        parts = {p.strip() for p in norm.split(",") if p.strip()}
        return parts or {"WIRED_LAN", "WIFI_INFRA", "SONOS_MESH"}
    if norm in ("WIRED_LAN", "WIFI_INFRA", "SONOS_MESH"):
        return {norm}
    return {"WIRED_LAN", "WIFI_INFRA", "SONOS_MESH"}


# Deterministic layout offsets for multi-device rooms so nodes never overlap on the 2D canvas
_DEVICE_LAYOUT_COORDS: dict[str, tuple[float, float]] = {
    "router-fritzbox-6660": (80.0, 720.0),
    "router-firewalla-purple": (240.0, 720.0),
    "switch-netgear-gs316ep": (420.0, 720.0),
    "sonos-keller": (620.0, 720.0),
    "ap-galerie-eap650": (400.0, 230.0),
    "ap-kitchen-eap650": (640.0, 410.0),
    "sonos-wohnzimmer-bookshelf": (110.0, 450.0),
    "sonos-wohnzimmer-esstisch": (230.0, 520.0),
    "sonos-wohnzimmer-buchregal": (110.0, 560.0),
    "sonos-fernsehecke-beam": (410.0, 450.0),
    "sonos-fernsehecke-lr": (360.0, 550.0),
    "sonos-fernsehecke-rr": (470.0, 550.0),
    "sonos-kueche": (680.0, 490.0),
    "sonos-bueroecke": (860.0, 470.0),
    "sonos-eltern": (160.0, 260.0),
    "sonos-elternbad": (50.0, 260.0),
    "sonos-noemi": (650.0, 260.0),
    "sonos-noah": (850.0, 260.0),
    "sonos-nicolas": (500.0, 80.0),
}


async def synthesize_unified_topology_graph(
    session: AsyncSession,
    latest_sonos: HouseholdSonosSnapshot | None,
    layer_filter: str = "ALL",
    floor_slug: str | None = None,
    room_slug: str | None = None,
    include_blocking: bool = True,
) -> TopologyGraphResponse:
    """
    Synthesize the normalized House Network Topology Graph across three layers:
      1. WIRED_LAN
      2. WIFI_INFRA
      3. SONOS_MESH
    """
    floors_res = await session.execute(
        select(Floor).where(Floor.is_archived.is_(False))
    )
    floors = list(floors_res.scalars().all())
    floors_by_id = {f.id: f for f in floors}

    rooms_res = await session.execute(
        select(Room).where(Room.is_archived.is_(False))
    )
    rooms = list(rooms_res.scalars().all())
    rooms_by_id = {r.id: r for r in rooms}
    rooms_by_slug = {r.slug: r for r in rooms}

    ports_res = await session.execute(
        select(SwitchPort).where(SwitchPort.is_archived.is_(False))
    )
    ports = list(ports_res.scalars().all())
    ports_by_id = {p.id: p for p in ports}
    ports_by_room_id: dict[str, SwitchPort] = {}
    for p in ports:
        if p.patched_room_id and p.patched_room_id not in ports_by_room_id:
            ports_by_room_id[p.patched_room_id] = p

    devices_res = await session.execute(
        select(NetworkDevice).where(NetworkDevice.is_archived.is_(False))
    )
    devices = list(devices_res.scalars().all())

    # Fetch AP radios for channel summary
    radios_res = await session.execute(select(AccessPointRadio))
    radios = list(radios_res.scalars().all())
    radios_by_ap_slug: dict[str, list[AccessPointRadio]] = {}
    for rad in radios:
        radios_by_ap_slug.setdefault(rad.ap_device_slug, []).append(rad)

    # Fetch latest WiFiRoomSurvey & connected BssidReading per room
    surveys_res = await session.execute(
        select(WiFiRoomSurvey).order_by(WiFiRoomSurvey.captured_at.desc())
    )
    latest_survey_by_room_id: dict[str, WiFiRoomSurvey] = {}
    for s in surveys_res.scalars().all():
        if s.room_id not in latest_survey_by_room_id:
            latest_survey_by_room_id[s.room_id] = s

    latest_survey_ids = [s.id for s in latest_survey_by_room_id.values()]
    readings_by_survey_id: dict[str, list[BssidReading]] = {}
    if latest_survey_ids:
        br_res = await session.execute(
            select(BssidReading).where(BssidReading.survey_id.in_(latest_survey_ids))
        )
        for br in br_res.scalars().all():
            readings_by_survey_id.setdefault(br.survey_id, []).append(br)

    telem_by_uuid: dict[str, PlayerTelemetryDto] = {}
    if latest_sonos:
        telem_by_uuid = {p.rincon_uuid: p for p in latest_sonos.players}

    # Build TopologyNodeSchema for all active NetworkDevices
    nodes_by_slug: dict[str, TopologyNodeSchema] = {}
    nodes_by_uuid: dict[str, TopologyNodeSchema] = {}
    room_slot_counts: dict[str | None, int] = {}

    for dev in devices:
        room = rooms_by_id.get(dev.room_id) if dev.room_id else None
        floor = floors_by_id.get(room.floor_id) if room else None
        port = ports_by_id.get(dev.switch_port_id) if dev.switch_port_id else None
        if port is None and room and room.id in ports_by_room_id:
            port = ports_by_room_id[room.id]

        telem = telem_by_uuid.get(dev.rincon_uuid) if dev.rincon_uuid else None

        # Determine connection_mode, ANI, PHY error rate, STP cost, root status
        conn_mode = dev.connection_mode
        if not conn_mode and telem:
            conn_mode = (
                telem.connection_mode.value
                if hasattr(telem.connection_mode, "value")
                else str(telem.connection_mode)
            )

        ani = telem.ofdm_ani_level if telem is not None else dev.ofdm_ani_level
        noise_floor = telem.noise_floor_dbm if telem is not None else None
        phy_rate = telem.phy_error_rate if telem is not None else None
        stp_cost = telem.stp_path_cost if telem is not None else None
        desig_root = telem.designated_root if telem is not None else None
        is_ghost = telem.is_ghost_group if telem is not None else False
        is_root = bool(
            conn_mode == ConnectionMode.ETHERNET_ROOT.value
            or (stp_cost == 0 and dev.device_role == DeviceRole.SONOS_PLAYER.value)
        )

        # Determine RSSI dBm for node (from connected BSSID reading or room survey)
        rssi_dbm: int | None = None
        if room:
            survey = latest_survey_by_room_id.get(room.id)
            if survey:
                s_readings = readings_by_survey_id.get(survey.id, [])
                conn_reading = next(
                    (
                        r_item
                        for r_item in s_readings
                        if r_item.is_connected
                        or (
                            survey.connected_bssid
                            and r_item.bssid.upper() == survey.connected_bssid.upper()
                        )
                    ),
                    None,
                )
                if conn_reading is not None:
                    rssi_dbm = conn_reading.rssi_dbm
                elif survey.best_5ghz_dbm is not None:
                    rssi_dbm = survey.best_5ghz_dbm
                elif survey.best_24ghz_dbm is not None:
                    rssi_dbm = survey.best_24ghz_dbm
            if rssi_dbm is None:
                rssi_dbm = room.best_5ghz_rssi_dbm or room.best_24ghz_rssi_dbm

        # Determine AP channel summary if WIFI_AP
        ap_channels: str | None = None
        if dev.device_role == DeviceRole.WIFI_AP.value:
            ap_short_slug = (
                "galerie-ap" if "galerie" in dev.slug else "kitchen-ap"
            )
            ap_rads = radios_by_ap_slug.get(ap_short_slug, [])
            if ap_rads:
                ap_rads_sorted = sorted(ap_rads, key=lambda r: r.channel)
                parts = [
                    f"{r.band} Ch {r.channel} ({r.width_mhz}MHz)"
                    for r in ap_rads_sorted
                ]
                ap_channels = " · ".join(parts)
            elif "galerie" in dev.slug:
                ap_channels = "2.4GHz Ch 1 (20MHz) · 5GHz Ch 44 (80MHz)"
            else:
                ap_channels = "2.4GHz Ch 11 (20MHz) · 5GHz Ch 40 (40MHz)"

        # Coordinates (x, y)
        slot_idx = room_slot_counts.get(dev.room_id, 0)
        room_slot_counts[dev.room_id] = slot_idx + 1
        if dev.slug in _DEVICE_LAYOUT_COORDS:
            default_x, default_y = _DEVICE_LAYOUT_COORDS[dev.slug]
            # If room coordinates were customized via CRUD, shift accordingly
            if room and (room.pos_x != 150.0 or room.pos_y != 450.0) and dev.slug.startswith("sonos-wohnzimmer"):
                x = room.pos_x + (slot_idx * 90.0)
                y = room.pos_y + (slot_idx * 40.0)
            else:
                x, y = default_x, default_y
        elif room:
            x = room.pos_x + (slot_idx * 95.0)
            y = room.pos_y + ((slot_idx % 2) * 55.0)
        else:
            x = 120.0 + (slot_idx * 100.0)
            y = 700.0

        node = TopologyNodeSchema(
            id=dev.slug,
            device_id=dev.id,
            slug=dev.slug,
            name=dev.name,
            device_role=dev.device_role,
            model_name=dev.model_name,
            ip_address=dev.ip_address or (telem.ip_address if telem else None),
            base_mac=dev.base_mac,
            rincon_uuid=dev.rincon_uuid,
            room_id=room.id if room else dev.room_id,
            room_slug=room.slug if room else None,
            room_name=room.name if room else None,
            floor_id=floor.id if floor else None,
            floor_slug=floor.slug if floor else None,
            floor_name=floor.name if floor else None,
            connection_mode=conn_mode,
            health_grade=dev.health_grade,
            ofdm_ani_level=ani,
            noise_floor_dbm=noise_floor,
            phy_error_rate=phy_rate,
            stp_path_cost=stp_cost,
            designated_root=desig_root,
            is_stp_root=is_root,
            is_ghost_group=is_ghost,
            rssi_dbm=rssi_dbm,
            ap_channels=ap_channels,
            switch_port_number=port.port_number if port else None,
            x=x,
            y=y,
            pos_x=x,
            pos_y=y,
        )
        nodes_by_slug[node.slug] = node
        if node.rincon_uuid:
            nodes_by_uuid[node.rincon_uuid] = node

    # Fallback synthesis for Fritzbox 6660 if not yet in DB
    if "router-fritzbox-6660" not in nodes_by_slug:
        keller_room = rooms_by_slug.get("keller")
        keller_floor = floors_by_id.get(keller_room.floor_id) if keller_room else None
        fb_node = TopologyNodeSchema(
            id="router-fritzbox-6660",
            device_id=None,
            slug="router-fritzbox-6660",
            name="Fritzbox 6660",
            device_role=DeviceRole.ROUTER.value,
            model_name="FRITZ!Box 6660 Cable",
            ip_address="192.168.178.1",
            base_mac="0C:72:74:00:63:9A",
            room_id=keller_room.id if keller_room else None,
            room_slug="keller",
            room_name="Keller",
            floor_id=keller_floor.id if keller_floor else None,
            floor_slug="keller",
            floor_name="Keller",
            health_grade=HealthGrade.EXCELLENT.value,
            x=80.0,
            y=720.0,
            pos_x=80.0,
            pos_y=720.0,
        )
        nodes_by_slug[fb_node.slug] = fb_node

    all_edges: list[DeviceConnectionEdgeSchema] = []

    def _add_edge(
        edge_id: str,
        layer: str,
        src: TopologyNodeSchema,
        tgt: TopologyNodeSchema,
        label: str,
        *,
        is_forwarding: bool = True,
        stp_state: str | None = None,
        band: str | None = None,
        channel: int | None = None,
        from_db: int | None = None,
        to_db: int | None = None,
        rssi_dbm: int | None = None,
        link_speed_mbps: int | None = None,
        port_number: int | None = None,
        vlan_label: str | None = None,
        health_grade: str = HealthGrade.GOOD.value,
    ) -> None:
        all_edges.append(
            DeviceConnectionEdgeSchema(
                id=edge_id,
                layer=layer,
                source=src.id,
                source_id=src.id,
                source_slug=src.slug,
                source_name=src.name,
                target=tgt.id,
                target_id=tgt.id,
                target_slug=tgt.slug,
                target_name=tgt.name,
                label=label,
                is_forwarding=is_forwarding,
                line_style="solid" if is_forwarding else "dashed",
                stp_state=stp_state,
                band=band,
                channel=channel,
                from_db=from_db,
                to_db=to_db,
                rssi_dbm=rssi_dbm,
                link_speed_mbps=link_speed_mbps,
                port_number=port_number,
                vlan_label=vlan_label,
                health_grade=health_grade,
            )
        )

    # =========================================================================
    # 1. WIRED_LAN Layer
    # =========================================================================
    fritzbox = nodes_by_slug.get("router-fritzbox-6660")
    firewalla = nodes_by_slug.get("router-firewalla-purple")
    switch_node = nodes_by_slug.get("switch-netgear-gs316ep")
    galerie_ap = nodes_by_slug.get("ap-galerie-eap650")
    kitchen_ap = nodes_by_slug.get("ap-kitchen-eap650")

    if fritzbox and firewalla:
        _add_edge(
            edge_id="wired-fritzbox-to-firewalla",
            layer="WIRED_LAN",
            src=fritzbox,
            tgt=firewalla,
            label="WAN/Uplink (2.5GbE Cable Bridge)",
            link_speed_mbps=1000,
            health_grade=HealthGrade.EXCELLENT.value,
        )

    if firewalla and switch_node:
        _add_edge(
            edge_id="wired-firewalla-to-gs316ep",
            layer="WIRED_LAN",
            src=firewalla,
            tgt=switch_node,
            label="Port 1 Trunk — VLANs 1, 10, 20, 30",
            port_number=1,
            vlan_label="VLANs 1, 10, 20, 30",
            link_speed_mbps=1000,
            health_grade=HealthGrade.EXCELLENT.value,
        )

    if switch_node and galerie_ap:
        _add_edge(
            edge_id="wired-gs316ep-to-galerie-ap",
            layer="WIRED_LAN",
            src=switch_node,
            tgt=galerie_ap,
            label="Port 11 Trunk — VLANs 1, 10, 20, 30",
            port_number=11,
            vlan_label="VLANs 1, 10, 20, 30",
            link_speed_mbps=1000,
            health_grade=HealthGrade.EXCELLENT.value,
        )

    if switch_node and kitchen_ap:
        _add_edge(
            edge_id="wired-gs316ep-to-kitchen-ap",
            layer="WIRED_LAN",
            src=switch_node,
            tgt=kitchen_ap,
            label="Port 12 Trunk — VLANs 1, 10, 20, 30",
            port_number=12,
            vlan_label="VLANs 1, 10, 20, 30",
            link_speed_mbps=1000,
            health_grade=HealthGrade.GOOD.value,
        )

    if switch_node:
        for node in nodes_by_slug.values():
            if node.device_role == DeviceRole.SONOS_PLAYER.value and node.connection_mode in (
                ConnectionMode.ETHERNET_ROOT.value,
                ConnectionMode.ETHERNET_NODE.value,
            ):
                port_num = node.switch_port_number or 13
                cost = node.stp_path_cost if node.stp_path_cost is not None else (
                    0 if node.connection_mode == ConnectionMode.ETHERNET_ROOT.value else 10
                )
                role_tag = (
                    f"STP Root Cost {cost}"
                    if node.connection_mode == ConnectionMode.ETHERNET_ROOT.value
                    else f"Wired Leaf Cost {cost}"
                )
                _add_edge(
                    edge_id=f"wired-gs316ep-to-{node.slug}",
                    layer="WIRED_LAN",
                    src=switch_node,
                    tgt=node,
                    label=f"Port {port_num} — VLAN 10, 100FD, {role_tag}",
                    stp_state="FORWARDING",
                    port_number=port_num,
                    vlan_label="VLAN 10",
                    link_speed_mbps=100,
                    health_grade=node.health_grade,
                )

    # =========================================================================
    # 2. WIFI_INFRA Layer
    # =========================================================================
    for node in nodes_by_slug.values():
        is_station_sonos = (
            node.device_role == DeviceRole.SONOS_PLAYER.value
            and node.connection_mode == ConnectionMode.STATION_MODE.value
        )
        is_client_dev = node.device_role == DeviceRole.CLIENT_DEVICE.value
        if not (is_station_sonos or is_client_dev):
            continue

        room = rooms_by_id.get(node.room_id) if node.room_id else None
        survey = latest_survey_by_room_id.get(room.id) if room else None
        ap_node = galerie_ap or kitchen_ap
        band = "5GHz"
        channel = 44
        rssi = node.rssi_dbm if node.rssi_dbm is not None else -75
        speed = 1201

        if survey:
            if survey.best_ap_slug == "kitchen-ap" and kitchen_ap:
                ap_node = kitchen_ap
                channel = 40
            s_readings = readings_by_survey_id.get(survey.id, [])
            conn_br = next(
                (
                    r_item
                    for r_item in s_readings
                    if r_item.is_connected
                    or (
                        survey.connected_bssid
                        and r_item.bssid.upper() == survey.connected_bssid.upper()
                    )
                ),
                None,
            )
            if conn_br is not None:
                band = conn_br.band
                channel = conn_br.channel
                rssi = conn_br.rssi_dbm
                if conn_br.ap_device_slug == "kitchen-ap" and kitchen_ap:
                    ap_node = kitchen_ap
                elif conn_br.ap_device_slug == "galerie-ap" and galerie_ap:
                    ap_node = galerie_ap
            if survey.link_speed_mbps is not None:
                speed = survey.link_speed_mbps

        if ap_node:
            edge_grade = grade_wifi_dbm(rssi)
            _add_edge(
                edge_id=f"wifi-{ap_node.slug}-to-{node.slug}",
                layer="WIFI_INFRA",
                src=ap_node,
                tgt=node,
                label=f"{band} Ch {channel} {rssi} dBm ({speed} Mbps)",
                band=band,
                channel=channel,
                rssi_dbm=rssi,
                link_speed_mbps=speed,
                health_grade=edge_grade,
            )

    # Also ensure Kitchen EAP650 has WIFI_INFRA room coverage link(s) so both APs are represented
    if kitchen_ap:
        for cov_room_slug, fallback_ch, fallback_rssi, fallback_spd in (
            ("kueche", 40, -58, 1201),
            ("noemi", 40, -72, 573),
            ("keller", 40, -68, 1201),
        ):
            cov_room = rooms_by_slug.get(cov_room_slug)
            if not cov_room:
                continue
            target_node = next(
                (
                    n
                    for n in nodes_by_slug.values()
                    if n.room_id == cov_room.id
                    and n.device_role == DeviceRole.SONOS_PLAYER.value
                ),
                None,
            )
            if not target_node:
                continue
            already_linked = any(
                e.layer == "WIFI_INFRA"
                and e.source == kitchen_ap.id
                and e.target == target_node.id
                for e in all_edges
            )
            if already_linked:
                continue

            survey = latest_survey_by_room_id.get(cov_room.id)
            band = "5GHz"
            ch = fallback_ch
            rssi = fallback_rssi
            spd = fallback_spd
            if survey:
                if survey.link_speed_mbps is not None:
                    spd = survey.link_speed_mbps
                s_readings = readings_by_survey_id.get(survey.id, [])
                k_reading = next(
                    (
                        r_item
                        for r_item in s_readings
                        if r_item.ap_device_slug == "kitchen-ap"
                        and r_item.band == "5GHz"
                    ),
                    None,
                )
                if k_reading is not None:
                    ch = k_reading.channel
                    rssi = k_reading.rssi_dbm

            _add_edge(
                edge_id=f"wifi-{kitchen_ap.slug}-coverage-{target_node.slug}",
                layer="WIFI_INFRA",
                src=kitchen_ap,
                tgt=target_node,
                label=f"{band} Ch {ch} {rssi} dBm ({spd} Mbps)",
                band=band,
                channel=ch,
                rssi_dbm=rssi,
                link_speed_mbps=spd,
                health_grade=grade_wifi_dbm(rssi),
            )

    # =========================================================================
    # 3. SONOS_MESH Layer
    # =========================================================================
    if latest_sonos:
        for idx, link in enumerate(latest_sonos.mesh_links, start=1):
            node_a = nodes_by_uuid.get(link.source_rincon_uuid)
            node_b = nodes_by_uuid.get(link.target_rincon_uuid)
            if not node_a or not node_b:
                continue

            # Dedicated 5 GHz Ch 48 HT_SATELLITE bonds (Beam -> LR & RR)
            is_ht_bond = bool(
                link.channel == 48
                or node_a.connection_mode == ConnectionMode.HT_SATELLITE.value
                or node_b.connection_mode == ConnectionMode.HT_SATELLITE.value
            )
            if is_ht_bond:
                if node_a.connection_mode == ConnectionMode.HT_SATELLITE.value:
                    src_node, tgt_node = node_b, node_a
                else:
                    src_node, tgt_node = node_a, node_b
                snr_grade = grade_sonos_snr_db(link.from_db, link.to_db)
                _add_edge(
                    edge_id=f"sonos-ht-bond-{src_node.slug}-to-{tgt_node.slug}",
                    layer="SONOS_MESH",
                    src=src_node,
                    tgt=tgt_node,
                    label=f"5GHz Ch 48 HT Bond · {link.from_db}/{link.to_db} dB",
                    is_forwarding=True,
                    stp_state="HT_BOND",
                    band="5GHz",
                    channel=48,
                    from_db=link.from_db,
                    to_db=link.to_db,
                    health_grade=snr_grade,
                )
                continue

            # Skip SonosNet Ch 6 links for nodes currently operating in 5 GHz STATION_MODE
            if (
                node_a.connection_mode == ConnectionMode.STATION_MODE.value
                or node_b.connection_mode == ConnectionMode.STATION_MODE.value
            ):
                continue

            # Orient edge from upstream (lower STP cost / root) -> downstream leaf
            cost_a = node_a.stp_path_cost if node_a.stp_path_cost is not None else 999
            cost_b = node_b.stp_path_cost if node_b.stp_path_cost is not None else 999
            if cost_b <= cost_a:
                src_node, tgt_node = node_b, node_a
            else:
                src_node, tgt_node = node_a, node_b

            is_fwd = link.stp_state.upper() != "BLOCKING"
            stp_state = "FORWARDING" if is_fwd else "BLOCKING"
            snr_grade = grade_sonos_snr_db(link.from_db, link.to_db)
            state_badge = "STP FORWARDING" if is_fwd else "STP 00 BLOCKING"

            _add_edge(
                edge_id=f"sonos-mesh-{idx}-{src_node.slug}-to-{tgt_node.slug}-{stp_state.lower()}",
                layer="SONOS_MESH",
                src=src_node,
                tgt=tgt_node,
                label=f"Ch {link.channel} · {link.from_db}/{link.to_db} dB ({state_badge})",
                is_forwarding=is_fwd,
                stp_state=stp_state,
                band="2.4GHz",
                channel=link.channel,
                from_db=link.from_db,
                to_db=link.to_db,
                health_grade=snr_grade,
            )

    # Filter edges by layer_filter and include_blocking
    allowed_layers = _resolve_allowed_layers(layer_filter)
    filtered_edges = [
        e
        for e in all_edges
        if e.layer in allowed_layers and (include_blocking or e.is_forwarding)
    ]

    # Filter nodes (and incident edges) by floor_slug / room_slug when requested
    filtered_nodes = list(nodes_by_slug.values())
    if floor_slug:
        norm_floor = floor_slug.strip().lower()
        filtered_nodes = [
            n for n in filtered_nodes if (n.floor_slug or "").lower() == norm_floor
        ]
    if room_slug:
        norm_room = room_slug.strip().lower()
        filtered_nodes = [
            n for n in filtered_nodes if (n.room_slug or "").lower() == norm_room
        ]

    if floor_slug or room_slug:
        matched_ids = {n.id for n in filtered_nodes}
        filtered_edges = [
            e
            for e in filtered_edges
            if e.source in matched_ids or e.target in matched_ids
        ]

    designated_root = (
        latest_sonos.designated_stp_root
        if latest_sonos
        else f"{EXPECTED_STP_ROOT} (Wohnzimmer_Bookshelf 192.168.10.230)"
    )

    return TopologyGraphResponse(
        layer_filter=(layer_filter or "ALL").strip().upper(),
        floor_slug=floor_slug,
        room_slug=room_slug,
        include_blocking=include_blocking,
        designated_stp_root=designated_root,
        total_nodes=len(filtered_nodes),
        total_edges=len(filtered_edges),
        nodes=filtered_nodes,
        edges=filtered_edges,
    )
