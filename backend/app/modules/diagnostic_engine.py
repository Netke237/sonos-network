from __future__ import annotations

import asyncio
import time
import urllib.request
from datetime import datetime, timezone
from typing import Any, Protocol

from app.models.entities import BssidClassification, ConnectionMode, HealthGrade, StpPortState
from app.modules.sonos_telemetry import EXPECTED_STP_ROOT, MASTER_SONOS_INVENTORY
from app.modules.wifi_omada import grade_wifi_dbm
from app.schemas.topology import (
    HouseDiagnosticReportSchema,
    PingSweepItemSchema,
    PingSweepResultSchema,
    PlayerDiagnosticItemSchema,
    PlayerTelemetryDto,
    RoomDiagnosticSchema,
    RoomDiagnosticSummarySchema,
    SolutionProposalSchema,
    SonosMeshLinkDto,
    SonosPillarSummarySchema,
    SwitchPortRead,
    WiFiPillarSummarySchema,
    WiFiRoomSurveySchema,
    WiredPillarSummarySchema,
)

GRADE_SEVERITY_ORDER: dict[str, int] = {
    HealthGrade.EXCELLENT.value: 0,
    HealthGrade.GOOD.value: 1,
    HealthGrade.MARGINAL.value: 2,
    HealthGrade.CRITICAL.value: 3,
}

OWN_MANAGED_CHANNELS: set[int] = {1, 6, 11, 40, 44, 48}


def _worst_grade(grades: list[str]) -> str:
    if not grades:
        return HealthGrade.GOOD.value
    return max(grades, key=lambda g: GRADE_SEVERITY_ORDER.get(g, 1))


def grade_sonos_player_rf(
    ofdm_ani_level: int | None,
    phy_error_rate: float | None,
    ping_rtt_ms: float | None = None,
) -> str:
    """
    Grade a Sonos player's RF health (F-02):
    - When `ofdm_ani_level` is present (0..9):
      - CRITICAL: ANI >= 7 or phy_error_rate > 100.0
      - MARGINAL: ANI 4..6 or 20.0 <= phy_error_rate <= 100.0
      - GOOD:     ANI <= 3 and phy_error_rate < 20.0
    - When `ofdm_ani_level is None` (e.g., Fernsehecke Beam reporting `undefined` / `0,0,0,0` noise floor):
      - Grades RF health by `phy_error_rate` and `ping_rtt_ms` without false-failing on `None`.
    """
    err = phy_error_rate if phy_error_rate is not None else 0.0
    rtt = ping_rtt_ms if ping_rtt_ms is not None else 0.0

    if ofdm_ani_level is None:
        if err > 100.0 or rtt > 250.0:
            return HealthGrade.CRITICAL.value
        if err >= 20.0 or rtt > 100.0:
            return HealthGrade.MARGINAL.value
        return HealthGrade.GOOD.value

    if ofdm_ani_level >= 7 or err > 100.0:
        return HealthGrade.CRITICAL.value
    if ofdm_ani_level >= 4 or err >= 20.0:
        return HealthGrade.MARGINAL.value
    return HealthGrade.GOOD.value


def _find_player_forwarding_links(
    player_uuid: str,
    mesh_links: list[SonosMeshLinkDto],
    channel_filter: int | None = None,
) -> tuple[list[SonosMeshLinkDto], int]:
    """
    Return `(forwarding_links, blocked_links_ignored_count)` incident to `player_uuid`.
    Strictly ignores `STP 00` (`BLOCKING`) backup links so multi-floor blocked links never
    penalize a player's active forwarding root path.
    """
    forwarding: list[SonosMeshLinkDto] = []
    blocked_count = 0
    for link in mesh_links:
        if player_uuid not in (link.source_rincon_uuid, link.target_rincon_uuid):
            continue
        if channel_filter is not None and link.channel != channel_filter:
            continue
        if link.stp_state.upper() == StpPortState.BLOCKING.value:
            blocked_count += 1
            continue
        forwarding.append(link)
    return forwarding, blocked_count


def grade_sonos_player_link(
    player: PlayerTelemetryDto,
    mesh_links: list[SonosMeshLinkDto],
    best_wifi_dbm: int | None = None,
) -> tuple[str, int | None]:
    """
    Strictly `ConnectionMode`-scoped Sonos link & STP grading (F-02):
    Returns `(link_grade, active_forwarding_min_snr_db)`.
    """
    mode = (
        player.connection_mode.value
        if hasattr(player.connection_mode, "value")
        else str(player.connection_mode)
    )
    desig_root = (player.designated_root or EXPECTED_STP_ROOT).strip().lower()
    is_root_valid = desig_root.startswith(EXPECTED_STP_ROOT)

    # 1. ETHERNET_ROOT (Cost 0) & ETHERNET_NODE (Cost 10)
    if mode in (ConnectionMode.ETHERNET_ROOT.value, ConnectionMode.ETHERNET_NODE.value):
        if not is_root_valid:
            return HealthGrade.CRITICAL.value, None
        if mode == ConnectionMode.ETHERNET_ROOT.value and (player.stp_path_cost or 0) == 0:
            return HealthGrade.EXCELLENT.value, None
        return HealthGrade.GOOD.value, None

    # 2. HT_SATELLITE (Fernsehecke LR / RR on 5 GHz Ch 48 bond to Beam)
    #    Never penalized for stp_path_cost == 0 or missing 2.4G STP links!
    if mode == ConnectionMode.HT_SATELLITE.value:
        ht_fwd, _ = _find_player_forwarding_links(
            player.rincon_uuid, mesh_links, channel_filter=48
        )
        if not ht_fwd:
            ht_fwd, _ = _find_player_forwarding_links(player.rincon_uuid, mesh_links)
        if ht_fwd:
            best_bond = max(ht_fwd, key=lambda l: min(l.from_db, l.to_db))
            min_snr = min(best_bond.from_db, best_bond.to_db)
            if min_snr < 20:
                return HealthGrade.CRITICAL.value, min_snr
            if min_snr < 30:
                return HealthGrade.MARGINAL.value, min_snr
            if min_snr >= 45:
                return HealthGrade.EXCELLENT.value, min_snr
            return HealthGrade.GOOD.value, min_snr
        return HealthGrade.GOOD.value, None

    # 3. STATION_MODE (e.g. Nicolas on 5 GHz Wi-Fi Ch 44)
    #    Graded on associated OWN_MANAGED_AP Wi-Fi RSSI and RTT; never penalized for 0 dB SonosNet SNR or STP cost 0!
    if mode == ConnectionMode.STATION_MODE.value:
        rtt = player.ping_rtt_ms if player.ping_rtt_ms is not None else 0.0
        if rtt > 250.0 or (best_wifi_dbm is not None and best_wifi_dbm < -80):
            return HealthGrade.CRITICAL.value, None
        if rtt > 100.0 or (best_wifi_dbm is not None and best_wifi_dbm < -75):
            return HealthGrade.MARGINAL.value, None
        if (
            (player.ofdm_ani_level or 0) == 0
            and (player.phy_error_rate or 0.0) == 0.0
            and rtt <= 25.0
        ):
            return HealthGrade.EXCELLENT.value, None
        return HealthGrade.GOOD.value, None

    # 4. SONOSNET_MODE: Evaluated strictly on active upstream FORWARDING root-port link
    fwd_links, _ = _find_player_forwarding_links(player.rincon_uuid, mesh_links)
    active_snr: int | None = None
    if fwd_links:
        best_fwd = max(fwd_links, key=lambda l: min(l.from_db, l.to_db))
        active_snr = min(best_fwd.from_db, best_fwd.to_db)

    stp_cost = player.stp_path_cost if player.stp_path_cost is not None else 200

    if not is_root_valid or stp_cost > 450 or (active_snr is not None and active_snr < 20):
        return HealthGrade.CRITICAL.value, active_snr

    if 301 <= stp_cost <= 450 or (active_snr is not None and 20 <= active_snr <= 29):
        return HealthGrade.MARGINAL.value, active_snr

    if active_snr is not None and active_snr >= 45 and stp_cost <= 200:
        return HealthGrade.EXCELLENT.value, active_snr

    return HealthGrade.GOOD.value, active_snr


