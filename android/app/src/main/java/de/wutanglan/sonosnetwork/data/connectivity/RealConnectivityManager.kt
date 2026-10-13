package de.wutanglan.sonosnetwork.data.connectivity

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.NetworkRequest
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

class RealConnectivityManager(
    private val context: Context,
    initialEndpointMode: EndpointMode = EndpointMode.AUTO
) : ConnectivityPort {

    private val connectivityManager =
        context.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager

    private val _connectionState = MutableStateFlow(
        computeInitialState(initialEndpointMode)
    )

    private val networkCallback = object : ConnectivityManager.NetworkCallback() {
        override fun onCapabilitiesChanged(network: Network, capabilities: NetworkCapabilities) {
            updateStateFromCapabilities(capabilities)
        }

        override fun onLost(network: Network) {
            val activeNetwork = connectivityManager?.activeNetwork
            val capabilities = activeNetwork?.let { connectivityManager.getNetworkCapabilities(it) }
            if (capabilities == null) {
                _connectionState.value = _connectionState.value.copy(
                    transportType = NetworkTransportType.DISCONNECTED,
                    isConnected = false,
                    isRemoteVpnActive = false
                )
            } else {
                updateStateFromCapabilities(capabilities)
            }
        }
    }

    init {
        registerCallback()
    }

    private fun registerCallback() {
        try {
            val request = NetworkRequest.Builder().build()
            connectivityManager?.registerNetworkCallback(request, networkCallback)
        } catch (_: Exception) {
            // Graceful fallback in constrained test runners
        }
    }

    private fun computeInitialState(endpointMode: EndpointMode): ConnectionState {
        val activeNetwork = connectivityManager?.activeNetwork
        val caps = activeNetwork?.let { connectivityManager.getNetworkCapabilities(it) }
        return resolveStateFromCapabilities(caps, endpointMode)
    }

    private fun updateStateFromCapabilities(capabilities: NetworkCapabilities) {
        val currentMode = _connectionState.value.endpointMode
        _connectionState.value = resolveStateFromCapabilities(capabilities, currentMode)
    }

    private fun resolveStateFromCapabilities(
        capabilities: NetworkCapabilities?,
        endpointMode: EndpointMode
    ): ConnectionState {
        if (capabilities == null) {
            return ConnectionState(
                transportType = NetworkTransportType.DISCONNECTED,
                isConnected = false,
                isRemoteVpnActive = false,
                activeEndpointUrl = resolveUrlForMode(endpointMode, isVpn = false),
                endpointMode = endpointMode
            )
        }

        val hasInternet = capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
        val isVpn = capabilities.hasTransport(NetworkCapabilities.TRANSPORT_VPN)
        val isWifi = capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)
        val isEthernet = capabilities.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET)
        val isCellular = capabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)

        val transport = when {
            isVpn -> NetworkTransportType.REMOTE_VPN
            isWifi -> NetworkTransportType.LOCAL_WIFI
            isEthernet -> NetworkTransportType.LOCAL_ETHERNET
            isCellular -> NetworkTransportType.CELLULAR
            else -> NetworkTransportType.DISCONNECTED
        }

        return ConnectionState(
            transportType = transport,
            isConnected = hasInternet,
            isRemoteVpnActive = isVpn,
            activeEndpointUrl = resolveUrlForMode(endpointMode, isVpn = isVpn),
            endpointMode = endpointMode
        )
    }

    private fun resolveUrlForMode(mode: EndpointMode, isVpn: Boolean): String {
        return when (mode) {
            EndpointMode.LOCAL_LAN -> ConnectionState.DEFAULT_LOCAL_LAN_URL
            EndpointMode.FIREWALLA_VPN -> ConnectionState.DEFAULT_FIREWALLA_VPN_URL
            EndpointMode.AUTO -> if (isVpn) {
                ConnectionState.DEFAULT_FIREWALLA_VPN_URL
            } else {
                ConnectionState.DEFAULT_LOCAL_LAN_URL
            }
        }
    }

    override fun observeConnectionState(): Flow<ConnectionState> = _connectionState.asStateFlow()

    override fun isRemoteVpnActive(): Boolean = _connectionState.value.isRemoteVpnActive

    override fun getActiveEndpointUrl(): String = _connectionState.value.activeEndpointUrl

    override fun setEndpointMode(mode: EndpointMode) {
        val current = _connectionState.value
        val url = resolveUrlForMode(mode, current.isRemoteVpnActive)
        _connectionState.value = current.copy(endpointMode = mode, activeEndpointUrl = url)
    }
}
