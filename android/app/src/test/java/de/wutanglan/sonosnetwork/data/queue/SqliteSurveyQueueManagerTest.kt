package de.wutanglan.sonosnetwork.data.queue

import androidx.test.core.app.ApplicationProvider
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34])
class SqliteSurveyQueueManagerTest {

    private lateinit var queueManager: SqliteSurveyQueueManager

    @Before
    fun setUp() {
        val context = ApplicationProvider.getApplicationContext<android.content.Context>()
        queueManager = SqliteSurveyQueueManager(context, "test_survey_cache_${System.currentTimeMillis()}.db")
    }

    @After
    fun tearDown() {
        queueManager.close()
    }

    @Test
    fun testEnqueueAndRetrievePendingSurveys() = runBlocking {
        assertEquals(0, queueManager.getPendingCount().first())

        val survey = PendingSurveyEntity(
            client_survey_id = "test-client-survey-uuid-1",
            room_slug = "nicolas",
            timestamp = "2026-10-13T06:20:00Z",
            label = "Attic Walkthrough",
            trigger_mode = "STORE_AND_FORWARD",
            connected_bssid = "76:4c:bc:76:7c:41",
            connected_ssid = "WuTangLan-Family",
            link_speed_mbps = 1201,
            frequency_mhz = 5220,
            readings_json = """[{"bssid":"76:4c:bc:76:7c:41","band":"5GHz","channel":44,"rssi_dbm":-75}]"""
        )

        val id = queueManager.enqueueSurvey(survey)
        assertTrue(id > 0)
        assertEquals(1, queueManager.getPendingCount().first())

        val pending = queueManager.getPendingSurveys()
        assertEquals(1, pending.size)
        val item = pending.first()
        assertEquals("test-client-survey-uuid-1", item.client_survey_id)
        assertEquals("nicolas", item.room_slug)
        assertEquals("2026-10-13T06:20:00Z", item.timestamp)
        assertEquals("Attic Walkthrough", item.label)
        assertEquals("STORE_AND_FORWARD", item.trigger_mode)
        assertEquals("76:4c:bc:76:7c:41", item.connected_bssid)
        assertEquals("WuTangLan-Family", item.connected_ssid)
        assertEquals(1201, item.link_speed_mbps)
        assertEquals(5220, item.frequency_mhz)
        assertTrue(item.readings_json.contains("-75"))
    }

    @Test
    fun testMarkSurveySyncedAndPurge() = runBlocking {
        val s1 = PendingSurveyEntity(
            room_slug = "noemi",
            timestamp = "2026-10-13T06:21:00Z",
            label = "Noemi Walkthrough",
            readings_json = "[]"
        )
        val s2 = PendingSurveyEntity(
            room_slug = "noah",
            timestamp = "2026-10-13T06:22:00Z",
            label = "Noah Walkthrough",
            readings_json = "[]"
        )

        val id1 = queueManager.enqueueSurvey(s1)
        val id2 = queueManager.enqueueSurvey(s2)
        assertEquals(2, queueManager.getPendingCount().first())

        // Mark s1 as synced
        queueManager.markSurveySynced(id1)
        assertEquals(1, queueManager.getPendingCount().first())

        val pending = queueManager.getPendingSurveys()
        assertEquals(1, pending.size)
        assertEquals(id2, pending.first().id)
        assertEquals("noah", pending.first().room_slug)

        // Purge synced
        queueManager.purgeSyncedSurveys()
        assertEquals(1, queueManager.getPendingCount().first())
    }

    @Test
    fun testSequentialOrdering() = runBlocking {
        val idA = queueManager.enqueueSurvey(PendingSurveyEntity(room_slug = "room-a", timestamp = "1", label = "A", readings_json = "[]"))
        val idB = queueManager.enqueueSurvey(PendingSurveyEntity(room_slug = "room-b", timestamp = "2", label = "B", readings_json = "[]"))

        val pending = queueManager.getPendingSurveys()
        assertEquals(2, pending.size)
        assertEquals(idA, pending[0].id)
        assertEquals("room-a", pending[0].room_slug)
        assertEquals(idB, pending[1].id)
        assertEquals("room-b", pending[1].room_slug)
    }
}
