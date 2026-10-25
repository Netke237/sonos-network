package de.wutanglan.sonosnetwork.ui.walkthrough

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import de.wutanglan.sonosnetwork.data.connectivity.ConnectivityPort
import de.wutanglan.sonosnetwork.data.models.BssidReadingInputDto
import de.wutanglan.sonosnetwork.data.models.RoomSurveyInputDto
import de.wutanglan.sonosnetwork.data.network.SonosNetworkClientPort
import de.wutanglan.sonosnetwork.data.queue.AutoSyncCoordinator
import de.wutanglan.sonosnetwork.data.queue.PendingSurveyEntity
import de.wutanglan.sonosnetwork.data.queue.SurveyQueuePort
import de.wutanglan.sonosnetwork.data.wifi.SingleShotScanResult
import de.wutanglan.sonosnetwork.data.wifi.WifiScannerPort
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.time.Instant

data class WalkthroughUiState(
    val selectedFloorSlug: String = "obergeschoss",
    val selectedRoomSlug: String = "galerie",
    val availableFloors: List<Pair<String, String>> = listOf(
        "keller" to "Keller",
        "erdgeschoss" to "Erdgeschoss",
        "obergeschoss" to "Obergeschoss",
        "dachgeschoss" to "Dachgeschoss"
    ),
    val availableRooms: List<Pair<String, String>> = listOf(
        "galerie" to "Galerie",
        "elternschlafzimmer" to "Elternschlafzimmer",
        "elternbad" to "Elternbad",
        "noemi" to "Noemi",
        "noah" to "Noah"
    ),
    val isScanning: Boolean = false,
    val isThrottled: Boolean = false,
    val throttleCooldownSec: Int = 0,
    val lastScanResult: SingleShotScanResult? = null,
    val isSyncingQueue: Boolean = false,
    val queuedSurveysCount: Int = 0,
    val isRemoteVpnActive: Boolean = false,
    val statusMessage: String? = null,
    val errorMessage: String? = null
)

