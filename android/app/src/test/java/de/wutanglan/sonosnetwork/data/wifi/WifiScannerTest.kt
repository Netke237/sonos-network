package de.wutanglan.sonosnetwork.data.wifi

import androidx.test.core.app.ApplicationProvider
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34])
class WifiScannerTest {

    @Test
    fun testFakeWifiScannerFreshProbe() = runBlocking {
        val fake = FakeWifiScanner()
        assertTrue(fake.hasWifiPermissions())
        assertEquals(0, fake.getThrottleCooldownRemainingSec())

        val result = fake.probeSingleShotScan()
        assertTrue(result.is_fresh)
        assertFalse(result.is_throttled)
        assertEquals(2, result.readings.size)
        assertEquals("76:4c:bc:76:7c:41", result.connected_bssid)
        assertEquals(1201, result.link_speed_mbps)

        val first = result.readings.first()
        assertEquals(44, first.channel)
        assertEquals("5GHz", first.band)
        assertEquals(BssidClassifier.OWN_MANAGED_AP, first.classification)
        assertEquals("galerie-ap", first.ap_device_slug)
    }

    @Test
    fun testFakeWifiScannerThrottledProbe() = runBlocking {
        val fake = FakeWifiScanner()
        fake.simulateThrottle = true
        fake.throttleCooldownSec = 45

        val result = fake.probeSingleShotScan()
        assertFalse(result.is_fresh)
        assertTrue(result.is_throttled)
        assertEquals(45, result.throttle_cooldown_sec)
        assertTrue(result.readings.isEmpty())
        assertEquals(45, fake.getThrottleCooldownRemainingSec())
    }

    @Test
    fun testRealWifiScannerCooldownCalculation() {
        val context = ApplicationProvider.getApplicationContext<android.content.Context>()
        val real = RealWifiScanner(context)

        // Initially no scans executed, cooldown should be 0
        assertEquals(0, real.getThrottleCooldownRemainingSec())
    }
}