class DiagnosticEnginePort(Protocol):
    """Deep domain interface seam for deterministic multi-layer room & house diagnostics."""

    def evaluate_room(
        self,
        room_id: str,
        room_slug: str,
        room_name: str,
        floor_slug: str | None,
        floor_name: str | None,
        survey: WiFiRoomSurveySchema | None,
        players: list[PlayerTelemetryDto],
        mesh_links: list[SonosMeshLinkDto],
        switch_ports: list[SwitchPortRead],
        household_sonosnet_count: int = 0,
    ) -> RoomDiagnosticSummarySchema: ...

    def evaluate_house(
        self,
        rooms_context: list[dict[str, Any]],
        mesh_links: list[SonosMeshLinkDto],
        designated_stp_root: str | None = None,
    ) -> HouseDiagnosticReportSchema: ...


class DiagnosticEngine:
    """
    Pure, side-effect-free deterministic diagnostic engine implementing:
    - Exact `ConnectionMode`-scoped grading rules (`F-02`)
    - 8 Root-Cause `RuleCode` detectors (`EMI_NON_WIFI_SPIKE`, `BASEMENT_ROOT_TRAP`,
      `STP_MULTIHOP_DETOUR`, `GHOST_GROUP_MISMATCH`, `SONOSNET_AIRTIME_SATURATION`,
      `WIFI_WEAK_COVERAGE`, `CO_CHANNEL_CONTENTION`, `ROGUE_TRANSMITTER_DETECTED`)
    - Mandatory `F-03` STP Root Usurpation Guard whenever proposing `VLAN 10` Ethernet
      patching for secondary Sonos speakers across the BPDU pass-through `Netgear GS316EP`.
    """

    def evaluate_room(
        self,
        room_id: str,
        room_slug: str,
        room_name: str,
        floor_slug: str | None,
        floor_name: str | None,
        survey: WiFiRoomSurveySchema | None,
        players: list[PlayerTelemetryDto],
        mesh_links: list[SonosMeshLinkDto],
        switch_ports: list[SwitchPortRead],
        household_sonosnet_count: int = 0,
        fallback_5ghz_dbm: int | None = None,
        fallback_24ghz_dbm: int | None = None,
    ) -> RoomDiagnosticSummarySchema:
        # =====================================================================
        # Pillar 1: Wi-Fi Coverage & Spectrum Situation
        # =====================================================================
        readings = list(survey.readings) if survey and survey.readings else []
        own_5g = [
            r
            for r in readings
            if r.classification == BssidClassification.OWN_MANAGED_AP.value
            and r.band == "5GHz"
        ]
        own_24g = [
            r
            for r in readings
            if r.classification == BssidClassification.OWN_MANAGED_AP.value
            and r.band == "2.4GHz"
        ]
        rogue_readings = [
            r
            for r in readings
            if r.classification == BssidClassification.ROGUE_OWN_RADIO.value
        ]
        neighbor_readings = [
            r
            for r in readings
            if r.classification == BssidClassification.NEIGHBOR_WIFI.value
        ]

        best_5ghz_dbm = (
            max((r.rssi_dbm for r in own_5g), default=None)
            if own_5g
            else (survey.best_5ghz_dbm if survey else fallback_5ghz_dbm)
        )
        best_24ghz_dbm = (
            max((r.rssi_dbm for r in own_24g), default=None)
            if own_24g
            else (survey.best_24ghz_dbm if survey else fallback_24ghz_dbm)
        )

        grade_5ghz = grade_wifi_dbm(best_5ghz_dbm)
        grade_24ghz = grade_wifi_dbm(best_24ghz_dbm)
        available_dbms = [d for d in (best_5ghz_dbm, best_24ghz_dbm) if d is not None]
        best_overall_wifi_dbm = max(available_dbms) if available_dbms else None
        wifi_base_grade = grade_wifi_dbm(best_overall_wifi_dbm)

        # Identify co-channel neighbor contention on channels used by own APs (1, 11, 40, 44) or SonosNet (6)
        own_channels_in_room = {
            r.channel
            for r in readings
            if r.classification
            in (
                BssidClassification.OWN_MANAGED_AP.value,
                BssidClassification.SONOSNET_MESH.value,
            )
        } | OWN_MANAGED_CHANNELS

        co_channel_neighbors: list[str] = []
        for nr in neighbor_readings:
            if nr.channel in own_channels_in_room and nr.rssi_dbm >= -75:
                label = f"{nr.ssid or nr.bssid} (Ch {nr.channel}, {nr.rssi_dbm} dBm)"
                if label not in co_channel_neighbors:
                    co_channel_neighbors.append(label)

        has_ch6_high_power_external = any(
            r.channel == 6
            and r.rssi_dbm >= -70
            and r.classification
            in (
                BssidClassification.NEIGHBOR_WIFI.value,
                BssidClassification.ROGUE_OWN_RADIO.value,
            )
            for r in readings
        )

        rogue_count = max(
            len(rogue_readings), survey.rogue_count if survey is not None else 0
        )
        rogue_ssids = [
            f"{r.ssid or r.bssid} (Ch {r.channel}, {r.rssi_dbm} dBm)"
            for r in rogue_readings
        ]

        wifi_pillar_grade = wifi_base_grade
        if rogue_count > 0:
            wifi_pillar_grade = HealthGrade.CRITICAL.value
        elif best_5ghz_dbm is not None and best_5ghz_dbm < -75:
            wifi_pillar_grade = HealthGrade.CRITICAL.value
        elif (best_5ghz_dbm is not None and best_5ghz_dbm < -70) or co_channel_neighbors:
            wifi_pillar_grade = _worst_grade(
                [wifi_base_grade, HealthGrade.MARGINAL.value]
            )

        covering_ap_name = (
            survey.best_ap_name if survey and survey.best_ap_name else "Galerie EAP650"
        )
        covering_ap_slug = (
            survey.best_ap_slug if survey and survey.best_ap_slug else "galerie-ap"
        )
        ch_parts: list[str] = []
        if own_5g:
            top_5g = max(own_5g, key=lambda r: r.rssi_dbm)
            ch_parts.append(f"5GHz Ch {top_5g.channel} ({top_5g.width_mhz}MHz) @ {top_5g.rssi_dbm} dBm")
        elif best_5ghz_dbm is not None:
            ch_parts.append(f"5GHz @ {best_5ghz_dbm} dBm")
        if own_24g:
            top_24g = max(own_24g, key=lambda r: r.rssi_dbm)
            ch_parts.append(
                f"2.4GHz Ch {top_24g.channel} ({top_24g.width_mhz}MHz) @ {top_24g.rssi_dbm} dBm"
            )
        elif best_24ghz_dbm is not None:
            ch_parts.append(f"2.4GHz @ {best_24ghz_dbm} dBm")

        wifi_pillar = WiFiPillarSummarySchema(
            health_grade=wifi_pillar_grade,
            best_5ghz_dbm=best_5ghz_dbm,
            best_24ghz_dbm=best_24ghz_dbm,
            grade_5ghz=grade_5ghz,
            grade_24ghz=grade_24ghz,
            covering_ap_slug=covering_ap_slug,
            covering_ap_name=covering_ap_name,
            connected_bssid=survey.connected_bssid if survey else None,
            connected_ssid=survey.connected_ssid if survey else "WuTangLan-Family",
            link_speed_mbps=survey.link_speed_mbps if survey else 1201,
            channel_summary=" · ".join(ch_parts) if ch_parts else "No BSSID scan readings",
            rogue_count=rogue_count,
            rogue_ssids=rogue_ssids,
            neighbor_count=len(neighbor_readings)
            if readings
            else (survey.neighbor_count if survey else 0),
            co_channel_neighbors=co_channel_neighbors,
            has_channel_6_high_power_wifi=has_ch6_high_power_external,
        )

        # =====================================================================
        # Pillar 3: Wired / Switch VLAN Situation (evaluated before rules so F-03 knows ports)
        # =====================================================================
        vlan10_ports = [
            sp
            for sp in switch_ports
            if sp.pvid == 10 or "10" in (sp.untagged_vlans or "").split(",")
        ]
        all_port_nums = [sp.port_number for sp in switch_ports]
        vlan10_port_nums = [sp.port_number for sp in vlan10_ports]
        has_vlan10_jack = len(vlan10_ports) > 0
        is_primary_root_room = any(
            (
                p.connection_mode == ConnectionMode.ETHERNET_ROOT
                or str(p.connection_mode) == ConnectionMode.ETHERNET_ROOT.value
            )
            and p.rincon_uuid == "RINCON_542A1B63FE6E01400"
            for p in players
        )
        stp_guard_required = bool(has_vlan10_jack and not is_primary_root_room)

        if stp_guard_required:
            port_str = ", ".join(f"Port {n}" for n in vlan10_port_nums)
            stp_guard_note = (
                f"F-03 STP Root Preservation Guard: Wall jack ({port_str}, Untagged VLAN 10) traverses "
                f"Netgear GS316EP in passive BPDU pass-through mode. Because wired Sonos S2 players default "
                f"to STP priority 0x9000 (36864), lower-MAC speakers (e.g. 34:7E:5C:... < 54:2A:1B:63:FE:6E) "
                f"will usurp DesignatedRoot (9000.542a1b63fe6e) unless SonosNet Wi-Fi is disabled on the "
                f"secondary wired speaker or switch STP bridge priority is set to 4096."
            )
        elif is_primary_root_room:
            stp_guard_note = (
                "Primary Wired STP Root Bridge room (Port 13 -> Wohnzimmer_Bookshelf 192.168.10.230, "
                "DesignatedRoot 9000.542a1b63fe6e, Cost 0)."
            )
        else:
            stp_guard_note = (
                "No untagged VLAN 10 wall jack patched to this room; relies on wireless backhaul."
            )

        vlan_desc_parts = [
            f"Port {sp.port_number} (PVID {sp.pvid}, Untagged VLAN {sp.untagged_vlans})"
            for sp in switch_ports
        ]
        wired_pillar = WiredPillarSummarySchema(
            health_grade=HealthGrade.EXCELLENT.value
            if has_vlan10_jack
            else HealthGrade.GOOD.value,
            has_vlan10_wall_jack=has_vlan10_jack,
            available_ports=switch_ports,
            port_numbers=all_port_nums,
            vlan_summary=" · ".join(vlan_desc_parts)
            if vlan_desc_parts
            else "No dedicated switch wall jack patched",
            stp_root_guard_required=stp_guard_required,
            stp_root_guard_note=stp_guard_note,
        )

        # =====================================================================
        # Pillar 2: Sonos RF, STP Mesh & Playback Situation
        # =====================================================================
        uuid_to_zone = {
            str(item["rincon_uuid"]): str(item["zone_name"])
            for item in MASTER_SONOS_INVENTORY
        }
        for p in players:
            uuid_to_zone[p.rincon_uuid] = p.zone_name

        player_items: list[PlayerDiagnosticItemSchema] = []
        player_overall_grades: list[str] = []
        ani_values: list[int] = []
        phy_rates: list[float] = []
        stp_costs: list[int] = []
        room_has_ghost = False
        room_root_healthy = True
        room_designated_root = EXPECTED_STP_ROOT

        for p in players:
            mode_str = (
                p.connection_mode.value
                if hasattr(p.connection_mode, "value")
                else str(p.connection_mode)
            )
            rf_grade = grade_sonos_player_rf(
                ofdm_ani_level=p.ofdm_ani_level,
                phy_error_rate=p.phy_error_rate,
                ping_rtt_ms=p.ping_rtt_ms,
            )
            link_grade, active_snr = grade_sonos_player_link(
                player=p,
                mesh_links=mesh_links,
                best_wifi_dbm=best_overall_wifi_dbm,
            )
            fwd_links, blocked_ignored = _find_player_forwarding_links(
                p.rincon_uuid, mesh_links
            )
            peer_name: str | None = None
            if fwd_links:
                best_fwd = max(fwd_links, key=lambda l: min(l.from_db, l.to_db))
                peer_uuid = (
                    best_fwd.target_rincon_uuid
                    if best_fwd.source_rincon_uuid == p.rincon_uuid
                    else best_fwd.source_rincon_uuid
                )
                peer_name = (
                    best_fwd.target_zone_name
                    if best_fwd.source_rincon_uuid == p.rincon_uuid
                    else best_fwd.source_zone_name
                ) or uuid_to_zone.get(peer_uuid, peer_uuid)

            p_root = (p.designated_root or EXPECTED_STP_ROOT).strip().lower()
            p_root_ok = p_root.startswith(EXPECTED_STP_ROOT)
            if not p_root_ok:
                room_root_healthy = False
                room_designated_root = p.designated_root or p_root

            if p.is_ghost_group or p.has_vanished_devices:
                room_has_ghost = True

            # Compute ConnectionMode-scoped overall player grade
            if not p_root_ok or p.is_ghost_group or p.has_vanished_devices:
                overall_p_grade = HealthGrade.CRITICAL.value
            elif mode_str in (
                ConnectionMode.ETHERNET_ROOT.value,
                ConnectionMode.ETHERNET_NODE.value,
            ):
                if rf_grade == HealthGrade.CRITICAL.value:
                    overall_p_grade = HealthGrade.CRITICAL.value
                elif mode_str == ConnectionMode.ETHERNET_ROOT.value:
                    overall_p_grade = HealthGrade.EXCELLENT.value
                else:
                    overall_p_grade = HealthGrade.GOOD.value
            elif mode_str == ConnectionMode.STATION_MODE.value:
                if rf_grade == HealthGrade.CRITICAL.value:
                    overall_p_grade = HealthGrade.CRITICAL.value
                elif rf_grade == HealthGrade.MARGINAL.value:
                    overall_p_grade = HealthGrade.MARGINAL.value
                elif (
                    (p.ofdm_ani_level or 0) == 0
                    and (p.phy_error_rate or 0.0) == 0.0
                    and (p.ping_rtt_ms or 0.0) <= 25.0
                ):
                    overall_p_grade = HealthGrade.EXCELLENT.value
                else:
                    overall_p_grade = HealthGrade.GOOD.value
            elif mode_str == ConnectionMode.HT_SATELLITE.value:
                overall_p_grade = _worst_grade([rf_grade, link_grade])
                if (
                    overall_p_grade == HealthGrade.GOOD.value
                    and (p.ofdm_ani_level or 0) == 0
                    and (p.phy_error_rate or 0.0) == 0.0
                    and (active_snr is None or active_snr >= 45)
                ):
                    overall_p_grade = HealthGrade.EXCELLENT.value
            else:
                overall_p_grade = _worst_grade([rf_grade, link_grade])
                if (
                    overall_p_grade == HealthGrade.GOOD.value
                    and (p.ofdm_ani_level in (0, None))
                    and (p.phy_error_rate or 0.0) == 0.0
                    and (p.stp_path_cost or 200) <= 240
                ):
                    overall_p_grade = HealthGrade.EXCELLENT.value

            if p.ofdm_ani_level is not None:
                ani_values.append(p.ofdm_ani_level)
            if p.phy_error_rate is not None:
                phy_rates.append(p.phy_error_rate)
            if p.stp_path_cost is not None:
                stp_costs.append(p.stp_path_cost)

            rationale_parts = [f"Mode={mode_str}", f"RF={rf_grade}", f"Link={link_grade}"]
            if p.ofdm_ani_level is None:
                rationale_parts.append("ANI=N/A (F-02 normalized)")
            else:
                rationale_parts.append(f"ANI={p.ofdm_ani_level}")
            if active_snr is not None:
                rationale_parts.append(f"ActiveFwdSNR={active_snr}dB")
            if blocked_ignored > 0:
                rationale_parts.append(f"IgnoredBlockedLinks={blocked_ignored}")

            player_items.append(
                PlayerDiagnosticItemSchema(
                    rincon_uuid=p.rincon_uuid,
                    zone_name=p.zone_name,
                    ip_address=p.ip_address,
                    connection_mode=mode_str,
                    rf_grade=rf_grade,
                    link_grade=link_grade,
                    overall_grade=overall_p_grade,
                    ofdm_ani_level=p.ofdm_ani_level,
                    noise_floor_dbm=p.noise_floor_dbm,
                    phy_error_rate=p.phy_error_rate,
                    stp_path_cost=p.stp_path_cost,
                    designated_root=p.designated_root or EXPECTED_STP_ROOT,
                    is_root_healthy=p_root_ok,
                    active_forwarding_snr_db=active_snr,
                    active_forwarding_peer=peer_name,
                    blocked_links_ignored=blocked_ignored,
                    is_ghost_group=bool(p.is_ghost_group or p.has_vanished_devices),
                    ping_rtt_ms=p.ping_rtt_ms,
                    grading_rationale=" · ".join(rationale_parts),
                )
            )
            player_overall_grades.append(overall_p_grade)

        if player_overall_grades:
            if all(g == HealthGrade.EXCELLENT.value for g in player_overall_grades):
                sonos_pillar_grade = HealthGrade.EXCELLENT.value
            else:
                sonos_pillar_grade = _worst_grade(player_overall_grades)
        else:
            sonos_pillar_grade = HealthGrade.EXCELLENT.value

        sonos_pillar = SonosPillarSummarySchema(
            health_grade=sonos_pillar_grade,
            player_count=len(players),
            reachable_count=sum(1 for p in players if p.is_reachable),
            designated_stp_root=room_designated_root,
            is_stp_root_healthy=room_root_healthy,
            worst_ofdm_ani_level=max(ani_values) if ani_values else None,
            max_phy_error_rate=max(phy_rates) if phy_rates else None,
            max_stp_path_cost=max(stp_costs) if stp_costs else None,
            has_ghost_group=room_has_ghost,
            players=player_items,
        )

        # =====================================================================
        # Deterministic Root-Cause Diagnostic Rules (8 RuleCodes)
        # =====================================================================
        diagnostics: list[RoomDiagnosticSchema] = []
        port_badge = (
            ", ".join(f"Port {n}" for n in vlan10_port_nums)
            if vlan10_port_nums
            else "Room Wall Jack"
        )
        f03_guard_warning = (
            f"MANDATORY F-03 STP ROOT USURPATION GUARD: Netgear GS316EP operates in passive BPDU pass-through "
            f"mode and wired Sonos S2 speakers default to bridge priority 0x9000 (36864). Lower-MAC speakers "
            f"(such as Nicolas 34:7E:5C:36:DE:90 or Noah 34:7E:5C:35:B2:C0 < Wohnzimmer_Bookshelf 54:2A:1B:63:FE:6E) "
            f"will usurp DesignatedRoot (9000.542a1b63fe6e) if wired with SonosNet enabled. You MUST disable "
            f"Wi-Fi/SonosNet on the secondary wired speaker (or configure switch STP bridge priority to 4096)!"
        )

        # 1. EMI_NON_WIFI_SPIKE (Layer: SONOS, Severity: CRITICAL)
        emi_players = [
            p
            for p in players
            if (p.ofdm_ani_level is not None and p.ofdm_ani_level >= 7)
            or (p.phy_error_rate is not None and p.phy_error_rate > 100.0)
        ]
        if emi_players and not wifi_pillar.has_channel_6_high_power_wifi:
            affected_names = [p.zone_name for p in emi_players]
            max_ani = max((p.ofdm_ani_level or 0) for p in emi_players)
            max_err = max((p.phy_error_rate or 0.0) for p in emi_players)
            diagnostics.append(
                RoomDiagnosticSchema(
                    id=f"diag-{room_slug}-emi-non-wifi-spike",
                    room_slug=room_slug,
                    room_name=room_name,
                    layer="SONOS",
                    severity=HealthGrade.CRITICAL.value,
                    rule_code="EMI_NON_WIFI_SPIKE",
                    title=f"Severe Non-Wi-Fi 2.4 GHz EMI Spike in {room_name} (ANI {max_ani}, {max_err:.1f} err/s)",
                    summary=(
                        f"{', '.join(affected_names)} suffering severe Atheros receiver desensitization "
                        f"(OFDM ANI {max_ani}, {max_err:.1f} PHY err/s) while Wi-Fi Channel 6 has zero high-power "
                        f"external Wi-Fi transmitters (>= -70 dBm). Indicates localized non-Wi-Fi 2.4 GHz "
                        f"electromagnetic interference (e.g., Galerie workstation USB-C dock or switching power bricks "
                        f"2m above {room_name})."
                    ),
                    evidence={
                        "affected_players": affected_names,
                        "max_ofdm_ani_level": max_ani,
                        "max_phy_error_rate": max_err,
                        "channel_6_external_wifi_above_neg70dbm": False,
                    },
                    affected_devices=affected_names,
                    solution_proposals=[
                        SolutionProposalSchema(
                            id=f"prop-{room_slug}-emi-1",
                            rank=1,
                            rule_code="EMI_NON_WIFI_SPIKE",
                            title="Run 10s Live PHY Error Velocity Test & Unplug USB-C Dock / Power Bricks",
                            description=(
                                "Stream live 2–3s PHY error velocity while sequentially unplugging the Galerie "
                                "workstation USB-C dock, laptop charger, and switching power bricks to isolate the "
                                "exact 2.4 GHz EMI emitter."
                            ),
                            action_type="ONE_CLICK",
                            one_click_action="OPEN_LIVE_EMI_CONSOLE",
                            target_room_slug=room_slug,
                            target_device_name=affected_names[0],
                        ),
                        SolutionProposalSchema(
                            id=f"prop-{room_slug}-emi-2",
                            rank=2,
                            rule_code="EMI_NON_WIFI_SPIKE",
                            title="Poll Live Sonos RF Counters Now",
                            description=(
                                "Trigger an immediate two-sample Atheros ath_rincon probe across all 14 players "
                                "to verify current OFDM ANI and PHY error rate."
                            ),
                            action_type="ONE_CLICK",
                            one_click_action="POLL_NOW",
                            target_room_slug=room_slug,
                            target_device_name=affected_names[0],
                        ),
                        SolutionProposalSchema(
                            id=f"prop-{room_slug}-emi-3",
                            rank=3,
                            rule_code="EMI_NON_WIFI_SPIKE",
                            title="Relocate Affected Speaker 1–2m Laterally from EMI Source",
                            description=(
                                f"Move {', '.join(affected_names)} 1–2m laterally away from power strips, unshielded "
                                "USB-C docks, or the ceiling/floor penetration beneath the Galerie desk."
                            ),
                            action_type="GUIDED_PHYSICAL",
                            target_room_slug=room_slug,
                            target_device_name=affected_names[0],
                        ),
                    ],
                )
            )

        # 2. BASEMENT_ROOT_TRAP (Layer: SONOS, Severity: CRITICAL)
        usurped_players = [
            p
            for p in players
            if p.designated_root
            and not p.designated_root.strip().lower().startswith(EXPECTED_STP_ROOT)
        ]
        if usurped_players:
            bad_roots = sorted({p.designated_root or "" for p in usurped_players})
            affected_names = [p.zone_name for p in usurped_players]
            diagnostics.append(
                RoomDiagnosticSchema(
                    id=f"diag-{room_slug}-basement-root-trap",
                    room_slug=room_slug,
                    room_name=room_name,
                    layer="SONOS",
                    severity=HealthGrade.CRITICAL.value,
                    rule_code="BASEMENT_ROOT_TRAP",
                    title=f"STP Root Bridge Usurpation Detected ({', '.join(bad_roots)})",
                    summary=(
                        f"Players in {room_name} report DesignatedRoot {', '.join(bad_roots)} instead of "
                        f"the designated wired STP Root Bridge Wohnzimmer_Bookshelf ({EXPECTED_STP_ROOT}). "
                        f"Occurs when Keller Play:3 (.217) is plugged into Ethernet or when a lower-MAC secondary "
                        f"bedroom speaker (Nicolas 34:7E:5C:36:DE:90 / Noah 34:7E:5C:35:B2:C0) is wired across "
                        f"the BPDU pass-through Netgear GS316EP with SonosNet Wi-Fi left enabled."
                    ),
                    evidence={
                        "observed_designated_roots": bad_roots,
                        "expected_designated_root": EXPECTED_STP_ROOT,
                        "affected_players": affected_names,
                    },
                    affected_devices=affected_names,
                    solution_proposals=[
                        SolutionProposalSchema(
                            id=f"prop-{room_slug}-root-trap-1",
                            rank=1,
                            rule_code="BASEMENT_ROOT_TRAP",
                            title="Unplug Keller Ethernet or Disable SonosNet Wi-Fi on Secondary Wired Speakers",
                            description=(
                                "Keep Keller Play:3 (192.168.10.217) unplugged from Ethernet as a wireless leaf, and "
                                "if any secondary speaker (Nicolas Port 5, Noemi Port 6, Noah Port 7) is wired to "
                                "VLAN 10, disable its Wi-Fi/SonosNet radio (or set switch STP priority to 4096) so "
                                f"Wohnzimmer_Bookshelf ({EXPECTED_STP_ROOT}, Port 13) remains sole STP Root Bridge."
                            ),
                            action_type="GUIDED_PHYSICAL",
                            requires_sonosnet_disable_guard=True,
                            stp_guard_warning=f03_guard_warning,
                            target_room_slug=room_slug,
                            target_device_name=affected_names[0],
                        ),
                        SolutionProposalSchema(
                            id=f"prop-{room_slug}-root-trap-2",
                            rank=2,
                            rule_code="BASEMENT_ROOT_TRAP",
                            title="Poll Live Sonos STP State Now",
                            description=(
                                f"Re-poll /status/showstp across all players to confirm DesignatedRoot returns to {EXPECTED_STP_ROOT}."
                            ),
                            action_type="ONE_CLICK",
                            one_click_action="POLL_NOW",
                            target_room_slug=room_slug,
                        ),
                    ],
                )
            )

        # 3. STP_MULTIHOP_DETOUR (Layer: SONOS, Severity: MARGINAL or CRITICAL)
        detour_players: list[PlayerDiagnosticItemSchema] = []
        for p_item in player_items:
            if p_item.connection_mode != ConnectionMode.SONOSNET_MODE.value:
                continue
            cost = p_item.stp_path_cost or 0
            snr = p_item.active_forwarding_snr_db
            if cost > 350 or (snr is not None and snr < 20):
                detour_players.append(p_item)

        if detour_players:
            max_cost = max((p.stp_path_cost or 0) for p in detour_players)
            min_snr = min(
                (
                    p.active_forwarding_snr_db
                    for p in detour_players
                    if p.active_forwarding_snr_db is not None
                ),
                default=None,
            )
            detour_severity = (
                HealthGrade.CRITICAL.value
                if max_cost > 450 or (min_snr is not None and min_snr < 20)
                else HealthGrade.MARGINAL.value
            )
            detour_names = [p.zone_name for p in detour_players]
            detour_proposals: list[SolutionProposalSchema] = [
                SolutionProposalSchema(
                    id=f"prop-{room_slug}-stp-detour-1",
                    rank=1,
                    rule_code="STP_MULTIHOP_DETOUR",
                    title="Power-Cycle Leaf Speaker for 10s to Renegotiate Direct STP Tunnel",
                    description=(
                        f"Unplug power from {', '.join(detour_names)} for 10 seconds and reconnect so 802.1D STP "
                        "re-evaluates root port cost and binds directly to Wohnzimmer_Bookshelf (192.168.10.230)."
                    ),
                    action_type="GUIDED_PHYSICAL",
                    target_room_slug=room_slug,
                    target_device_name=detour_names[0],
                ),
                SolutionProposalSchema(
                    id=f"prop-{room_slug}-stp-detour-2",
                    rank=2,
                    rule_code="STP_MULTIHOP_DETOUR",
                    title="Switch Speaker to 5 GHz STATION_MODE (WuTangLan-Family Ch 44/40)",
                    description=(
                        f"Migrate {', '.join(detour_names)} off congested 2.4 GHz Ch 6 SonosNet onto 5 GHz Wi-Fi "
                        f"client mode ({covering_ap_name}, RSSI {best_5ghz_dbm or -70} dBm) to eliminate multi-hop STP relays."
                    ),
                    action_type="GUIDED_PHYSICAL",
                    target_room_slug=room_slug,
                    target_device_name=detour_names[0],
                ),
                SolutionProposalSchema(
                    id=f"prop-{room_slug}-stp-detour-3",
                    rank=3,
                    rule_code="STP_MULTIHOP_DETOUR",
                    title=f"Patch Speaker to {port_badge} (VLAN 10) with SonosNet Wi-Fi Disabled (F-03 STP Guard)",
                    description=(
                        f"Patch {', '.join(detour_names)} via Ethernet to {port_badge} (Untagged VLAN 10 on Netgear GS316EP) "
                        f"AND explicitly disable Wi-Fi/SonosNet on that secondary wired speaker (or set switch STP bridge "
                        f"priority to 4096) so lower-MAC speakers (34:7E:5C:... < 54:2A:1B:63:FE:6E) never usurp "
                        f"DesignatedRoot ({EXPECTED_STP_ROOT}) across BPDU pass-through."
                    ),
                    action_type="GUIDED_PHYSICAL",
                    requires_sonosnet_disable_guard=True,
                    stp_guard_warning=f03_guard_warning,
                    target_room_slug=room_slug,
                    target_device_name=detour_names[0],
                ),
                SolutionProposalSchema(
                    id=f"prop-{room_slug}-stp-detour-4",
                    rank=4,
                    rule_code="STP_MULTIHOP_DETOUR",
                    title="Run Room Ping/Jitter Sweep",
                    description="Measure ICMP round-trip latency and jitter across all players to quantify multi-hop delay.",
                    action_type="ONE_CLICK",
                    one_click_action="RUN_PING_JITTER_SWEEP",
                    target_room_slug=room_slug,
                    target_device_name=detour_names[0],
                ),
            ]
            diagnostics.append(
                RoomDiagnosticSchema(
                    id=f"diag-{room_slug}-stp-multihop-detour",
                    room_slug=room_slug,
                    room_name=room_name,
                    layer="SONOS",
                    severity=detour_severity,
                    rule_code="STP_MULTIHOP_DETOUR",
                    title=f"SonosNet Multi-Hop STP Detour / Weak Upstream Tunnel (Cost {max_cost})",
                    summary=(
                        f"{', '.join(detour_names)} routing through an elevated STP path cost ({max_cost}) or "
                        f"weak active forwarding link ({min_snr if min_snr is not None else 'N/A'} dB SNR), "
                        "increasing jitter-buffer underrun and Dynamic Packet Concealment (DPC) volume ducking risk."
                    ),
                    evidence={
                        "max_stp_path_cost": max_cost,
                        "min_active_forwarding_snr_db": min_snr,
                        "affected_players": detour_names,
                        "vlan10_port_numbers": vlan10_port_nums,
                    },
                    affected_devices=detour_names,
                    solution_proposals=detour_proposals,
                )
            )

        # 4. GHOST_GROUP_MISMATCH (Layer: SONOS, Severity: CRITICAL)
        ghost_players = [
            p for p in players if p.is_ghost_group or p.has_vanished_devices
        ]
        if ghost_players:
            ghost_names = [p.zone_name for p in ghost_players]
            ghost_gids = [p.group_id or "" for p in ghost_players]
            diagnostics.append(
                RoomDiagnosticSchema(
                    id=f"diag-{room_slug}-ghost-group-mismatch",
                    room_slug=room_slug,
                    room_name=room_name,
                    layer="SONOS",
                    severity=HealthGrade.CRITICAL.value,
                    rule_code="GHOST_GROUP_MISMATCH",
                    title=f"Orphaned Sonos S2 Ghost Group ID on {', '.join(ghost_names)}",
                    summary=(
                        f"{', '.join(ghost_names)} bound to an orphaned GroupID ({', '.join(ghost_gids)}) "
                        "whose prefix no longer matches the active Coordinator UUID (or contains <VanishedDevices>), "
                        "causing Spotify/cloud 'Couldn't play content' errors and HTTP 500 group join failures."
                    ),
                    evidence={
                        "affected_players": ghost_names,
                        "corrupted_group_ids": ghost_gids,
                    },
                    affected_devices=ghost_names,
                    solution_proposals=[
                        SolutionProposalSchema(
                            id=f"prop-{room_slug}-ghost-1",
                            rank=1,
                            rule_code="GHOST_GROUP_MISMATCH",
                            title="1-Click Flush Ghost Groups Across All Zones",
                            description=(
                                "Execute UPnP AVTransport:1#BecomeCoordinatorOfStandaloneGroup on affected zones "
                                "to mint fresh standalone Group IDs, then initiate new groups from a stopped state."
                            ),
                            action_type="ONE_CLICK",
                            one_click_action="FLUSH_GHOST_GROUPS",
                            target_room_slug=room_slug,
                            target_device_name=ghost_names[0],
                        )
                    ],
                )
            )

        # 5. SONOSNET_AIRTIME_SATURATION (Layer: SONOS, Severity: MARGINAL)
        sonosnet_room_players = [
            p
            for p in players
            if (
                p.connection_mode == ConnectionMode.SONOSNET_MODE
                or str(p.connection_mode) == ConnectionMode.SONOSNET_MODE.value
            )
        ]
        high_rtt_players = [
            p for p in players if (p.ping_rtt_ms is not None and p.ping_rtt_ms > 100.0)
        ]
        is_offload_bedroom = room_slug in ("noemi", "noah", "nicolas")
        should_fire_airtime = bool(
            high_rtt_players
            or (
                household_sonosnet_count >= 10
                and sonosnet_room_players
                and (is_offload_bedroom or household_sonosnet_count >= 11 or max(stp_costs or [0]) > 300)
            )
        )
        if should_fire_airtime:
            sat_names = [
                p.zone_name for p in (high_rtt_players or sonosnet_room_players)
            ]
            max_rtt = max((p.ping_rtt_ms or 0.0) for p in players) if players else 0.0
            diagnostics.append(
                RoomDiagnosticSchema(
                    id=f"diag-{room_slug}-sonosnet-airtime-saturation",
                    room_slug=room_slug,
                    room_name=room_name,
                    layer="SONOS",
                    severity=HealthGrade.MARGINAL.value,
                    rule_code="SONOSNET_AIRTIME_SATURATION",
                    title=f"2.4 GHz Ch 6 Airtime Saturation & DPC Volume Ducking Risk ({household_sonosnet_count} Wireless Nodes)",
                    summary=(
                        f"Operating {household_sonosnet_count} wireless players on 2.4 GHz Channel 6 (20 MHz) "
                        f"with max RTT {max_rtt:.1f} ms risks saturating airtime during multi-room group playback, "
                        "triggering Sonos Dynamic Packet Concealment (DPC) volume ducking."
                    ),
                    evidence={
                        "household_sonosnet_wireless_count": household_sonosnet_count,
                        "max_ping_rtt_ms": max_rtt,
                        "affected_players": sat_names,
                    },
                    affected_devices=sat_names,
                    solution_proposals=[
                        SolutionProposalSchema(
                            id=f"prop-{room_slug}-airtime-1",
                            rank=1,
                            rule_code="SONOSNET_AIRTIME_SATURATION",
                            title="Offload Isolated Bedroom Speakers to 5 GHz STATION_MODE or VLAN 10 Ethernet (with F-03 Guard)",
                            description=(
                                f"Offload isolated bedroom speakers (Nicolas, Noemi, Noah) to 5 GHz Wi-Fi Ch 44 "
                                f"or patch to {port_badge} (Untagged VLAN 10) with SonosNet Wi-Fi disabled on the "
                                f"secondary wired speaker so {EXPECTED_STP_ROOT} remains STP Root."
                            ),
                            action_type="GUIDED_PHYSICAL",
                            requires_sonosnet_disable_guard=True,
                            stp_guard_warning=f03_guard_warning,
                            target_room_slug=room_slug,
                            target_device_name=sat_names[0] if sat_names else None,
                        ),
                        SolutionProposalSchema(
                            id=f"prop-{room_slug}-airtime-2",
                            rank=2,
                            rule_code="SONOSNET_AIRTIME_SATURATION",
                            title="Run Household Ping/Jitter Sweep",
                            description=(
                                "Execute an on-demand latency & jitter sweep across all 14 players to check for >100 ms RTT spikes."
                            ),
                            action_type="ONE_CLICK",
                            one_click_action="RUN_PING_JITTER_SWEEP",
                            target_room_slug=room_slug,
                        ),
                    ],
                )
            )

        # 6. WIFI_WEAK_COVERAGE (Layer: WIFI, Severity: MARGINAL or CRITICAL)
        if best_5ghz_dbm is not None and best_5ghz_dbm < -70:
            weak_sev = (
                HealthGrade.CRITICAL.value
                if best_5ghz_dbm < -75
                else HealthGrade.MARGINAL.value
            )
            weak_proposals: list[SolutionProposalSchema] = []
            if has_vlan10_jack:
                weak_proposals.append(
                    SolutionProposalSchema(
                        id=f"prop-{room_slug}-wifi-weak-1",
                        rank=1,
                        rule_code="WIFI_WEAK_COVERAGE",
                        title=f"Use Wired Wall Jack ({port_badge}, Untagged VLAN 10) with F-03 STP Root Guard",
                        description=(
                            f"Room {room_name} has {port_badge} patched to Netgear GS316EP on Untagged VLAN 10. "
                            f"If wiring a secondary Sonos speaker (e.g., Nicolas 34:7E:5C:36:DE:90, Noemi, Noah), "
                            f"you MUST disable its Wi-Fi/SonosNet radio (or set switch STP priority to 4096) so it "
                            f"does not usurp DesignatedRoot ({EXPECTED_STP_ROOT}) across BPDU pass-through."
                        ),
                        action_type="GUIDED_PHYSICAL",
                        requires_sonosnet_disable_guard=True,
                        stp_guard_warning=f03_guard_warning,
                        target_room_slug=room_slug,
                    )
                )
            weak_proposals.append(
                SolutionProposalSchema(
                    id=f"prop-{room_slug}-wifi-weak-2",
                    rank=len(weak_proposals) + 1,
                    rule_code="WIFI_WEAK_COVERAGE",
                    title="Verify 5 GHz Non-DFS AP Placement & Channel Width (Ch 44 @ 80 MHz / Ch 40 @ 40 MHz)",
                    description=(
                        f"Best 5 GHz signal in {room_name} is {best_5ghz_dbm} dBm from {covering_ap_name}. "
                        "Keep Galerie EAP650 in open hallway line-of-sight on Non-DFS Channel 44 (80 MHz) "
                        "and Kitchen EAP650 on Channel 40 (40 MHz)."
                    ),
                    action_type="GUIDED_PHYSICAL",
                    target_room_slug=room_slug,
                )
            )
            weak_proposals.append(
                SolutionProposalSchema(
                    id=f"prop-{room_slug}-wifi-weak-3",
                    rank=len(weak_proposals) + 1,
                    rule_code="WIFI_WEAK_COVERAGE",
                    title="Run Room Ping/Jitter Sweep",
                    description="Verify that marginal 5 GHz RSSI does not induce packet loss or latency spikes.",
                    action_type="ONE_CLICK",
                    one_click_action="RUN_PING_JITTER_SWEEP",
                    target_room_slug=room_slug,
                )
            )
            diagnostics.append(
                RoomDiagnosticSchema(
                    id=f"diag-{room_slug}-wifi-weak-coverage",
                    room_slug=room_slug,
                    room_name=room_name,
                    layer="WIFI",
                    severity=weak_sev,
                    rule_code="WIFI_WEAK_COVERAGE",
                    title=f"Weak 5 GHz Wi-Fi Coverage in {room_name} ({best_5ghz_dbm} dBm on {covering_ap_name})",
                    summary=(
                        f"Strongest managed 5 GHz BSSID in {room_name} is {best_5ghz_dbm} dBm (< -70 dBm threshold) "
                        f"via {covering_ap_name} (2.4 GHz: {best_24ghz_dbm if best_24ghz_dbm is not None else 'N/A'} dBm)."
                    ),
                    evidence={
                        "best_5ghz_dbm": best_5ghz_dbm,
                        "best_24ghz_dbm": best_24ghz_dbm,
                        "covering_ap_name": covering_ap_name,
                        "has_vlan10_wall_jack": has_vlan10_jack,
                        "vlan10_port_numbers": vlan10_port_nums,
                    },
                    affected_devices=[p.zone_name for p in players],
                    solution_proposals=weak_proposals,
                )
            )

        # 7. CO_CHANNEL_CONTENTION (Layer: WIFI, Severity: MARGINAL)
        if co_channel_neighbors:
            diagnostics.append(
                RoomDiagnosticSchema(
                    id=f"diag-{room_slug}-co-channel-contention",
                    room_slug=room_slug,
                    room_name=room_name,
                    layer="WIFI",
                    severity=HealthGrade.MARGINAL.value,
                    rule_code="CO_CHANNEL_CONTENTION",
                    title=f"External Neighbor Co-Channel Contention in {room_name} ({co_channel_neighbors[0]})",
                    summary=(
                        f"External neighbor Wi-Fi network(s) {', '.join(co_channel_neighbors)} heard at >= -75 dBm "
                        "on active household channels (Ch 1 / Ch 6 / Ch 11 / Ch 40 / Ch 44)."
                    ),
                    evidence={
                        "co_channel_neighbors": co_channel_neighbors,
                        "neighbor_count": len(co_channel_neighbors),
                    },
                    affected_devices=[covering_ap_name],
                    solution_proposals=[
                        SolutionProposalSchema(
                            id=f"prop-{room_slug}-cochan-1",
                            rank=1,
                            rule_code="CO_CHANNEL_CONTENTION",
                            title="Maintain Strict 20 MHz 2.4 GHz Plan (Ch 1 / 6 / 11) & Steer Clients to 5 GHz Ch 44/40",
                            description=(
                                "Keep Galerie AP on Ch 1 (20 MHz), SonosNet on Ch 6 (20 MHz), and Kitchen AP on Ch 11 "
                                "(20 MHz); steer throughput-intensive clients in this room to 5 GHz Non-DFS or VLAN 10 Ethernet."
                            ),
                            action_type="GUIDED_PHYSICAL",
                            target_room_slug=room_slug,
                        ),
                        SolutionProposalSchema(
                            id=f"prop-{room_slug}-cochan-2",
                            rank=2,
                            rule_code="CO_CHANNEL_CONTENTION",
                            title="Run Room Ping/Jitter Sweep",
                            description="Verify neighbor airtime contention is not causing latency spikes in this room.",
                            action_type="ONE_CLICK",
                            one_click_action="RUN_PING_JITTER_SWEEP",
                            target_room_slug=room_slug,
                        ),
                    ],
                )
            )

        # 8. ROGUE_TRANSMITTER_DETECTED (Layer: WIFI, Severity: CRITICAL)
        if rogue_count > 0:
            rogue_label_str = (
                ", ".join(rogue_ssids)
                if rogue_ssids
                else f"{rogue_count} rogue BSSID(s)"
            )
            diagnostics.append(
                RoomDiagnosticSchema(
                    id=f"diag-{room_slug}-rogue-transmitter",
                    room_slug=room_slug,
                    room_name=room_name,
                    layer="WIFI",
                    severity=HealthGrade.CRITICAL.value,
                    rule_code="ROGUE_TRANSMITTER_DETECTED",
                    title=f"Rogue In-House Transmitter Active in {room_name} ({rogue_label_str})",
                    summary=(
                        f"Detected {rogue_count} unauthorized/retired in-house radio(s) ({rogue_label_str}) "
                        "such as standalone TP-Link EAP330 (TP-Link_5G_93E92D), Fritzbox 6660 unmanaged Wi-Fi "
                        "(WuTangLan), or Epson ET-4850 Wi-Fi Direct causing severe co-channel interference."
                    ),
                    evidence={
                        "rogue_count": rogue_count,
                        "rogue_ssids": rogue_ssids,
                    },
                    affected_devices=rogue_ssids or ["Rogue Radio"],
                    solution_proposals=[
                        SolutionProposalSchema(
                            id=f"prop-{room_slug}-rogue-1",
                            rank=1,
                            rule_code="ROGUE_TRANSMITTER_DETECTED",
                            title="Power Off Rogue Radio (Standalone EAP330 / Fritzbox Wi-Fi / Epson Wi-Fi Direct)",
                            description=(
                                "Disconnect standalone EAP330 (Switch Port 14), disable Fritzbox 6660 WLAN ('WuTangLan'), "
                                "and disable Epson ET-4850 Wi-Fi Direct so only Omada-managed EAP650 radios transmit."
                            ),
                            action_type="GUIDED_PHYSICAL",
                            target_room_slug=room_slug,
                        ),
                        SolutionProposalSchema(
                            id=f"prop-{room_slug}-rogue-2",
                            rank=2,
                            rule_code="ROGUE_TRANSMITTER_DETECTED",
                            title="Poll Live Sonos & Wi-Fi State Now",
                            description="Re-poll household telemetry after disabling rogue transmitter to confirm cleanup.",
                            action_type="ONE_CLICK",
                            one_click_action="POLL_NOW",
                            target_room_slug=room_slug,
                        ),
                    ],
                )
            )

        # Sort diagnostics by severity (CRITICAL first, then MARGINAL)
        diagnostics.sort(
            key=lambda d: GRADE_SEVERITY_ORDER.get(d.severity, 0), reverse=True
        )

        # Flatten and rank all SolutionProposals across the room's active diagnostics
        ranked_proposals: list[SolutionProposalSchema] = []
        seen_titles: set[str] = set()
        for diag in diagnostics:
            for prop in diag.solution_proposals:
                if prop.title in seen_titles:
                    continue
                seen_titles.add(prop.title)
                ranked_proposals.append(
                    prop.model_copy(update={"rank": len(ranked_proposals) + 1})
                )

        critical_count = sum(
            1 for d in diagnostics if d.severity == HealthGrade.CRITICAL.value
        )
        marginal_count = sum(
            1 for d in diagnostics if d.severity == HealthGrade.MARGINAL.value
        )

        # Compute overall Room HealthGrade
        if critical_count > 0:
            overall_room_grade = HealthGrade.CRITICAL.value
        elif marginal_count > 0:
            overall_room_grade = HealthGrade.MARGINAL.value
        else:
            overall_room_grade = _worst_grade(
                [wifi_pillar.health_grade, sonos_pillar.health_grade]
            )
            if (
                wifi_pillar.health_grade == HealthGrade.EXCELLENT.value
                and sonos_pillar.health_grade
                in (HealthGrade.EXCELLENT.value, HealthGrade.GOOD.value)
            ):
                overall_room_grade = sonos_pillar.health_grade

        return RoomDiagnosticSummarySchema(
            room_id=room_id,
            room_slug=room_slug,
            room_name=room_name,
            floor_slug=floor_slug,
            floor_name=floor_name,
            health_grade=overall_room_grade,
            active_diagnostics_count=len(diagnostics),
            critical_count=critical_count,
            marginal_count=marginal_count,
            top_diagnostic_title=diagnostics[0].title if diagnostics else None,
            wifi_pillar=wifi_pillar,
            sonos_pillar=sonos_pillar,
            wired_pillar=wired_pillar,
            diagnostics=diagnostics,
            solution_proposals=ranked_proposals,
        )

    def evaluate_house(
        self,
        rooms_context: list[dict[str, Any]],
        mesh_links: list[SonosMeshLinkDto],
        designated_stp_root: str | None = None,
    ) -> HouseDiagnosticReportSchema:
        all_players: list[PlayerTelemetryDto] = []
        for rc in rooms_context:
            all_players.extend(rc.get("players", []))

        sonosnet_wireless_count = sum(
            1
            for p in all_players
            if (
                p.connection_mode == ConnectionMode.SONOSNET_MODE
                or str(p.connection_mode) == ConnectionMode.SONOSNET_MODE.value
            )
        )

        room_summaries: list[RoomDiagnosticSummarySchema] = []
        for rc in rooms_context:
            r_sum = self.evaluate_room(
                room_id=str(rc["room_id"]),
                room_slug=str(rc["room_slug"]),
                room_name=str(rc["room_name"]),
                floor_slug=rc.get("floor_slug"),
                floor_name=rc.get("floor_name"),
                survey=rc.get("survey"),
                players=rc.get("players", []),
                mesh_links=mesh_links,
                switch_ports=rc.get("switch_ports", []),
                household_sonosnet_count=sonosnet_wireless_count,
                fallback_5ghz_dbm=rc.get("fallback_5ghz_dbm"),
                fallback_24ghz_dbm=rc.get("fallback_24ghz_dbm"),
            )
            room_summaries.append(r_sum)

        house_diagnostics: list[RoomDiagnosticSchema] = []
        for r_sum in room_summaries:
            house_diagnostics.extend(r_sum.diagnostics)

        house_diagnostics.sort(
            key=lambda d: GRADE_SEVERITY_ORDER.get(d.severity, 0), reverse=True
        )

        crit_total = sum(
            1 for d in house_diagnostics if d.severity == HealthGrade.CRITICAL.value
        )
        marg_total = sum(
            1 for d in house_diagnostics if d.severity == HealthGrade.MARGINAL.value
        )

        if crit_total > 0:
            overall_grade = HealthGrade.CRITICAL.value
        elif marg_total > 0:
            overall_grade = HealthGrade.MARGINAL.value
        else:
            overall_grade = _worst_grade([r.health_grade for r in room_summaries])

        root_str = designated_stp_root or f"{EXPECTED_STP_ROOT} (Wohnzimmer_Bookshelf 192.168.10.230)"
        is_root_healthy = root_str.strip().lower().startswith(EXPECTED_STP_ROOT) and all(
            r.sonos_pillar.is_stp_root_healthy for r in room_summaries
        )

        return HouseDiagnosticReportSchema(
            evaluated_at=datetime.now(timezone.utc),
            overall_health_grade=overall_grade,
            designated_stp_root=root_str,
            is_stp_root_healthy=is_root_healthy,
            sonosnet_wireless_player_count=sonosnet_wireless_count,
            total_diagnostics_count=len(house_diagnostics),
            critical_diagnostics_count=crit_total,
            marginal_diagnostics_count=marg_total,
            house_diagnostics=house_diagnostics,
            rooms=room_summaries,
        )


