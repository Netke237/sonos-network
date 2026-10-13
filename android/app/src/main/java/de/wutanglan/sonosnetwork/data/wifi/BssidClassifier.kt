package de.wutanglan.sonosnetwork.data.wifi

data class ClassificationResult(
    val classification: String,
    val apDeviceSlug: String? = null,
    val apName: String? = null,
    val radioBand: String? = null
)

object BssidClassifier {

    const val OWN_MANAGED_AP = "OWN_MANAGED_AP"
    const val SONOSNET_MESH = "SONOSNET_MESH"
    const val ROGUE_OWN_RADIO = "ROGUE_OWN_RADIO"
    const val NEIGHBOR_WIFI = "NEIGHBOR_WIFI"

    private val SONOSNET_BSSIDS = setOf(
        "54:2a:1b:63:fe:6f",
        "b8:e9:37:e6:09:85",
        "b8:e9:37:e5:15:2b",
        "94:9f:3e:c0:ee:a2",
        "5c:aa:fd:49:0c:cb",
        "94:9f:3e:00:29:2f",
        "5c:aa:fd:59:5e:eb",
        "34:7e:5c:38:26:e3",
        "34:7e:5c:35:b0:f5",
        "34:7e:5c:35:b2:c1",
        "54:2a:1b:64:26:81",
        "34:7e:5c:36:de:91",
        "34:7e:5c:38:28:b1",
        "34:7e:5c:31:ce:29"
    )

    fun classifyBssid(bssid: String, ssid: String?): ClassificationResult {
        val norm = bssid.lowercase().trim()
        val clean = norm.replace(":", "").replace("-", "")

        // 1. Managed TP-Link EAP650 Access Points (matches lower 5 octets across all virtual VLAN SSIDs)
        if (clean.endsWith("4cbc767c40")) {
            return ClassificationResult(
                classification = OWN_MANAGED_AP,
                apDeviceSlug = "galerie-ap",
                apName = "Galerie AP",
                radioBand = "2.4GHz"
            )
        }
        if (clean.endsWith("4cbc767c41")) {
            return ClassificationResult(
                classification = OWN_MANAGED_AP,
                apDeviceSlug = "galerie-ap",
                apName = "Galerie AP",
                radioBand = "5GHz"
            )
        }
        if (clean.endsWith("4cbc7694c0")) {
            return ClassificationResult(
                classification = OWN_MANAGED_AP,
                apDeviceSlug = "kitchen-ap",
                apName = "Kitchen AP",
                radioBand = "2.4GHz"
            )
        }
        if (clean.endsWith("4cbc7694c1")) {
            return ClassificationResult(
                classification = OWN_MANAGED_AP,
                apDeviceSlug = "kitchen-ap",
                apName = "Kitchen AP",
                radioBand = "5GHz"
            )
        }

        // 2. Household SonosNet Mesh (BaseMAC + 1 registered BSSIDs)
        if (norm in SONOSNET_BSSIDS) {
            return ClassificationResult(
                classification = SONOSNET_MESH,
                radioBand = "2.4GHz"
            )
        }

        // 3. Rogue / retired in-house radios
        val cleanSsid = ssid?.trim() ?: ""
        if (clean.startsWith("8416f993e92") || clean.startsWith("8616f9bfe92") ||
            cleanSsid == "TP-Link_5G_93E92D"
        ) {
            return ClassificationResult(
                classification = ROGUE_OWN_RADIO,
                apName = "Retired EAP330"
            )
        }

        if (clean.startsWith("0c727400639") || cleanSsid == "WuTangLan") {
            return ClassificationResult(
                classification = ROGUE_OWN_RADIO,
                apName = "Fritzbox Rogue Wi-Fi"
            )
        }

        if (clean == "6a55d47d0b9b" || cleanSsid.matches(Regex("DIRECT-.*-EPSON.*", RegexOption.IGNORE_CASE))) {
            return ClassificationResult(
                classification = ROGUE_OWN_RADIO,
                apName = "Epson Wi-Fi Direct"
            )
        }

        // 4. Neighbor / External Wi-Fi
        return ClassificationResult(
            classification = NEIGHBOR_WIFI
        )
    }
}
