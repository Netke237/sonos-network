package de.wutanglan.sonosnetwork.data.queue

import de.wutanglan.sonosnetwork.data.connectivity.ConnectivityPort
import de.wutanglan.sonosnetwork.data.models.BssidReadingInputDto
import de.wutanglan.sonosnetwork.data.models.RoomSurveyInputDto
import de.wutanglan.sonosnetwork.data.network.SonosNetworkClientPort
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach
import kotlinx.serialization.json.Json

data class SyncResult(
    val syncedCount: Int,
    val failedCount: Int,
    val remainingCount: Int,
    val isSuccessful: Boolean,
    val error: String? = null
)

class AutoSyncCoordinator(
    private val surveyQueue: SurveyQueuePort,
    private val networkClient: SonosNetworkClientPort,
    private val connectivityPort: ConnectivityPort,
    private val json: Json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        encodeDefaults = true
    }
) {

    suspend fun syncPendingSurveys(): SyncResult {
        val pending = surveyQueue.getPendingSurveys()
        if (pending.isEmpty()) {
            return SyncResult(
                syncedCount = 0,
                failedCount = 0,
                remainingCount = 0,
                isSuccessful = true
            )
        }

        var synced = 0
        var lastError: String? = null

        for (survey in pending) {
            val readings: List<BssidReadingInputDto> = try {
                if (survey.readings_json.isNotBlank()) {
                    json.decodeFromString(survey.readings_json)
                } else {
                    emptyList()
                }
            } catch (e: Exception) {
                emptyList()
            }

            val payload = RoomSurveyInputDto(
                label = survey.label,
                trigger_mode = survey.trigger_mode,
                captured_at = survey.timestamp,
                connected_bssid = survey.connected_bssid,
                connected_ssid = survey.connected_ssid,
                link_speed_mbps = survey.link_speed_mbps,
                frequency_mhz = survey.frequency_mhz,
                readings = readings
            )

            val result = networkClient.submitRoomSurvey(survey.room_slug, payload)
            if (result.isSuccess) {
                surveyQueue.markSurveySynced(survey.id)
                synced++
            } else {
                lastError = result.exceptionOrNull()?.message ?: "Submission failed"
                val remaining = pending.size - synced
                return SyncResult(
                    syncedCount = synced,
                    failedCount = 1,
                    remainingCount = remaining,
                    isSuccessful = false,
                    error = lastError
                )
            }
        }

        surveyQueue.purgeSyncedSurveys()

        return SyncResult(
            syncedCount = synced,
            failedCount = 0,
            remainingCount = 0,
            isSuccessful = true
        )
    }

    fun startAutoSync(coroutineScope: CoroutineScope) {
        connectivityPort.observeConnectionState()
            .onEach { state ->
                if (state.isConnected) {
                    try {
                        syncPendingSurveys()
                    } catch (_: Exception) {
                    }
                }
            }
            .launchIn(coroutineScope)
    }
}
