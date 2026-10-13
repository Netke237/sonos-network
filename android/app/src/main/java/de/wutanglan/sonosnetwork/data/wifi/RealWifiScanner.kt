package de.wutanglan.sonosnetwork.data.wifi

import android.Manifest
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.net.wifi.ScanResult
import android.net.wifi.WifiInfo
import android.net.wifi.WifiManager
import android.os.Build
import android.os.SystemClock
import androidx.core.content.ContextCompat
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withTimeoutOrNull
import kotlin.coroutines.resume

class RealWifiScanner(
    private val context: Context,
    private val wifiManager: WifiManager? = context.applicationContext.getSystemService(Context.WIFI_SERVICE) as? WifiManager
) : WifiScannerPort {

    private val scanHistory = mutableListOf<Long>()

    override fun hasWifiPermissions(): Boolean {
        val fineLocation = ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.ACCESS_FINE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED

        val nearbyWifi = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.NEARBY_WIFI_DEVICES
            ) == PackageManager.PERMISSION_GRANTED
        } else {
            true
        }

        return fineLocation && nearbyWifi
    }

    override fun getThrottleCooldownRemainingSec(): Int {
        val now = SystemClock.elapsedRealtime()
        val windowStart = now - 120_000L
        synchronized(scanHistory) {
            scanHistory.removeAll { it < windowStart }
            if (scanHistory.size >= 4) {
                val oldestInWindow = scanHistory.first()
                val remainingMs = (oldestInWindow + 120_000L) - now
                return ((remainingMs + 999) / 1000).toInt().coerceAtLeast(0)
            }
        }
        return 0
    }

    override suspend fun probeSingleShotScan(): SingleShotScanResult {
        val probeStartTimeMicros = SystemClock.elapsedRealtime() * 1000L

        if (!hasWifiPermissions() || wifiManager == null) {
            return SingleShotScanResult(
                probe_start_time_micros = probeStartTimeMicros,
                probe_finish_time_micros = SystemClock.elapsedRealtime() * 1000L,
                is_fresh = false,
                is_throttled = false,
                throttle_cooldown_sec = 0,
                connected_bssid = null,
                connected_ssid = null,
                link_speed_mbps = null,
                frequency_mhz = null,
                readings = emptyList()
            )
        }

        val cooldownSec = getThrottleCooldownRemainingSec()
        if (cooldownSec > 0) {
            return SingleShotScanResult(
                probe_start_time_micros = probeStartTimeMicros,
                probe_finish_time_micros = SystemClock.elapsedRealtime() * 1000L,
                is_fresh = false,
                is_throttled = true,
                throttle_cooldown_sec = cooldownSec,
                connected_bssid = null,
                connected_ssid = null,
                link_speed_mbps = null,
                frequency_mhz = null,
                readings = emptyList()
            )
        }

        val scanResultOutcome = withTimeoutOrNull(10_000L) {
            suspendCancellableCoroutine<Pair<Boolean, List<ScanResult>>> { continuation ->
                val receiver = object : BroadcastReceiver() {
                    override fun onReceive(c: Context?, intent: Intent?) {
                        val isUpdated = intent?.getBooleanExtra(
                            WifiManager.EXTRA_RESULTS_UPDATED,
                            false
                        ) ?: false

                        try {
                            context.unregisterReceiver(this)
                        } catch (_: Exception) {
                        }

                        val results = try {
                            wifiManager.scanResults ?: emptyList()
                        } catch (_: Exception) {
                            emptyList()
                        }

                        if (continuation.isActive) {
                            continuation.resume(isUpdated to results)
                        }
                    }
                }

                val filter = IntentFilter(WifiManager.SCAN_RESULTS_AVAILABLE_ACTION)
                context.registerReceiver(receiver, filter)

                continuation.invokeOnCancellation {
                    try {
                        context.unregisterReceiver(receiver)
                    } catch (_: Exception) {
                    }
                }

                val started = try {
                    wifiManager.startScan()
                } catch (_: Exception) {
                    false
                }

                if (!started) {
                    try {
                        context.unregisterReceiver(receiver)
                    } catch (_: Exception) {
                    }
                    if (continuation.isActive) {
                        continuation.resume(false to (wifiManager.scanResults ?: emptyList()))
                    }
                }
            }
        }

        val finishTimeMicros = SystemClock.elapsedRealtime() * 1000L
        val isUpdated = scanResultOutcome?.first ?: false
        val rawResults = scanResultOutcome?.second ?: emptyList()

        if (!isUpdated) {
            // Android 10+ throttling triggered
            return SingleShotScanResult(
                probe_start_time_micros = probeStartTimeMicros,
                probe_finish_time_micros = finishTimeMicros,
                is_fresh = false,
                is_throttled = true,
                throttle_cooldown_sec = 30,
                connected_bssid = null,
                connected_ssid = null,
                link_speed_mbps = null,
                frequency_mhz = null,
                readings = emptyList()
            )
        }

        // Record successful scan in history
        synchronized(scanHistory) {
            scanHistory.add(SystemClock.elapsedRealtime())
        }

        // Active connection info
        val connectionInfo: WifiInfo? = try {
            wifiManager.connectionInfo
        } catch (_: Exception) {
            null
        }

        val connectedBssid = connectionInfo?.bssid?.takeIf { it != "02:00:00:00:00:00" }
        val connectedSsid = connectionInfo?.ssid?.trim('\"')
        val linkSpeed = connectionInfo?.linkSpeed?.takeIf { it > 0 }
        val connectedFreq = connectionInfo?.frequency?.takeIf { it > 0 }

        // Filter for fresh probe entries: timestamp >= probeStartTimeMicros
        // Add a 500ms safety window in case hardware clock slightly desynchronized
        val freshnessThresholdMicros = probeStartTimeMicros - 500_000L
        val freshScanResults = rawResults.filter { it.timestamp >= freshnessThresholdMicros }

        val readings = freshScanResults.map { sr ->
            val primaryCh = WifiFrequencyMapper.frequencyToChannel(sr.frequency)
            val centerCh = WifiFrequencyMapper.centerFrequencyToChannel(sr.centerFreq0, primaryCh)
            val band = WifiFrequencyMapper.frequencyToBand(sr.frequency)
            val width = WifiFrequencyMapper.channelWidthMhz(sr.channelWidth)
            val classification = BssidClassifier.classifyBssid(sr.BSSID, sr.SSID)
            val isConnected = connectedBssid?.equals(sr.BSSID, ignoreCase = true) == true

            ScannedBssid(
                bssid = sr.BSSID,
                ssid = sr.SSID?.takeIf { it.isNotBlank() },
                band = band,
                channel = primaryCh,
                center_channel = centerCh,
                width_mhz = width,
                rssi_dbm = sr.level,
                classification = classification.classification,
                ap_device_slug = classification.apDeviceSlug,
                ap_name = classification.apName,
                is_connected = isConnected,
                timestamp_micros = sr.timestamp
            )
        }

        return SingleShotScanResult(
            probe_start_time_micros = probeStartTimeMicros,
            probe_finish_time_micros = finishTimeMicros,
            is_fresh = true,
            is_throttled = false,
            throttle_cooldown_sec = 0,
            connected_bssid = connectedBssid,
            connected_ssid = connectedSsid,
            link_speed_mbps = linkSpeed,
            frequency_mhz = connectedFreq,
            readings = readings
        )
    }
}
