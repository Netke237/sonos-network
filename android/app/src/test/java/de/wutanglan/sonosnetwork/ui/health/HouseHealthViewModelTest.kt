package de.wutanglan.sonosnetwork.ui.health

import de.wutanglan.sonosnetwork.data.network.FakeSonosNetworkClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class HouseHealthViewModelTest {

    private val testDispatcher = StandardTestDispatcher()
    private lateinit var fakeClient: FakeSonosNetworkClient
    private lateinit var viewModel: HouseHealthViewModel

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        fakeClient = FakeSonosNetworkClient()
        viewModel = HouseHealthViewModel(fakeClient)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun testInitialLoadHealthData() = runTest {
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertFalse(state.isLoading)
        assertNotNull(state.overview)
        assertEquals(4, state.overview!!.total_floors)
        assertEquals(14, state.overview!!.total_sonos_players)
        assertNotNull(state.topology)
        assertNotNull(state.houseDiagnostics)
    }

    @Test
    fun testToggleViewMode() {
        assertEquals(HouseViewMode.ACCORDION_CARDS, viewModel.uiState.value.activeViewMode)

        viewModel.toggleViewMode()
        assertEquals(HouseViewMode.TOPOLOGY_CANVAS, viewModel.uiState.value.activeViewMode)

        viewModel.toggleViewMode()
        assertEquals(HouseViewMode.ACCORDION_CARDS, viewModel.uiState.value.activeViewMode)
    }

    @Test
    fun testOpenAndCloseRoomDiagnostic() = runTest {
        advanceUntilIdle()
        assertFalse(viewModel.uiState.value.isDiagnosticSheetOpen)

        viewModel.openRoomDiagnostic("galerie")
        advanceUntilIdle()

        assertTrue(viewModel.uiState.value.isDiagnosticSheetOpen)
        assertNotNull(viewModel.uiState.value.selectedRoomDiagnostic)
        assertEquals("galerie", viewModel.uiState.value.selectedRoomDiagnostic!!.room_slug)

        viewModel.closeDiagnosticSheet()
        assertFalse(viewModel.uiState.value.isDiagnosticSheetOpen)
    }
}
