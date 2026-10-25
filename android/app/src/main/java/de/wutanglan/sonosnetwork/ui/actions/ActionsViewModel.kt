package de.wutanglan.sonosnetwork.ui.actions

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import de.wutanglan.sonosnetwork.data.models.*
import de.wutanglan.sonosnetwork.data.network.SonosNetworkClientPort
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.launch

data class ActionsUiState(
    val isFlushingGhostGroups: Boolean = false,
    val ghostFlushResult: GhostFlushResultDto? = null,
    val ghostFlushDialogVisible: Boolean = false,
    val isPollingNow: Boolean = false,
    val pollSuccessMessage: String? = null,
    val isRunningPingSweep: Boolean = false,
    val pingSweepResult: PingSweepResultDto? = null,
    val daemonStatus: DaemonStatusDto? = null,
    val isLoadingDaemon: Boolean = false,
    val isTriggeringDaemon: Boolean = false,
    val isDeepResetting: Boolean = false,
    val deepResetResult: DeepResetResultDto? = null,
    val deepResetDialogVisible: Boolean = false,
    val selectedOscilloscopeRoom: String = "wohnzimmer",
    val isStreamingOscilloscope: Boolean = false,
    val livePhyHistory: List<Double> = emptyList(),
    val liveAniHistory: List<Int> = emptyList(),
    val latestPhyErrPerSec: Double? = null,
    val latestAniLevel: Int? = null,
    val lastOscilloscopeTimestamp: String? = null,
    val errorMessage: String? = null
)

