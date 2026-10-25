package de.wutanglan.sonosnetwork.data.network

import de.wutanglan.sonosnetwork.data.models.*
import kotlinx.coroutines.flow.Flow

interface SonosNetworkClientPort {
    suspend fun getOverview(): Result<HouseOverviewDto>
    suspend fun getTopology(layer: String? = null): Result<TopologyGraphDto>
    suspend fun getHouseDiagnostics(): Result<HouseDiagnosticReportDto>
    suspend fun getRoomDiagnostics(roomSlug: String): Result<RoomDiagnosticSummaryDto>
    suspend fun getRoomSurveys(roomSlug: String): Result<List<WiFiRoomSurveyDto>>
    suspend fun submitRoomSurvey(roomSlug: String, payload: RoomSurveyInputDto): Result<WiFiRoomSurveyDto>
    suspend fun flushGhostGroups(zoneIps: List<String>? = null): Result<GhostFlushResultDto>
    suspend fun pollNow(): Result<HouseholdSonosSnapshotDto>
    suspend fun pingSweep(): Result<PingSweepResultDto>
    suspend fun getDaemonStatus(): Result<DaemonStatusDto>
    suspend fun triggerDaemonCollect(): Result<Unit>
    suspend fun toggleDaemon(enabled: Boolean): Result<DaemonStatusDto>
    suspend fun deepReset(zoneIps: List<String>? = null): Result<DeepResetResultDto>
    fun streamLiveRf(roomSlug: String): Flow<LiveRfFrameDto>
}
