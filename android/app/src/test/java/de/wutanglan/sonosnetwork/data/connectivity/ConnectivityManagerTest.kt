package de.wutanglan.sonosnetwork.data.connectivity

import androidx.test.core.app.ApplicationProvider
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34])
class ConnectivityManagerTest {

    @Test
    fun testFakeConnectivityManagerEndpointSwitching() {
        val fake = FakeConnectivityManager()

        // Default state: Local Wi-Fi, Auto mode -> Local LAN url
        assertEquals(ConnectionState.DEFAULT_LOCAL_LAN_URL, fake.getActiveEndpointUrl())
        assertFalse(fake.isRemoteVpnActive())

        // Simulate VPN connection in Auto mode -> switches to VPN URL
        fake.simulateVpnConnected(true)
        assertTrue(fake.isRemoteVpnActive())
        assertEquals(ConnectionState.DEFAULT_FIREWALLA_VPN_URL, fake.getActiveEndpointUrl())

        // Force LOCAL_LAN override even while VPN is active
        fake.setEndpointMode(EndpointMode.LOCAL_LAN)
        assertEquals(ConnectionState.DEFAULT_LOCAL_LAN_URL, fake.getActiveEndpointUrl())

        // Force FIREWALLA_VPN override
        fake.setEndpointMode(EndpointMode.FIREWALLA_VPN)
        assertEquals(ConnectionState.DEFAULT_FIREWALLA_VPN_URL, fake.getActiveEndpointUrl())

        // Return to AUTO while VPN disconnected -> Local LAN URL
        fake.setEndpointMode(EndpointMode.AUTO)
        fake.simulateVpnConnected(false)
        assertFalse(fake.isRemoteVpnActive())
        assertEquals(ConnectionState.DEFAULT_LOCAL_LAN_URL, fake.getActiveEndpointUrl())
    }

    @Test
    fun testRealConnectivityManagerInitialization() {
        val context = ApplicationProvider.getApplicationContext<android.content.Context>()
        val real = RealConnectivityManager(context, EndpointMode.AUTO)

        assertNotNull(real.getActiveEndpointUrl())
        // In Robolectric environment without active VPN transport
        assertFalse(real.isRemoteVpnActive())
        assertEquals(ConnectionState.DEFAULT_LOCAL_LAN_URL, real.getActiveEndpointUrl())

        // Setting explicit endpoint mode updates URL
        real.setEndpointMode(EndpointMode.FIREWALLA_VPN)
        assertEquals(ConnectionState.DEFAULT_FIREWALLA_VPN_URL, real.getActiveEndpointUrl())

        real.setEndpointMode(EndpointMode.LOCAL_LAN)
        assertEquals(ConnectionState.DEFAULT_LOCAL_LAN_URL, real.getActiveEndpointUrl())
    }
}
