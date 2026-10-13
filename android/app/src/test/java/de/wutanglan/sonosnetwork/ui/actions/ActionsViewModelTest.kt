package de.wutanglan.sonosnetwork.ui.actions

import de.wutanglan.sonosnetwork.data.models.LiveRfFrameDto
import de.wutanglan.sonosnetwork.data.models.LiveRfSampleDto
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
class ActionsViewModelTest {

    private val testDispatcher = StandardTestDispatcher()
    private lateinit var fakeClient: FakeSonosNetworkClient
    private lateinit var viewModel: ActionsViewModel

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        fakeClient = FakeSonosNetworkClient()
        viewModel = ActionsViewModel(fakeClient)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun testFlushGhostGroupsSuccess() = runTest {
        assertFalse(viewModel.uiState.value.ghostFlushDialogVisible)

        viewModel.flushGhostGroups()
        advanceUntilIdle()

        assertTrue(viewModel.uiState.value.ghostFlushDialogVisible)
        assertNotNull(viewModel.uiState.value.ghostFlushResult)
        assertFalse(viewModel.uiState.value.isFlushingGhostGroups)

        viewModel.dismissGhostFlushDialog()
        assertFalse(viewModel.uiState.value.ghostFlushDialogVisible)
    }

    @Test
    fun testPollNowSuccess() = runTest {
        assertNull(viewModel.uiState.value.pollSuccessMessage)

        viewModel.pollNow()
        advanceUntilIdle()

        assertNotNull(viewModel.uiState.value.pollSuccessMessage)
        assertTrue(viewModel.uiState.value.pollSuccessMessage!!.contains("14/14"))
        assertFalse(viewModel.uiState.value.isPollingNow)
    }

    @Test
    fun testPingSweepSuccess() = runTest {
        assertNull(viewModel.uiState.value.pingSweepResult)

        viewModel.runPingSweep()
        advanceUntilIdle()

        assertNotNull(viewModel.uiState.value.pingSweepResult)
        assertEquals(14, viewModel.uiState.value.pingSweepResult!!.total_probed)
        assertEquals(4.2, viewModel.uiState.value.pingSweepResult!!.max_rtt_ms, 0.01)
        assertFalse(viewModel.uiState.value.isRunningPingSweep)
    }

    @Test
    fun testOscilloscopeFrameReceivedUpdatesWaveform() {
        val frame = LiveRfFrameDto(
            room_slug = "wohnzimmer",
            interval_sec = 2.0,
            consumer_id = "test",
            captured_at = "2026-10-13T06:30:00Z",
            samples = listOf(
                LiveRfSampleDto(
                    rincon_uuid = "RINCON_001",
                    zone_name = "Wohnzimmer_Bookshelf",
                    phy_error_rate = 14.5,
                    ofdm_ani_level = 2,
                    captured_at = "2026-10-13T06:30:00Z"
                )
            )
        )

        viewModel.onOscilloscopeFrameReceived(frame)

        val state = viewModel.uiState.value
        assertEquals(1, state.livePhyHistory.size)
        assertEquals(14.5, state.livePhyHistory.first(), 0.01)
        assertEquals(1, state.liveAniHistory.size)
        assertEquals(2, state.liveAniHistory.first())
        assertEquals(14.5, state.latestPhyErrPerSec ?: 0.0, 0.01)
        assertEquals(2, state.latestAniLevel)
    }

    @Test
    fun testActionFailureSetsErrorMessage() = runTest {
        fakeClient.simulateNetworkError = true
        fakeClient.networkErrorMessage = "Host unreachable"

        viewModel.pollNow()
        advanceUntilIdle()

        assertNull(viewModel.uiState.value.pollSuccessMessage)
        assertNotNull(viewModel.uiState.value.errorMessage)
        assertTrue(viewModel.uiState.value.errorMessage!!.contains("Host unreachable"))
    }
}
