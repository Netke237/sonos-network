package de.wutanglan.sonosnetwork.data.wifi

data class ScannedBssid(
    val bssid: String,
    val ssid: String?,
    val band: String,
    val channel: Int,
    val center_channel: Int,
    val width_mhz: Int,
    val rssi_dbm: Int,
    val classification: String,
    val ap_device_slug: String?,
    val ap_name: String?,
    val is_connected: Boolean = false,
    val timestamp_micros: Long
)

data class SingleShotScanResult(
    val probe_start_time_micros: Long,
    val probe_finish_time_micros: Long,
    val is_fresh: Boolean,
    val is_throttled: Boolean,
    val throttle_cooldown_sec: Int,
    val connected_bssid: String?,
    val connected_ssid: String?,
    val link_speed_mbps: Int?,
    val frequency_mhz: Int?,
    val readings: List<ScannedBssid>
)

interface WifiScannerPort {
    suspend fun probeSingleShotScan(): SingleShotScanResult
    fun hasWifiPermissions(): Boolean
    fun getThrottleCooldownRemainingSec(): Int
}
