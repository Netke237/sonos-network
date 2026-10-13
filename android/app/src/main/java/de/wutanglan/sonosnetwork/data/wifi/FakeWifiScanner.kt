package de.wutanglan.sonosnetwork.data.wifi

import kotlinx.coroutines.delay

class FakeWifiScanner : WifiScannerPort {

    var simulateThrottle: Boolean = false
    var throttleCooldownSec: Int = 30
    var permissionsGranted: Boolean = true
    var scanDelayMs: Long = 50L

    var cannedReadings: List<ScannedBssid> = listOf(
        ScannedBssid(
            bssid = "76:4c:bc:76:7c:41",
            ssid = "WuTangLan-Family",
            band = "5GHz",
            channel = 44,
            center_channel = 44,
            width_mhz = 80,
            rssi_dbm = -52,
            classification = BssidClassifier.OWN_MANAGED_AP,
            ap_device_slug = "galerie-ap",
            ap_name = "Galerie AP",
            is_connected = true,
            timestamp_micros = System.currentTimeMillis() * 1000
        ),
        ScannedBssid(
            bssid = "76:4c:bc:76:7c:40",
            ssid = "WuTangLan-Family",
            band = "2.4GHz",
            channel = 1,
            center_channel = 1,
            width_mhz = 20,
            rssi_dbm = -45,
            classification = BssidClassifier.OWN_MANAGED_AP,
            ap_device_slug = "galerie-ap",
            ap_name = "Galerie AP",
            is_connected = false,
            timestamp_micros = System.currentTimeMillis() * 1000
        )
    )

    override suspend fun probeSingleShotScan(): SingleShotScanResult {
        val startMicros = System.currentTimeMillis() * 1000
        if (scanDelayMs > 0) {
            delay(scanDelayMs)
        }
        val finishMicros = System.currentTimeMillis() * 1000

        if (simulateThrottle) {
            return SingleShotScanResult(
                probe_start_time_micros = startMicros,
                probe_finish_time_micros = finishMicros,
                is_fresh = false,
                is_throttled = true,
                throttle_cooldown_sec = throttleCooldownSec,
                connected_bssid = null,
                connected_ssid = null,
                link_speed_mbps = null,
                frequency_mhz = null,
                readings = emptyList()
            )
        }

        val connected = cannedReadings.firstOrNull { it.is_connected }
        return SingleShotScanResult(
            probe_start_time_micros = startMicros,
            probe_finish_time_micros = finishMicros,
            is_fresh = true,
            is_throttled = false,
            throttle_cooldown_sec = 0,
            connected_bssid = connected?.bssid,
            connected_ssid = connected?.ssid,
            link_speed_mbps = 1201,
            frequency_mhz = 5220,
            readings = cannedReadings
        )
    }

    override fun hasWifiPermissions(): Boolean = permissionsGranted

    override fun getThrottleCooldownRemainingSec(): Int {
        return if (simulateThrottle) throttleCooldownSec else 0
    }
}
