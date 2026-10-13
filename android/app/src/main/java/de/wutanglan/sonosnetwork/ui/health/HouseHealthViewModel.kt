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
        _uiState.value = _uiState.value.copy(isDiagnosticSheetOpen = false)
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(errorMessage = null)
    }
}
