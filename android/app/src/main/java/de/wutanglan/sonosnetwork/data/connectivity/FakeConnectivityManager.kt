package de.wutanglan.sonosnetwork.data.connectivity

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

class FakeConnectivityManager(
    initialState: ConnectionState = ConnectionState(
        transportType = NetworkTransportType.LOCAL_WIFI,
        isConnected = true,
        isRemoteVpnActive = false,
        activeEndpointUrl = ConnectionState.DEFAULT_LOCAL_LAN_URL,
        endpointMode = EndpointMode.AUTO
    )
) : ConnectivityPort {

    private val _state = MutableStateFlow(initialState)

    override fun observeConnectionState(): Flow<ConnectionState> = _state.asStateFlow()

    override fun isRemoteVpnActive(): Boolean = _state.value.isRemoteVpnActive

    override fun getActiveEndpointUrl(): String = _state.value.activeEndpointUrl

    override fun setEndpointMode(mode: EndpointMode) {
        val current = _state.value
        val url = when (mode) {
            EndpointMode.LOCAL_LAN -> ConnectionState.DEFAULT_LOCAL_LAN_URL
            EndpointMode.FIREWALLA_VPN -> ConnectionState.DEFAULT_FIREWALLA_VPN_URL
            EndpointMode.AUTO -> if (current.isRemoteVpnActive) {
                ConnectionState.DEFAULT_FIREWALLA_VPN_URL
            } else {
                ConnectionState.DEFAULT_LOCAL_LAN_URL
            }
        }
        _state.value = current.copy(endpointMode = mode, activeEndpointUrl = url)
    }

    fun updateState(newState: ConnectionState) {
        _state.value = newState
    }

    fun simulateVpnConnected(isActive: Boolean) {
        val current = _state.value
        val transport = if (isActive) NetworkTransportType.REMOTE_VPN else NetworkTransportType.LOCAL_WIFI
        val url = when (current.endpointMode) {
            EndpointMode.FIREWALLA_VPN -> ConnectionState.DEFAULT_FIREWALLA_VPN_URL
            EndpointMode.LOCAL_LAN -> ConnectionState.DEFAULT_LOCAL_LAN_URL
            EndpointMode.AUTO -> if (isActive) ConnectionState.DEFAULT_FIREWALLA_VPN_URL else ConnectionState.DEFAULT_LOCAL_LAN_URL
        }
        _state.value = current.copy(
            transportType = transport,
            isConnected = true,
            isRemoteVpnActive = isActive,
            activeEndpointUrl = url
        )
    }
}