class WalkthroughViewModel(
    private val wifiScanner: WifiScannerPort,
    private val surveyQueue: SurveyQueuePort,
    private val networkClient: SonosNetworkClientPort,
    private val connectivityPort: ConnectivityPort,
    private val autoSyncCoordinator: AutoSyncCoordinator,
    private val json: Json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        encodeDefaults = true
    }
) : ViewModel() {

    private val _uiState = MutableStateFlow(WalkthroughUiState())
    val uiState = _uiState.asStateFlow()

    private val floorRoomsMap = mapOf(
        "keller" to listOf("keller" to "Keller"),
        "erdgeschoss" to listOf(
            "wohnzimmer" to "Wohnzimmer",
            "fernsehecke" to "Fernsehecke",
            "kueche" to "Küche",
            "bueroecke" to "Büroecke"
        ),
        "obergeschoss" to listOf(
            "galerie" to "Galerie",
            "elternschlafzimmer" to "Elternschlafzimmer",
            "elternbad" to "Elternbad",
            "noemi" to "Noemi",
            "noah" to "Noah"
        ),
        "dachgeschoss" to listOf(
            "nicolas" to "Nicolas"
        )
    )

    init {
        // Observe connection state for VPN safe mode
        connectivityPort.observeConnectionState()
            .onEach { conn ->
                _uiState.value = _uiState.value.copy(
                    isRemoteVpnActive = conn.isRemoteVpnActive
                )
            }
            .launchIn(viewModelScope)

        // Observe offline survey queue pending count
        viewModelScope.launch {
            surveyQueue.getPendingCount()
                .collect { count ->
                    _uiState.value = _uiState.value.copy(queuedSurveysCount = count)
                }
        }

        // Auto-sync setup
        autoSyncCoordinator.startAutoSync(viewModelScope)
    }

    fun selectFloor(floorSlug: String) {
        val rooms = floorRoomsMap[floorSlug] ?: emptyList()
        val defaultRoom = rooms.firstOrNull()?.first ?: ""
        _uiState.value = _uiState.value.copy(
            selectedFloorSlug = floorSlug,
            availableRooms = rooms,
            selectedRoomSlug = defaultRoom
        )
    }

    fun selectRoom(roomSlug: String) {
        _uiState.value = _uiState.value.copy(selectedRoomSlug = roomSlug)
    }

    fun scanRoomNow() {
        if (_uiState.value.isRemoteVpnActive) {
            _uiState.value = _uiState.value.copy(
                errorMessage = "Physical Wi-Fi scanning is paused while connected via Firewalla Remote VPN."
            )
            return
        }

        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(
                isScanning = true,
                errorMessage = null,
                statusMessage = null
            )

            val scanResult = wifiScanner.probeSingleShotScan()

            if (scanResult.is_throttled) {
                _uiState.value = _uiState.value.copy(
                    isScanning = false,
                    isThrottled = true,
                    throttleCooldownSec = scanResult.throttle_cooldown_sec,
                    errorMessage = "Scan rate limit reached. Cooldown: ${scanResult.throttle_cooldown_sec}s remaining."
                )
                return@launch
            }

            if (!scanResult.is_fresh) {
                _uiState.value = _uiState.value.copy(
                    isScanning = false,
                    isThrottled = false,
                    errorMessage = "Wi-Fi scan failed or permissions missing. Please verify Location toggle and permissions are enabled."
                )
                return@launch
            }

            _uiState.value = _uiState.value.copy(
                isScanning = false,
                isThrottled = false,
                throttleCooldownSec = 0,
                lastScanResult = scanResult
            )

            // Submit or enqueue
            val currentRoom = _uiState.value.selectedRoomSlug
            val capturedAt = Instant.now().toString()
            val readingsDto = scanResult.readings.map { r ->
                BssidReadingInputDto(
                    bssid = r.bssid,
                    ssid = r.ssid,
                    band = r.band,
                    channel = r.channel,
                    center_channel = r.center_channel,
                    width_mhz = r.width_mhz,
                    rssi_dbm = r.rssi_dbm
                )
            }

            val clientSurveyId = java.util.UUID.randomUUID().toString()
            val payload = RoomSurveyInputDto(
                label = "Android Walkthrough",
                trigger_mode = "MANUAL_SURVEY",
                captured_at = capturedAt,
                client_survey_id = clientSurveyId,
                connected_bssid = scanResult.connected_bssid,
                connected_ssid = scanResult.connected_ssid,
                link_speed_mbps = scanResult.link_speed_mbps,
                frequency_mhz = scanResult.frequency_mhz,
                readings = readingsDto
            )

            // Try direct submit
            val submitResult = networkClient.submitRoomSurvey(currentRoom, payload)
            if (submitResult.isSuccess) {
                _uiState.value = _uiState.value.copy(
                    statusMessage = "Survey recorded and synced to backend successfully."
                )
            } else {
                // Network failed -> Store and forward in local queue
                val readingsJson = json.encodeToString(readingsDto)
                val entity = PendingSurveyEntity(
                    client_survey_id = clientSurveyId,
                    room_slug = currentRoom,
                    timestamp = capturedAt,
                    label = "Android Walkthrough (Offline)",
                    trigger_mode = "STORE_AND_FORWARD",
                    connected_bssid = scanResult.connected_bssid,
                    connected_ssid = scanResult.connected_ssid,
                    link_speed_mbps = scanResult.link_speed_mbps,
                    frequency_mhz = scanResult.frequency_mhz,
                    readings_json = readingsJson,
                    sync_status = "PENDING"
                )
                surveyQueue.enqueueSurvey(entity)
                _uiState.value = _uiState.value.copy(
                    statusMessage = "Network unavailable. Survey saved offline in store-and-forward queue."
                )
            }
        }
    }

    fun syncQueueNow() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isSyncingQueue = true, errorMessage = null)
            val result = autoSyncCoordinator.syncPendingSurveys()
            _uiState.value = _uiState.value.copy(
                isSyncingQueue = false,
                statusMessage = if (result.isSuccessful) {
                    "Queue synced successfully (${result.syncedCount} surveys submitted)."
                } else {
                    "Sync failed: ${result.error}. ${result.remainingCount} surveys remain queued."
                }
            )
        }
    }

    fun clearMessages() {
        _uiState.value = _uiState.value.copy(statusMessage = null, errorMessage = null)
    }
}
