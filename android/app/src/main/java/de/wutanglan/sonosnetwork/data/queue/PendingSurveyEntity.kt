package de.wutanglan.sonosnetwork.data.queue

data class PendingSurveyEntity(
    val id: Long = 0,
    val room_slug: String,
    val timestamp: String,
    val label: String,
    val trigger_mode: String = "STORE_AND_FORWARD",
    val connected_bssid: String? = null,
    val connected_ssid: String? = null,
    val link_speed_mbps: Int? = null,
    val frequency_mhz: Int? = null,
    val readings_json: String,
    val sync_status: String = "PENDING"
)
