package de.wutanglan.sonosnetwork.data.models

import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import org.junit.Assert.*
import org.junit.Test

class DtosSerializationTest {

    private val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        encodeDefaults = true
    }

    @Test
    fun testRoomSurveyInputDtoSerialization() {
        val payload = RoomSurveyInputDto(
            label = "Attic Walkthrough",
            trigger_mode = "STORE_AND_FORWARD",
            captured_at = "2026-10-13T06:00:00Z",
            connected_bssid = "76:4C:BC:76:7C:41",
            connected_ssid = "WuTangLan-Family",
            link_speed_mbps = 1201,
            frequency_mhz = 5220,
            notes = "Test scan",
            readings = listOf(
                BssidReadingInputDto(
                    bssid = "76:4C:BC:76:7C:41",
                    ssid = "WuTangLan-Family",
                    band = "5GHz",
                    channel = 44,
                    center_channel = 44,
                    width_mhz = 80,
                    rssi_dbm = -75
                )
            )
        )

        val jsonStr = json.encodeToString(payload)
        assertTrue(jsonStr.contains("\"captured_at\":\"2026-10-13T06:00:00Z\""))
        assertTrue(jsonStr.contains("\"connected_ssid\":\"WuTangLan-Family\""))
        assertTrue(jsonStr.contains("\"frequency_mhz\":5220"))
        assertTrue(jsonStr.contains("\"bssid\":\"76:4C:BC:76:7C:41\""))

        val decoded: RoomSurveyInputDto = json.decodeFromString(jsonStr)
        assertEquals("Attic Walkthrough", decoded.label)
        assertEquals("STORE_AND_FORWARD", decoded.trigger_mode)
        assertEquals(1, decoded.readings?.size)
        assertEquals(-75, decoded.readings?.first()?.rssi_dbm)
    }

    @Test
    fun testHouseOverviewDtoDeserialization() {
        val jsonStr = """
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

        val overview: HouseOverviewDto = json.decodeFromString(jsonStr)
        assertEquals(4, overview.total_floors)
        assertEquals(11, overview.total_rooms)
        assertEquals(14, overview.total_sonos_players)
        assertEquals("9000.542a1b63fe6e", overview.designated_stp_root)
        assertFalse(overview.has_ghost_groups)
    }

    @Test
    fun testHouseDiagnosticReportDtoDeserialization() {
        val jsonStr = """
            {
                "evaluated_at": "2026-10-13T06:15:00Z",
                "overall_health_grade": "GOOD",
                "designated_stp_root": "9000.542a1b63fe6e",
                "is_stp_root_healthy": true,
                "sonosnet_wireless_player_count": 11,
                "total_diagnostics_count": 0,
                "critical_diagnostics_count": 0,
                "marginal_diagnostics_count": 0,
                "house_diagnostics": [],
                "rooms": []
            }
        """.trimIndent()

        val report: HouseDiagnosticReportDto = json.decodeFromString(jsonStr)
        assertEquals("GOOD", report.overall_health_grade)
        assertTrue(report.is_stp_root_healthy)
        assertEquals(11, report.sonosnet_wireless_player_count)
    }

    @Test
    fun testLiveRfFrameDtoDeserializationFromBackendPayload() {
        val jsonStr = """
            {
                "timestamp": "2026-10-13T06:30:00Z",
                "consumer_id": "ws-12345678",
                "room_slug": "nicolas",
                "samples": [
                    {
                        "rincon_uuid": "RINCON_001",
                        "zone_name": "Nicolas",
                        "phy_error_rate": 0.0,
                        "captured_at": "2026-10-13T06:30:00Z"
                    }
                ]
            }
        """.trimIndent()

        val frame: LiveRfFrameDto = json.decodeFromString(jsonStr)
        assertEquals("nicolas", frame.room_slug)
        assertEquals("ws-12345678", frame.consumer_id)
        assertEquals("2026-10-13T06:30:00Z", frame.captured_at)
        assertEquals(2.0, frame.interval_sec, 0.001)
        assertEquals(1, frame.samples.size)
        assertEquals("RINCON_001", frame.samples.first().rincon_uuid)
    }

    @Test
    fun testRoomSurveyInputDtoPreservesClientSurveyId() {
        val payload = RoomSurveyInputDto(
            client_survey_id = "test-uuid-123",
            label = "Test Survey",
            trigger_mode = "MANUAL_SURVEY"
        )
        val jsonStr = json.encodeToString(payload)
        assertTrue(jsonStr.contains("\"client_survey_id\":\"test-uuid-123\""))

        val decoded: RoomSurveyInputDto = json.decodeFromString(jsonStr)
        assertEquals("test-uuid-123", decoded.client_survey_id)
    }
}
