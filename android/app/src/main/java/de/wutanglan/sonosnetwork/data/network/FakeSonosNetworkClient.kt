package de.wutanglan.sonosnetwork.data.network

import de.wutanglan.sonosnetwork.data.models.*
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import java.time.Instant

class FakeSonosNetworkClient : SonosNetworkClientPort {

    var simulateNetworkError: Boolean = false
    var networkErrorMessage: String = "Network connection failed"
    var cannedOverview: HouseOverviewDto? = null
    var cannedTopology: TopologyGraphDto? = null
    var cannedHouseDiagnostics: HouseDiagnosticReportDto? = null

    private val surveyStore = mutableMapOf<String, MutableList<WiFiRoomSurveyDto>>()
    val submittedSurveys = mutableListOf<Pair<String, RoomSurveyInputDto>>()

    override suspend fun getOverview(): Result<HouseOverviewDto> {
        if (simulateNetworkError) return Result.failure(Exception(networkErrorMessage))
        cannedOverview?.let { return Result.success(it) }

        return Result.success(
            HouseOverviewDto(
                total_floors = 4,
                total_rooms = 11,
                total_sonos_players = 14,
                total_wifi_aps = 2,
                total_switch_ports = 16,
                designated_stp_root = "9000.542a1b63fe6e",
                ghost_group_count = 0,
                has_ghost_groups = false,
                active_diagnostics_count = 1,
                critical_diagnostics_count = 0,
                floors = listOf(
                    FloorMatrixItemDto(
                        id = "floor-og",
                        slug = "obergeschoss",
                        name = "Obergeschoss",
                        level_order = 2,
                        rooms = listOf(
                            RoomMatrixItemDto(
                                id = "room-galerie",
                                slug = "galerie",
                                name = "Galerie",
                                floor_id = "floor-og",
                                health_grade = "EXCELLENT",
                                best_5ghz_dbm = -48,
                                best_24ghz_dbm = -42,
                                best_ap_name = "Galerie AP",
                                link_speed_mbps = 1201,
                                devices = listOf(
                                    NetworkDeviceDto(
                                        id = "dev-galerie-sonos",
                                        slug = "galerie-sonos",
                                        name = "Galerie",
                                        device_role = "SONOS_PLAYER",
                                        connection_mode = "SONOSNET_MODE",
                                        ip_address = "192.168.10.162"
                                    )
                                )
                            )
                        )
                    ),
                    FloorMatrixItemDto(
                        id = "floor-eg",
                        slug = "erdgeschoss",
                        name = "Erdgeschoss",
                        level_order = 1,
                        rooms = listOf(
                            RoomMatrixItemDto(
                                id = "room-wohnzimmer",
                                slug = "wohnzimmer",
                                name = "Wohnzimmer",
                                floor_id = "floor-eg",
                                health_grade = "GOOD",
                                best_5ghz_dbm = -55,
                                best_24ghz_dbm = -52,
                                best_ap_name = "Galerie AP",
                                link_speed_mbps = 866,
                                devices = listOf(
                                    NetworkDeviceDto(
                                        id = "dev-wz-bookshelf",
                                        slug = "wohnzimmer-bookshelf",
                                        name = "Wohnzimmer_Bookshelf",
                                        device_role = "SONOS_PLAYER",
                                        connection_mode = "ETHERNET_ROOT",
                                        ip_address = "192.168.10.230"
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
    }

    override suspend fun getTopology(layer: String?): Result<TopologyGraphDto> {
        if (simulateNetworkError) return Result.failure(Exception(networkErrorMessage))
        cannedTopology?.let { return Result.success(it) }

        return Result.success(
            TopologyGraphDto(
                layer_filter = layer ?: "ALL",
                designated_stp_root = "9000.542a1b63fe6e",
                total_nodes = 2,
                total_edges = 1,
                nodes = listOf(
                    TopologyNodeDto(
                        id = "node-wz-bookshelf",
                        slug = "wohnzimmer-bookshelf",
                        name = "Wohnzimmer_Bookshelf",
                        device_role = "SONOS_PLAYER",
                        model_name = "Play:1",
                        ip_address = "192.168.10.230",
                        connection_mode = "ETHERNET_ROOT",
                        is_stp_root = true,
                        stp_path_cost = 0,
                        health_grade = "EXCELLENT"
                    ),
                    TopologyNodeDto(
                        id = "node-galerie",
                        slug = "galerie-sonos",
                        name = "Galerie",
                        device_role = "SONOS_PLAYER",
                        model_name = "One",
                        ip_address = "192.168.10.162",
                        connection_mode = "SONOSNET_MODE",
                        is_stp_root = false,
                        stp_path_cost = 250,
                        health_grade = "GOOD"
                    )
                ),
                edges = listOf(
                    DeviceConnectionEdgeDto(
                        id = "edge-mesh-1",
                        layer = "SONOS_MESH",
                        source = "node-wz-bookshelf",
                        source_id = "node-wz-bookshelf",
                        source_slug = "wohnzimmer-bookshelf",
                        source_name = "Wohnzimmer_Bookshelf",
                        target = "node-galerie",
                        target_id = "node-galerie",
                        target_slug = "galerie-sonos",
                        target_name = "Galerie",
                        label = "SNR 42/41 dB",
                        is_forwarding = true,
                        from_db = 42,
                        to_db = 41,
                        health_grade = "EXCELLENT"
                    )
                )
            )
        )
    }

    override suspend fun getHouseDiagnostics(): Result<HouseDiagnosticReportDto> {
        if (simulateNetworkError) return Result.failure(Exception(networkErrorMessage))
        cannedHouseDiagnostics?.let { return Result.success(it) }

        return Result.success(
            HouseDiagnosticReportDto(
                evaluated_at = Instant.now().toString(),
                overall_health_grade = "GOOD",
                designated_stp_root = "9000.542a1b63fe6e",
                is_stp_root_healthy = true,
                sonosnet_wireless_player_count = 11,
                total_diagnostics_count = 1,
                critical_diagnostics_count = 0,
                marginal_diagnostics_count = 1
            )
        )
    }

    override suspend fun getRoomDiagnostics(roomSlug: String): Result<RoomDiagnosticSummaryDto> {
        if (simulateNetworkError) return Result.failure(Exception(networkErrorMessage))

        return Result.success(
            RoomDiagnosticSummaryDto(
                room_id = "room-$roomSlug",
                room_slug = roomSlug,
                room_name = roomSlug.replaceFirstChar { it.uppercase() },
                health_grade = "GOOD",
                wifi_pillar = WiFiPillarSummaryDto(
                    health_grade = "GOOD",
                    best_5ghz_dbm = -58,
                    best_24ghz_dbm = -50,
                    covering_ap_name = "Galerie AP",
                    channel_summary = "Ch 44 (80 MHz) / Ch 1 (20 MHz)",
                    summary_note = "Strong coverage from Galerie AP"
                ),
                sonos_pillar = SonosPillarSummaryDto(
                    health_grade = "GOOD",
                    player_count = 1,
                    total_players = 1,
                    reachable_count = 1,
                    designated_stp_root = "9000.542a1b63fe6e",
                    summary_note = "Optimal SonosNet mesh forwarding link"
                ),
                wired_pillar = WiredPillarSummaryDto(
                    health_grade = "GOOD",
                    has_vlan10_wall_jack = true,
                    vlan_summary = "VLAN 10 Untagged wall jack available"
                ),
                diagnostics = emptyList(),
                solution_proposals = emptyList()
            )
        )
    }

    override suspend fun getRoomSurveys(roomSlug: String): Result<List<WiFiRoomSurveyDto>> {
        if (simulateNetworkError) return Result.failure(Exception(networkErrorMessage))
        return Result.success(surveyStore[roomSlug] ?: emptyList())
    }

    override suspend fun submitRoomSurvey(
        roomSlug: String,
        payload: RoomSurveyInputDto
    ): Result<WiFiRoomSurveyDto> {
        if (simulateNetworkError) return Result.failure(Exception(networkErrorMessage))

        submittedSurveys.add(roomSlug to payload)
        val surveySlug = "${roomSlug}-${Instant.now().toEpochMilli()}"
        val surveyDto = WiFiRoomSurveyDto(
            id = "srv-$surveySlug",
            survey_slug = surveySlug,
            room_slug = roomSlug,
            room_name = roomSlug.replaceFirstChar { it.uppercase() },
            label = payload.label ?: "Android Survey",
            trigger_mode = payload.trigger_mode,
            captured_at = payload.captured_at ?: Instant.now().toString(),
            connected_bssid = payload.connected_bssid,
            connected_ssid = payload.connected_ssid,
            link_speed_mbps = payload.link_speed_mbps,
            frequency_mhz = payload.frequency_mhz,
            best_5ghz_dbm = payload.readings?.filter { it.band == "5GHz" }?.maxOfOrNull { it.rssi_dbm },
            best_24ghz_dbm = payload.readings?.filter { it.band == "2.4GHz" }?.maxOfOrNull { it.rssi_dbm },
            wifi_health_grade = "GOOD",
            readings = payload.readings?.map { r ->
                BssidReadingDto(
                    bssid = r.bssid,
                    ssid = r.ssid,
                    band = r.band,
                    channel = r.channel,
                    center_channel = r.center_channel,
                    width_mhz = r.width_mhz,
                    rssi_dbm = r.rssi_dbm
                )
            } ?: emptyList()
        )

        val list = surveyStore.getOrPut(roomSlug) { mutableListOf() }
        list.add(0, surveyDto)
        return Result.success(surveyDto)
    }

    override suspend fun flushGhostGroups(zoneIps: List<String>?): Result<GhostFlushResultDto> {
        if (simulateNetworkError) return Result.failure(Exception(networkErrorMessage))
        return Result.success(
            GhostFlushResultDto(
                flushed_count = 0,
                flushed_zones = emptyList(),
                results = emptyList(),
                captured_at = Instant.now().toString()
            )
        )
    }

    override suspend fun pollNow(): Result<HouseholdSonosSnapshotDto> {
        if (simulateNetworkError) return Result.failure(Exception(networkErrorMessage))
        return Result.success(
            HouseholdSonosSnapshotDto(
                batch_id = "batch-live-${Instant.now().toEpochMilli()}",
                captured_at = Instant.now().toString(),
                consumer_id = "on-demand",
                designated_stp_root = "9000.542a1b63fe6e",
                is_root_healthy = true,
                total_players = 14,
                reachable_players = 14,
                ghost_group_count = 0,
                has_ghost_groups = false
            )
        )
    }

    override suspend fun pingSweep(): Result<PingSweepResultDto> {
        if (simulateNetworkError) return Result.failure(Exception(networkErrorMessage))
        return Result.success(
            PingSweepResultDto(
                swept_at = Instant.now().toString(),
                total_probed = 14,
                reachable_count = 14,
                max_rtt_ms = 4.2,
                avg_rtt_ms = 1.8,
                dpc_risk_zones = emptyList(),
                results = emptyList()
            )
        )
    }

    override suspend fun getDaemonStatus(): Result<DaemonStatusDto> {
        return Result.success(
            DaemonStatusDto(
                is_running = true,
                interval_sec = 60.0,
                retention_days = 365,
                total_cycles = 500
            )
        )
    }

    override suspend fun triggerDaemonCollect(): Result<Unit> {
        return Result.success(Unit)
    }

    override suspend fun toggleDaemon(enabled: Boolean): Result<DaemonStatusDto> {
        return Result.success(
            DaemonStatusDto(
                is_running = enabled,
                interval_sec = 60.0,
                retention_days = 365,
                total_cycles = 501
            )
        )
    }

    override suspend fun deepReset(zoneIps: List<String>?): Result<DeepResetResultDto> {
        return Result.success(
            DeepResetResultDto(
                total_targeted = zoneIps?.size ?: 12,
                success_count = zoneIps?.size ?: 12,
                reset_zones = zoneIps ?: listOf("Wohnzimmer_Bookshelf"),
                results = emptyList(),
                elapsed_ms = 150.0,
                captured_at = Instant.now().toString()
            )
        )
    }

    override fun streamLiveRf(roomSlug: String): Flow<LiveRfFrameDto> = flow {
        var tick = 0
        while (true) {
            emit(
                LiveRfFrameDto(
                    room_slug = roomSlug,
                    interval_sec = 2.0,
                    consumer_id = "ws-client",
                    captured_at = Instant.now().toString(),
                    samples = listOf(
                        LiveRfSampleDto(
                            rincon_uuid = "RINCON_001",
                            zone_name = roomSlug,
                            phy_error_rate = 1.2 + (tick % 5),
                            captured_at = Instant.now().toString()
                        )
                    )
                )
            )
            tick++
            delay(2000)
        }
    }
}
