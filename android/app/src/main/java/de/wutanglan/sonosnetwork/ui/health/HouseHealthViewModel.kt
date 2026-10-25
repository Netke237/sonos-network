package de.wutanglan.sonosnetwork.ui.health

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import de.wutanglan.sonosnetwork.data.models.HouseDiagnosticReportDto
import de.wutanglan.sonosnetwork.data.models.HouseOverviewDto
import de.wutanglan.sonosnetwork.data.models.RoomDiagnosticSummaryDto
import de.wutanglan.sonosnetwork.data.models.TopologyGraphDto
import de.wutanglan.sonosnetwork.data.network.SonosNetworkClientPort
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

enum class HouseViewMode {
    ACCORDION_CARDS,
    TOPOLOGY_CANVAS
}

data class HouseHealthUiState(
    val isLoading: Boolean = false,
    val overview: HouseOverviewDto? = null,
    val topology: TopologyGraphDto? = null,
    val houseDiagnostics: HouseDiagnosticReportDto? = null,
    val activeViewMode: HouseViewMode = HouseViewMode.ACCORDION_CARDS,
    val selectedRoomDiagnostic: RoomDiagnosticSummaryDto? = null,
    val isDiagnosticSheetOpen: Boolean = false,
    val isLoadingRoomDiagnostic: Boolean = false,
    val isRemediating: Boolean = false,
    val remediationMessage: String? = null,
    val errorMessage: String? = null
)

class HouseHealthViewModel(
    private val networkClient: SonosNetworkClientPort
) : ViewModel() {

    private val _uiState = MutableStateFlow(HouseHealthUiState())
    val uiState = _uiState.asStateFlow()

    init {
        loadHealthData()
    }

    fun loadHealthData() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, errorMessage = null)

            val overviewResult = networkClient.getOverview()
            val topologyResult = networkClient.getTopology("ALL")
            val diagResult = networkClient.getHouseDiagnostics()

            if (overviewResult.isSuccess) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    overview = overviewResult.getOrNull(),
                    topology = topologyResult.getOrNull(),
                    houseDiagnostics = diagResult.getOrNull()
                )
            } else {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    errorMessage = overviewResult.exceptionOrNull()?.message ?: "Failed to load house health"
                )
            }
        }
    }

    fun setViewMode(mode: HouseViewMode) {
        _uiState.value = _uiState.value.copy(activeViewMode = mode)
    }

    fun toggleViewMode() {
        val nextMode = if (_uiState.value.activeViewMode == HouseViewMode.ACCORDION_CARDS) {
            HouseViewMode.TOPOLOGY_CANVAS
        } else {
            HouseViewMode.ACCORDION_CARDS
        }
        _uiState.value = _uiState.value.copy(activeViewMode = nextMode)
    }

    fun openRoomDiagnostic(roomSlug: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(
                isLoadingRoomDiagnostic = true,
                isDiagnosticSheetOpen = true,
                selectedRoomDiagnostic = null
            )

            val result = networkClient.getRoomDiagnostics(roomSlug)
            if (result.isSuccess) {
                _uiState.value = _uiState.value.copy(
                    isLoadingRoomDiagnostic = false,
                    selectedRoomDiagnostic = result.getOrNull()
                )
            } else {
                _uiState.value = _uiState.value.copy(
                    isLoadingRoomDiagnostic = false,
                    errorMessage = result.exceptionOrNull()?.message ?: "Failed to load room diagnostics"
                )
            }
        }
    }

    fun closeDiagnosticSheet() {
        _uiState.value = _uiState.value.copy(
            isDiagnosticSheetOpen = false,
            remediationMessage = null
        )
    }

    fun flushGhostGroupsForIps(zoneIps: List<String>) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isRemediating = true, remediationMessage = null)
            val result = networkClient.flushGhostGroups(zoneIps)
            if (result.isSuccess) {
                val data = result.getOrNull()
                _uiState.value = _uiState.value.copy(
                    isRemediating = false,
                    remediationMessage = "✓ Ghost group flushed (${data?.flushed_zones?.size ?: 0} zones)"
                )
                loadHealthData()
                _uiState.value.selectedRoomDiagnostic?.let { currentRoom ->
                    val refreshRoom = networkClient.getRoomDiagnostics(currentRoom.room_slug)
                    if (refreshRoom.isSuccess) {
                        _uiState.value = _uiState.value.copy(selectedRoomDiagnostic = refreshRoom.getOrNull())
                    }
                }
            } else {
                _uiState.value = _uiState.value.copy(
                    isRemediating = false,
                    remediationMessage = "✗ Flush failed: ${result.exceptionOrNull()?.message}"
                )
            }
        }
    }

    fun deepResetForIps(zoneIps: List<String>) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isRemediating = true, remediationMessage = null)
            val result = networkClient.deepReset(zoneIps)
            if (result.isSuccess) {
                val data = result.getOrNull()
                val successCount = data?.results?.count { it.status == "RESET_SUCCESS" } ?: 0
                _uiState.value = _uiState.value.copy(
                    isRemediating = false,
                    remediationMessage = "✓ Deep reset complete: $successCount zone(s) unfrozen (${data?.elapsed_ms?.let { String.format("%.0f ms", it) } ?: "done"})"
                )
                loadHealthData()
                _uiState.value.selectedRoomDiagnostic?.let { currentRoom ->
                    val refreshRoom = networkClient.getRoomDiagnostics(currentRoom.room_slug)
                    if (refreshRoom.isSuccess) {
                        _uiState.value = _uiState.value.copy(selectedRoomDiagnostic = refreshRoom.getOrNull())
                    }
                }
            } else {
                _uiState.value = _uiState.value.copy(
                    isRemediating = false,
                    remediationMessage = "✗ Deep reset failed: ${result.exceptionOrNull()?.message}"
                )
            }
        }
    }

    fun clearRemediationMessage() {
        _uiState.value = _uiState.value.copy(remediationMessage = null)
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(errorMessage = null)
    }
}
