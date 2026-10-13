package de.wutanglan.sonosnetwork.data.wifi

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Test

class BssidClassifierTest {

    @Test
    fun testManagedEap650MatchingAcrossVirtualVlans() {
        // Galerie AP 2.4 GHz (Admin VLAN, Family VLAN, Guest VLAN, IOT VLAN)
        val galerie24Admin = BssidClassifier.classifyBssid("72:4C:BC:76:7C:40", "Admin")
        assertEquals(BssidClassifier.OWN_MANAGED_AP, galerie24Admin.classification)
        assertEquals("galerie-ap", galerie24Admin.apDeviceSlug)
        assertEquals("2.4GHz", galerie24Admin.radioBand)

        val galerie5GFamily = BssidClassifier.classifyBssid("76:4C:BC:76:7C:41", "WuTangLan-Family")
        assertEquals(BssidClassifier.OWN_MANAGED_AP, galerie5GFamily.classification)
        assertEquals("galerie-ap", galerie5GFamily.apDeviceSlug)
        assertEquals("5GHz", galerie5GFamily.radioBand)

        // Kitchen AP 2.4 GHz & 5 GHz
        val kitchen24 = BssidClassifier.classifyBssid("76:4C:BC:76:94:C0", "WuTangLan-Family")
        assertEquals(BssidClassifier.OWN_MANAGED_AP, kitchen24.classification)
        assertEquals("kitchen-ap", kitchen24.apDeviceSlug)

        val kitchen5G = BssidClassifier.classifyBssid("7A:4C:BC:76:94:C1", "WuTangLan-Guest")
        assertEquals(BssidClassifier.OWN_MANAGED_AP, kitchen5G.classification)
        assertEquals("kitchen-ap", kitchen5G.apDeviceSlug)
    }

    @Test
    fun testRegisteredSonosNetMeshBssids() {
        // Wohnzimmer_Bookshelf BaseMAC + 1
        val wzBookshelf = BssidClassifier.classifyBssid("54:2A:1B:63:FE:6F", "")
        assertEquals(BssidClassifier.SONOSNET_MESH, wzBookshelf.classification)

        // Keller Play:3 BaseMAC + 1
        val keller = BssidClassifier.classifyBssid("5C:AA:FD:59:5E:EB", "")
        assertEquals(BssidClassifier.SONOSNET_MESH, keller.classification)

        // Nicolas Play:1 BaseMAC + 1
        val nicolas = BssidClassifier.classifyBssid("34:7E:5C:36:DE:91", "")
        assertEquals(BssidClassifier.SONOSNET_MESH, nicolas.classification)
    }

    @Test
    fun testRogueInHouseTransmitters() {
        // Retired EAP330
        val eap330ByMac = BssidClassifier.classifyBssid("84:16:F9:93:E9:2D", "")
        assertEquals(BssidClassifier.ROGUE_OWN_RADIO, eap330ByMac.classification)

        val eap330BySsid = BssidClassifier.classifyBssid("00:11:22:33:44:55", "TP-Link_5G_93E92D")
        assertEquals(BssidClassifier.ROGUE_OWN_RADIO, eap330BySsid.classification)

        // Fritzbox rogue Wi-Fi
        val fritzByMac = BssidClassifier.classifyBssid("0C:72:74:00:63:9A", "")
        assertEquals(BssidClassifier.ROGUE_OWN_RADIO, fritzByMac.classification)

        val fritzBySsid = BssidClassifier.classifyBssid("AA:BB:CC:DD:EE:FF", "WuTangLan")
        assertEquals(BssidClassifier.ROGUE_OWN_RADIO, fritzBySsid.classification)

        // Epson Wi-Fi Direct
        val epsonByMac = BssidClassifier.classifyBssid("6A:55:D4:7D:0B:9B", "")
        assertEquals(BssidClassifier.ROGUE_OWN_RADIO, epsonByMac.classification)

        val epsonBySsid = BssidClassifier.classifyBssid("11:22:33:44:55:66", "DIRECT-4b-EPSON-ET4850")
        assertEquals(BssidClassifier.ROGUE_OWN_RADIO, epsonBySsid.classification)
    }

    @Test
    fun testNeighborExternalNetworks() {
        val neighbor = BssidClassifier.classifyBssid("DC:39:6F:89:D6:03", "WLAN-A7C604")
        assertEquals(BssidClassifier.NEIGHBOR_WIFI, neighbor.classification)
    }
}
