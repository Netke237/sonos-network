package de.wutanglan.sonosnetwork.ui.actions

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import de.wutanglan.sonosnetwork.data.models.GhostFlushResultDto
import de.wutanglan.sonosnetwork.data.models.LiveRfFrameDto
import de.wutanglan.sonosnetwork.data.models.PingSweepResultDto
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
                    errorMessage = result.exceptionOrNull()?.message ?: "Failed to flush ghost groups"
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
                    errorMessage = result.exceptionOrNull()?.message ?: "Poll request failed"
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
                    errorMessage = result.exceptionOrNull()?.message ?: "Ping sweep failed"
                )
            }
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

    fun clearMessages() {
        _uiState.value = _uiState.value.copy(pollSuccessMessage = null, errorMessage = null)
    }

    override fun onCleared() {
        super.onCleared()
        stopOscilloscopeStream()
    }
}
