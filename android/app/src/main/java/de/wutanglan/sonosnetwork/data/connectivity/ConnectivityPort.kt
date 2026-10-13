package de.wutanglan.sonosnetwork.data.connectivity

import kotlinx.coroutines.flow.Flow

enum class EndpointMode {
    AUTO,
    LOCAL_LAN,
    FIREWALLA_VPN
}

enum class NetworkTransportType {
    LOCAL_WIFI,
    LOCAL_ETHERNET,
    REMOTE_VPN,
    CELLULAR,
    DISCONNECTED
}

data class ConnectionState(
    val transportType: NetworkTransportType = NetworkTransportType.DISCONNECTED,
    val isConnected: Boolean = false,
    val isRemoteVpnActive: Boolean = false,
    val activeEndpointUrl: String = DEFAULT_LOCAL_LAN_URL,
    val endpointMode: EndpointMode = EndpointMode.AUTO
) {
    companion object {
        const val DEFAULT_LOCAL_LAN_URL = "http://192.168.55.60:8001"
        const val DEFAULT_FIREWALLA_VPN_URL = "http://192.168.55.60:8001"
    }
}

interface ConnectivityPort {
    fun observeConnectionState(): Flow<ConnectionState>
    fun isRemoteVpnActive(): Boolean
    fun getActiveEndpointUrl(): String
    fun setEndpointMode(mode: EndpointMode)
}