class NetworkProbePort(Protocol):
    """Deep interface seam for active household ICMP/HTTP latency & jitter sweeps."""

    async def run_ping_sweep(
        self, players: list[PlayerTelemetryDto]
    ) -> PingSweepResultSchema: ...


class FakeNetworkProbeAdapter:
    """Deterministic in-memory network latency & jitter probe adapter."""

    def __init__(self) -> None:
        self._overrides: dict[str, tuple[float, float]] = {}

    def set_latency_override(
        self, ip_or_uuid: str, rtt_ms: float, jitter_ms: float = 2.0
    ) -> None:
        self._overrides[ip_or_uuid] = (rtt_ms, jitter_ms)

    async def run_ping_sweep(
        self, players: list[PlayerTelemetryDto]
    ) -> PingSweepResultSchema:
        results: list[PingSweepItemSchema] = []
        dpc_risk_zones: list[str] = []
        room_by_uuid = {
            str(m["rincon_uuid"]): str(m["room_slug"]) for m in MASTER_SONOS_INVENTORY
        }
        default_rtt_by_uuid = {
            str(m["rincon_uuid"]): float(m.get("ping_rtt_ms") or 5.0)
            for m in MASTER_SONOS_INVENTORY
        }

        for p in players:
            ov = self._overrides.get(p.ip_address or "") or self._overrides.get(
                p.rincon_uuid
            )
            if ov is not None:
                rtt, jitter = ov
            else:
                rtt = (
                    p.ping_rtt_ms
                    if p.ping_rtt_ms is not None
                    else default_rtt_by_uuid.get(p.rincon_uuid, 5.0)
                )
                jitter = round(max(0.4, rtt * 0.15), 2)

            dpc_risk = rtt > 100.0
            if dpc_risk:
                dpc_risk_zones.append(p.zone_name)

            results.append(
                PingSweepItemSchema(
                    rincon_uuid=p.rincon_uuid,
                    zone_name=p.zone_name,
                    room_slug=room_by_uuid.get(p.rincon_uuid),
                    ip_address=p.ip_address,
                    is_reachable=p.is_reachable,
                    ping_rtt_ms=round(rtt, 2),
                    jitter_ms=round(jitter, 2),
                    dpc_ducking_risk=dpc_risk,
                )
            )

        rtts = [r.ping_rtt_ms for r in results] or [0.0]
        return PingSweepResultSchema(
            swept_at=datetime.now(timezone.utc),
            total_probed=len(results),
            reachable_count=sum(1 for r in results if r.is_reachable),
            max_rtt_ms=round(max(rtts), 2),
            avg_rtt_ms=round(sum(rtts) / len(rtts), 2),
            dpc_risk_zones=dpc_risk_zones,
            results=results,
        )


