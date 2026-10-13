package de.wutanglan.sonosnetwork.ui.walkthrough

import de.wutanglan.sonosnetwork.data.connectivity.FakeConnectivityManager
import de.wutanglan.sonosnetwork.data.network.FakeSonosNetworkClient
import de.wutanglan.sonosnetwork.data.queue.AutoSyncCoordinator
import de.wutanglan.sonosnetwork.data.queue.FakeSurveyQueueManager
import de.wutanglan.sonosnetwork.data.wifi.FakeWifiScanner
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
class WalkthroughViewModelTest {

    private val testDispatcher = StandardTestDispatcher()
    private lateinit var fakeScanner: FakeWifiScanner
    private lateinit var fakeQueue: FakeSurveyQueueManager
    private lateinit var fakeClient: FakeSonosNetworkClient
    private lateinit var fakeConn: FakeConnectivityManager
    private lateinit var coordinator: AutoSyncCoordinator
    private lateinit var viewModel: WalkthroughViewModel

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        fakeScanner = FakeWifiScanner()
        fakeQueue = FakeSurveyQueueManager()
        fakeClient = FakeSonosNetworkClient()
        fakeConn = FakeConnectivityManager()
        coordinator = AutoSyncCoordinator(fakeQueue, fakeClient, fakeConn)
        viewModel = WalkthroughViewModel(
            fakeScanner,
            fakeQueue,
            fakeClient,
            fakeConn,
            coordinator
        )
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun testFloorAndRoomSelection() {
        assertEquals("obergeschoss", viewModel.uiState.value.selectedFloorSlug)

        viewModel.selectFloor("erdgeschoss")
        assertEquals("erdgeschoss", viewModel.uiState.value.selectedFloorSlug)
        assertEquals("wohnzimmer", viewModel.uiState.value.selectedRoomSlug)

        viewModel.selectRoom("kueche")
        assertEquals("kueche", viewModel.uiState.value.selectedRoomSlug)
    }

    @Test
    fun testScanRoomNowDirectSubmitWhenOnline() = runTest {
        viewModel.selectFloor("dachgeschoss")
        assertEquals("nicolas", viewModel.uiState.value.selectedRoomSlug)

        viewModel.scanRoomNow()
        advanceUntilIdle()

        assertNotNull(viewModel.uiState.value.lastScanResult)
        assertEquals(1, fakeClient.submittedSurveys.size)
        assertEquals("nicolas", fakeClient.submittedSurveys.first().first)
        assertEquals(0, fakeQueue.getPendingSurveys().size)
        assertTrue(viewModel.uiState.value.statusMessage!!.contains("synced"))
    }

    @Test
    fun testScanRoomNowStoreAndForwardWhenOffline() = runTest {
        fakeClient.simulateNetworkError = true
        viewModel.selectFloor("obergeschoss")
        viewModel.selectRoom("galerie")

        viewModel.scanRoomNow()
        advanceUntilIdle()

        assertEquals(0, fakeClient.submittedSurveys.size)
        assertEquals(1, fakeQueue.getPendingSurveys().size)
        val queued = fakeQueue.getPendingSurveys().first()
        assertEquals("galerie", queued.room_slug)
        assertEquals("STORE_AND_FORWARD", queued.trigger_mode)
        assertTrue(viewModel.uiState.value.statusMessage!!.contains("offline"))
    }

    @Test
    fun testScanRoomBlockedWhenRemoteVpnActive() = runTest {
        fakeConn.simulateVpnConnected(true)
        advanceUntilIdle()
        assertTrue(viewModel.uiState.value.isRemoteVpnActive)

        viewModel.scanRoomNow()
        advanceUntilIdle()

        assertNull(viewModel.uiState.value.lastScanResult)
        assertNotNull(viewModel.uiState.value.errorMessage)
        assertTrue(viewModel.uiState.value.errorMessage!!.contains("Remote VPN"))
    }

    @Test
    fun testSyncQueueNow() = runTest {
        viewModel.syncQueueNow()
        advanceUntilIdle()
        assertNotNull(viewModel.uiState.value.statusMessage)
    }
}
