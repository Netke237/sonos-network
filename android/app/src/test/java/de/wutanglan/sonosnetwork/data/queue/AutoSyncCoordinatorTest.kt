package de.wutanglan.sonosnetwork.data.queue

import de.wutanglan.sonosnetwork.data.connectivity.FakeConnectivityManager
import de.wutanglan.sonosnetwork.data.network.FakeSonosNetworkClient
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Test

class AutoSyncCoordinatorTest {

    @Test
    fun testDrainQueueSequentially() = runBlocking {
        val fakeQueue = FakeSurveyQueueManager()
        val fakeClient = FakeSonosNetworkClient()
        val fakeConn = FakeConnectivityManager()
        val coordinator = AutoSyncCoordinator(fakeQueue, fakeClient, fakeConn)

        fakeQueue.enqueueSurvey(
            PendingSurveyEntity(
                client_survey_id = "survey-uuid-1",
                room_slug = "nicolas",
                timestamp = "2026-10-13T06:00:00Z",
                label = "Survey 1",
                connected_bssid = "76:4c:bc:76:7c:41",
                connected_ssid = "WuTangLan-Family",
                link_speed_mbps = 1201,
                frequency_mhz = 5220,
                readings_json = """[{"bssid":"76:4c:bc:76:7c:41","band":"5GHz","channel":44,"rssi_dbm":-75}]"""
            )
        )

        fakeQueue.enqueueSurvey(
            PendingSurveyEntity(
                room_slug = "galerie",
                timestamp = "2026-10-13T06:05:00Z",
                label = "Survey 2",
                connected_bssid = "76:4c:bc:76:7c:41",
                connected_ssid = "WuTangLan-Family",
                link_speed_mbps = 1201,
                frequency_mhz = 5220,
                readings_json = """[]"""
            )
        )

        assertEquals(2, fakeQueue.getPendingSurveys().size)

        val result = coordinator.syncPendingSurveys()
        assertTrue(result.isSuccessful)
        assertEquals(2, result.syncedCount)
        assertEquals(0, result.remainingCount)
        assertEquals(0, fakeQueue.getPendingSurveys().size)

        assertEquals(2, fakeClient.submittedSurveys.size)
        val firstSub = fakeClient.submittedSurveys[0]
        assertEquals("nicolas", firstSub.first)
        assertEquals("survey-uuid-1", firstSub.second.client_survey_id)
        assertEquals("Survey 1", firstSub.second.label)
        assertEquals("2026-10-13T06:00:00Z", firstSub.second.captured_at)
        assertEquals("STORE_AND_FORWARD", firstSub.second.trigger_mode)
        assertEquals("WuTangLan-Family", firstSub.second.connected_ssid)
        assertEquals(5220, firstSub.second.frequency_mhz)
        assertEquals(1, firstSub.second.readings?.size)

        val secondSub = fakeClient.submittedSurveys[1]
        assertEquals("galerie", secondSub.first)
        assertEquals("2026-10-13T06:05:00Z", secondSub.second.captured_at)
    }

    @Test
    fun testNetworkErrorStopsQueueDrainPreservingRemaining() = runBlocking {
        val fakeQueue = FakeSurveyQueueManager()
        val fakeClient = FakeSonosNetworkClient()
        val fakeConn = FakeConnectivityManager()
        val coordinator = AutoSyncCoordinator(fakeQueue, fakeClient, fakeConn)

        fakeQueue.enqueueSurvey(
            PendingSurveyEntity(room_slug = "room-1", timestamp = "t1", label = "S1", readings_json = "[]")
        )
        fakeQueue.enqueueSurvey(
            PendingSurveyEntity(room_slug = "room-2", timestamp = "t2", label = "S2", readings_json = "[]")
        )

        fakeClient.simulateNetworkError = true

        val result = coordinator.syncPendingSurveys()
        assertFalse(result.isSuccessful)
        assertEquals(0, result.syncedCount)
        assertEquals(2, result.remainingCount)
        assertEquals(2, fakeQueue.getPendingSurveys().size)

        // Now network recovers
        fakeClient.simulateNetworkError = false
        val retryResult = coordinator.syncPendingSurveys()
        assertTrue(retryResult.isSuccessful)
        assertEquals(2, retryResult.syncedCount)
        assertEquals(0, retryResult.remainingCount)
        assertEquals(0, fakeQueue.getPendingSurveys().size)
    }
}