class ActionsViewModel(
    private val networkClient: SonosNetworkClientPort
) : ViewModel() {

    private val _uiState = MutableStateFlow(ActionsUiState())
    val uiState = _uiState.asStateFlow()

    private var oscilloscopeJob: Job? = null

    init {
        loadDaemonStatus()
    }

    fun flushGhostGroups(zoneIps: List<String>? = null) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isFlushingGhostGroups = true, errorMessage = null)
            val result = networkClient.flushGhostGroups(zoneIps)
            if (result.isSuccess) {
                val data = result.getOrThrow()
                _uiState.value = _uiState.value.copy(
                    isFlushingGhostGroups = false,
                    ghostFlushResult = data,
                    ghostFlushDialogVisible = true
                )
            } else {
                _uiState.value = _uiState.value.copy(
                    isFlushingGhostGroups = false,
                    errorMessage = formatError("Ghost group flush", result.exceptionOrNull())
                )
            }
        }
    }

    fun dismissGhostFlushDialog() {
        _uiState.value = _uiState.value.copy(ghostFlushDialogVisible = false)
    }

    fun pollNow() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isPollingNow = true, errorMessage = null, pollSuccessMessage = null)
            val result = networkClient.pollNow()
            if (result.isSuccess) {
                val data = result.getOrThrow()
                _uiState.value = _uiState.value.copy(
                    isPollingNow = false,
                    pollSuccessMessage = "Live Sonos poll completed. Polled ${data.reachable_players}/${data.total_players} players."
                )
            } else {
                _uiState.value = _uiState.value.copy(
                    isPollingNow = false,
                    errorMessage = formatError("Sonos poll", result.exceptionOrNull())
                )
            }
        }
    }

    fun runPingSweep() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isRunningPingSweep = true, errorMessage = null)
            val result = networkClient.pingSweep()
            if (result.isSuccess) {
                val data = result.getOrThrow()
                _uiState.value = _uiState.value.copy(
                    isRunningPingSweep = false,
                    pingSweepResult = data
                )
            } else {
                _uiState.value = _uiState.value.copy(
                    isRunningPingSweep = false,
                    errorMessage = formatError("Ping sweep", result.exceptionOrNull())
                )
            }
        }
    }

    private fun formatError(prefix: String, err: Throwable?): String {
        val msg = err?.message ?: ""
        return when {
            msg.contains("timeout", ignoreCase = true) ->
                "$prefix timed out while querying players across the house. Please check network connectivity and try again."
            msg.isNotBlank() ->
                "$prefix: $msg"
            else ->
                "$prefix failed"
        }
    }

    fun selectOscilloscopeRoom(roomSlug: String) {
        val current = _uiState.value
        if (current.selectedOscilloscopeRoom != roomSlug) {
            _uiState.value = current.copy(
                selectedOscilloscopeRoom = roomSlug,
                livePhyHistory = emptyList(),
                liveAniHistory = emptyList(),
                latestPhyErrPerSec = null,
                latestAniLevel = null
            )
            if (current.isStreamingOscilloscope) {
                startOscilloscopeStream()
            }
        }
    }

    fun toggleOscilloscopeStream() {
        if (_uiState.value.isStreamingOscilloscope) {
            stopOscilloscopeStream()
        } else {
            startOscilloscopeStream()
        }
    }

    fun startOscilloscopeStream() {
        stopOscilloscopeStream()
        val roomSlug = _uiState.value.selectedOscilloscopeRoom
        _uiState.value = _uiState.value.copy(isStreamingOscilloscope = true)

        oscilloscopeJob = networkClient.streamLiveRf(roomSlug)
            .onEach { frame ->
                onOscilloscopeFrameReceived(frame)
            }
            .catch { t ->
                _uiState.value = _uiState.value.copy(
                    isStreamingOscilloscope = false,
                    errorMessage = t.message ?: "Oscilloscope stream failed"
                )
            }
            .launchIn(viewModelScope)
    }

    fun stopOscilloscopeStream() {
        oscilloscopeJob?.cancel()
        oscilloscopeJob = null
        _uiState.value = _uiState.value.copy(isStreamingOscilloscope = false)
    }

    fun onOscilloscopeFrameReceived(frame: LiveRfFrameDto) {
        val sample = frame.samples.firstOrNull() ?: return
        val current = _uiState.value

        val newPhyHistory = (current.livePhyHistory + sample.phy_error_rate).takeLast(30)
        val newAniHistory = if (sample.ofdm_ani_level != null) {
            (current.liveAniHistory + sample.ofdm_ani_level).takeLast(30)
        } else {
            current.liveAniHistory
        }

        _uiState.value = current.copy(
            livePhyHistory = newPhyHistory,
            liveAniHistory = newAniHistory,
            latestPhyErrPerSec = sample.phy_error_rate,
            latestAniLevel = sample.ofdm_ani_level,
            lastOscilloscopeTimestamp = sample.captured_at
        )
    }

    fun loadDaemonStatus() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoadingDaemon = true)
            val result = networkClient.getDaemonStatus()
            if (result.isSuccess) {
                _uiState.value = _uiState.value.copy(
                    isLoadingDaemon = false,
                    daemonStatus = result.getOrThrow()
                )
            } else {
                _uiState.value = _uiState.value.copy(isLoadingDaemon = false)
            }
        }
    }

    fun triggerDaemonCollect() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isTriggeringDaemon = true, errorMessage = null)
            val result = networkClient.triggerDaemonCollect()
            if (result.isSuccess) {
                loadDaemonStatus()
                _uiState.value = _uiState.value.copy(
                    isTriggeringDaemon = false,
                    pollSuccessMessage = "✓ 24/7 Daemon collection cycle completed."
                )
            } else {
                _uiState.value = _uiState.value.copy(
                    isTriggeringDaemon = false,
                    errorMessage = formatError("Daemon collect", result.exceptionOrNull())
                )
            }
        }
    }

    fun toggleDaemon() {
        viewModelScope.launch {
            val current = _uiState.value.daemonStatus?.is_running ?: true
            val target = !current
            val result = networkClient.toggleDaemon(target)
            if (result.isSuccess) {
                _uiState.value = _uiState.value.copy(daemonStatus = result.getOrThrow())
            } else {
                _uiState.value = _uiState.value.copy(
                    errorMessage = formatError("Toggle daemon", result.exceptionOrNull())
                )
            }
        }
    }

    fun executeDeepReset(zoneIps: List<String>? = null) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isDeepResetting = true, errorMessage = null)
            val result = networkClient.deepReset(zoneIps)
            if (result.isSuccess) {
                val data = result.getOrThrow()
                _uiState.value = _uiState.value.copy(
                    isDeepResetting = false,
                    deepResetResult = data,
                    deepResetDialogVisible = true
                )
            } else {
                _uiState.value = _uiState.value.copy(
                    isDeepResetting = false,
                    errorMessage = formatError("Hardcore Deep Reset", result.exceptionOrNull())
                )
            }
        }
    }

    fun dismissDeepResetDialog() {
        _uiState.value = _uiState.value.copy(deepResetDialogVisible = false)
    }

    fun clearMessages() {
        _uiState.value = _uiState.value.copy(pollSuccessMessage = null, errorMessage = null)
    }

    override fun onCleared() {
        super.onCleared()
        stopOscilloscopeStream()
    }
}
