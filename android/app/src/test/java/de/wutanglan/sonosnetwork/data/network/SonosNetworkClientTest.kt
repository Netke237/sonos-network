package de.wutanglan.sonosnetwork.data.network

import de.wutanglan.sonosnetwork.data.connectivity.ConnectionState
import de.wutanglan.sonosnetwork.data.connectivity.FakeConnectivityManager
import de.wutanglan.sonosnetwork.data.models.BssidReadingInputDto
import de.wutanglan.sonosnetwork.data.models.RoomSurveyInputDto
import kotlinx.coroutines.runBlocking
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

class SonosNetworkClientTest {

    private lateinit var mockWebServer: MockWebServer
    private lateinit var connectivityManager: FakeConnectivityManager
    private lateinit var client: RealSonosNetworkClient

    @Before
    fun setUp() {
        mockWebServer = MockWebServer()
        mockWebServer.start()

        val mockUrl = mockWebServer.url("/").toString().trimEnd('/')
        connectivityManager = FakeConnectivityManager(
            ConnectionState(
                activeEndpointUrl = mockUrl
            )
        )
        client = RealSonosNetworkClient(connectivityManager)
    }

    @After
    fun tearDown() {
        mockWebServer.shutdown()
    }

    @Test
    fun testGetOverviewSuccessful() = runBlocking {
        val mockJson = """
            {
                "total_floors": 4,
                "total_rooms": 11,
                "total_sonos_players": 14,
                "total_wifi_aps": 2,
                "total_switch_ports": 16,
                "designated_stp_root": "9000.542a1b63fe6e",
                "ghost_group_count": 0,
                "has_ghost_groups": false,
                "active_diagnostics_count": 0,
                "critical_diagnostics_count": 0,
                "floors": []
            }
        """.trimIndent()

        mockWebServer.enqueue(MockResponse().setResponseCode(200).setBody(mockJson))

        val result = client.getOverview()
        assertTrue(result.isSuccess)
        val overview = result.getOrThrow()
        assertEquals(4, overview.total_floors)
        assertEquals(14, overview.total_sonos_players)

        val recorded = mockWebServer.takeRequest()
        assertEquals("GET", recorded.method)
        assertEquals("/api/overview", recorded.path)
    }

    @Test
    fun testGetTopologyWithLayerFilter() = runBlocking {
        val mockJson = """
            {
                "layer_filter": "SONOS_MESH",
                "designated_stp_root": "9000.542a1b63fe6e",
                "total_nodes": 0,
                "total_edges": 0,
                "nodes": [],
                "edges": []
            }
        """.trimIndent()

        mockWebServer.enqueue(MockResponse().setResponseCode(200).setBody(mockJson))

        val result = client.getTopology("SONOS_MESH")
        assertTrue(result.isSuccess)
        val topology = result.getOrThrow()
        assertEquals("SONOS_MESH", topology.layer_filter)

        val recorded = mockWebServer.takeRequest()
        assertEquals("GET", recorded.method)
        assertEquals("/api/topology?layer=SONOS_MESH", recorded.path)
    }

    @Test
    fun testSubmitRoomSurveySendsPayload() = runBlocking {
        val mockResponseJson = """
            {
                "survey_slug": "nicolas-12345",
                "room_slug": "nicolas",
                "room_name": "Nicolas",
                "label": "Attic Test",
                "trigger_mode": "STORE_AND_FORWARD",
                "captured_at": "2026-10-13T06:00:00Z",
                "wifi_health_grade": "GOOD",
                "readings": []
            }
        """.trimIndent()

        mockWebServer.enqueue(MockResponse().setResponseCode(200).setBody(mockResponseJson))

        val payload = RoomSurveyInputDto(
            label = "Attic Test",
            trigger_mode = "STORE_AND_FORWARD",
            captured_at = "2026-10-13T06:00:00Z",
            connected_bssid = "76:4C:BC:76:7C:41",
            connected_ssid = "WuTangLan-Family",
            link_speed_mbps = 1201,
            frequency_mhz = 5220,
            readings = listOf(
                BssidReadingInputDto(
                    bssid = "76:4C:BC:76:7C:41",
                    ssid = "WuTangLan-Family",
                    band = "5GHz",
                    channel = 44,
                    rssi_dbm = -75
                )
            )
        )

        val result = client.submitRoomSurvey("nicolas", payload)
        assertTrue(result.isSuccess)
        val survey = result.getOrThrow()
        assertEquals("nicolas", survey.room_slug)
        assertEquals("STORE_AND_FORWARD", survey.trigger_mode)

        val recorded = mockWebServer.takeRequest()
        assertEquals("POST", recorded.method)
        assertEquals("/api/rooms/nicolas/surveys", recorded.path)
        val bodyStr = recorded.body.readUtf8()
        assertTrue(bodyStr.contains("\"captured_at\":\"2026-10-13T06:00:00Z\""))
        assertTrue(bodyStr.contains("\"connected_ssid\":\"WuTangLan-Family\""))
    }

    @Test
    fun testFlushGhostGroups() = runBlocking {
        val mockResponseJson = """
            {
                "flushed_count": 1,
                "flushed_zones": ["Galerie"],
                "results": [],
                "captured_at": "2026-10-13T06:00:00Z"
            }
        """.trimIndent()

        mockWebServer.enqueue(MockResponse().setResponseCode(200).setBody(mockResponseJson))

        val result = client.flushGhostGroups(listOf("192.168.10.162"))
        assertTrue(result.isSuccess)
        assertEquals(1, result.getOrThrow().flushed_count)

        val recorded = mockWebServer.takeRequest()
        assertEquals("POST", recorded.method)
        assertEquals("/api/actions/flush-ghost-groups", recorded.path)
        val bodyStr = recorded.body.readUtf8()
        assertTrue(bodyStr.contains("192.168.10.162"))
    }

    @Test
    fun testHttpErrorReturnsFailure() = runBlocking {
        mockWebServer.enqueue(MockResponse().setResponseCode(500).setBody("Internal Server Error"))

        val result = client.getOverview()
        assertTrue(result.isFailure)
        assertTrue(result.exceptionOrNull()?.message?.contains("500") == true)
    }

    @Test
    fun testFakeSonosNetworkClientDirectly() = runBlocking {
        val fake = FakeSonosNetworkClient()
        val overview = fake.getOverview().getOrThrow()
        assertEquals(4, overview.total_floors)
        assertEquals(14, overview.total_sonos_players)

        val surveyResult = fake.submitRoomSurvey(
            "galerie",
            RoomSurveyInputDto(
                label = "Manual Survey",
                captured_at = "2026-10-13T06:10:00Z"
            )
        ).getOrThrow()

        assertEquals("galerie", surveyResult.room_slug)
        assertEquals(1, fake.submittedSurveys.size)
    }
}