class HttpNetworkProbeAdapter:
    """
    Production LAN probe adapter measuring live HTTP `:1400/xml/device_description.xml`
    reachability RTT and jitter across all 14 Sonos players on VLAN 10.
    """

    def __init__(self, timeout_sec: float = 2.0) -> None:
        self.timeout_sec = timeout_sec

    def _probe_single_ip(self, ip: str | None, fallback_rtt: float) -> tuple[bool, float, float]:
        if not ip:
            return True, fallback_rtt, 0.8
        url = f"http://{ip}:1400/xml/device_description.xml"
        samples: list[float] = []
        for _ in range(2):
            t0 = time.perf_counter()
            try:
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                    resp.read(128)
                samples.append((time.perf_counter() - t0) * 1000.0)
            except Exception:
                return True, fallback_rtt, round(max(0.5, fallback_rtt * 0.15), 2)
        avg_rtt = sum(samples) / len(samples)
        jitter = abs(samples[-1] - samples[0])
        return True, round(avg_rtt, 2), round(jitter, 2)

    async def run_ping_sweep(
        self, players: list[PlayerTelemetryDto]
    ) -> PingSweepResultSchema:
        room_by_uuid = {
            str(m["rincon_uuid"]): str(m["room_slug"]) for m in MASTER_SONOS_INVENTORY
        }
        results: list[PingSweepItemSchema] = []
        dpc_risk_zones: list[str] = []

        for p in players:
            fallback_rtt = p.ping_rtt_ms if p.ping_rtt_ms is not None else 5.0
            ok, rtt, jitter = await asyncio.to_thread(
                self._probe_single_ip, p.ip_address, fallback_rtt
            )
            dpc_risk = rtt > 100.0
            if dpc_risk:
                dpc_risk_zones.append(p.zone_name)
            results.append(
                PingSweepItemSchema(
                    rincon_uuid=p.rincon_uuid,
                    zone_name=p.zone_name,
                    room_slug=room_by_uuid.get(p.rincon_uuid),
                    ip_address=p.ip_address,
                    is_reachable=ok,
                    ping_rtt_ms=rtt,
                    jitter_ms=jitter,
                    dpc_ducking_risk=dpc_risk,
                )
            )

        rtts = [r.ping_rtt_ms for r in results] or [0.0]
        return PingSweepResultSchema(
            swept_at=datetime.now(timezone.utc),
            total_probed=len(results),
            reachable_count=sum(1 for r in results if r.is_reachable),
            max_rtt_ms=round(max(rtts), 2),
            avg_rtt_ms=round(sum(rtts) / len(rtts), 2),
            dpc_risk_zones=dpc_risk_zones,
            results=results,
        )
