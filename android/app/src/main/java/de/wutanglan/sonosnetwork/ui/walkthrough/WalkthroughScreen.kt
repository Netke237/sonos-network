package de.wutanglan.sonosnetwork.ui.walkthrough

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import de.wutanglan.sonosnetwork.data.wifi.BssidClassifier
import de.wutanglan.sonosnetwork.data.wifi.ScannedBssid

@Composable
fun WalkthroughScreen(
    viewModel: WalkthroughViewModel,
    modifier: Modifier = Modifier
) {
    val state by viewModel.uiState.collectAsState()

    LazyColumn(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        item {
            Text(
                text = "📍 Room Survey Walkthrough",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onBackground
            )
        }

        // VPN Banner Guard
        if (state.isRemoteVpnActive) {
            item {
                Card(
                    colors = CardDefaults.cardColors(containerColor = Color(0xFFFFF3E0)),
                    shape = RoundedCornerShape(10.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(14.dp)) {
                        Text(
                            text = "🛡️ Connected via Firewalla Remote VPN",
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFFE65100),
                            fontSize = 14.sp
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "Physical Wi-Fi scanning paused (device is off-premise). Telemetry views and UPnP actions remain active.",
                            color = Color(0xFFE65100),
                            fontSize = 12.sp
                        )
                    }
                }
            }
        }

        // Offline queue status pill
        if (state.queuedSurveysCount > 0) {
            item {
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer),
                    shape = RoundedCornerShape(10.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "📦 ${state.queuedSurveysCount} survey(s) queued (offline)",
                            color = MaterialTheme.colorScheme.onSecondaryContainer,
                            fontWeight = FontWeight.SemiBold,
                            fontSize = 13.sp
                        )
                        Button(
                            onClick = { viewModel.syncQueueNow() },
                            enabled = !state.isSyncingQueue,
                            colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.secondary),
                            contentPadding = PaddingValues(horizontal = 12.dp, vertical = 6.dp)
                        ) {
                            Text(if (state.isSyncingQueue) "Syncing..." else "Sync Now", fontSize = 12.sp)
                        }
                    }
                }
            }
        }

        // Messages
        state.errorMessage?.let { error ->
            item {
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(text = error, color = MaterialTheme.colorScheme.onErrorContainer, fontSize = 13.sp)
                        TextButton(onClick = { viewModel.clearMessages() }) {
                            Text("Dismiss", color = MaterialTheme.colorScheme.onErrorContainer)
                        }
                    }
                }
            }
        }

        state.statusMessage?.let { msg ->
            item {
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(text = msg, color = MaterialTheme.colorScheme.onPrimaryContainer, fontSize = 13.sp)
                        TextButton(onClick = { viewModel.clearMessages() }) {
                            Text("OK", color = MaterialTheme.colorScheme.onPrimaryContainer)
                        }
                    }
                }
            }
        }

        // Floor selector
        item {
            Text("Select Floor:", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)
            Spacer(modifier = Modifier.height(4.dp))
            LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                items(state.availableFloors) { (slug, name) ->
                    FilterChip(
                        selected = state.selectedFloorSlug == slug,
                        onClick = { viewModel.selectFloor(slug) },
                        label = { Text(name) }
                    )
                }
            }
        }

        // Room selector
        item {
            Text("Select Room:", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)
            Spacer(modifier = Modifier.height(4.dp))
            LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                items(state.availableRooms) { (slug, name) ->
                    FilterChip(
                        selected = state.selectedRoomSlug == slug,
                        onClick = { viewModel.selectRoom(slug) },
                        label = { Text(name) }
                    )
                }
            }
        }

        // Action Button: Scan Room Now
        item {
            Button(
                onClick = { viewModel.scanRoomNow() },
                enabled = !state.isScanning && !state.isRemoteVpnActive && !state.isThrottled,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
                shape = RoundedCornerShape(12.dp)
            ) {
                if (state.isScanning) {
                    CircularProgressIndicator(
                        color = MaterialTheme.colorScheme.onPrimary,
                        modifier = Modifier.size(22.dp),
                        strokeWidth = 2.dp
                    )
                    Spacer(modifier = Modifier.width(10.dp))
                    Text("Probing 802.11 RF Sweep...", fontSize = 15.sp)
                } else if (state.isThrottled) {
                    Text("Throttled (${state.throttleCooldownSec}s cooldown)", fontSize = 15.sp)
                } else {
                    Text("📡 Scan Room Now (${state.selectedRoomSlug.replaceFirstChar { it.uppercase() }})", fontSize = 15.sp)
                }
            }
        }

        // Live Scan Preview Card
        state.lastScanResult?.let { scan ->
            val sortedReadings = scan.readings.sortedByDescending { it.rssi_dbm }

            item {
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = "Last Scan Results (${scan.readings.size} BSSIDs heard)",
                                fontWeight = FontWeight.Bold,
                                fontSize = 15.sp
                            )
                            if (sortedReadings.isNotEmpty()) {
                                Surface(
                                    color = Color(0xFFE8F5E9),
                                    shape = RoundedCornerShape(4.dp)
                                ) {
                                    Text(
                                        text = "Ranked #1 → #${sortedReadings.size}",
                                        color = Color(0xFF2E7D32),
                                        fontSize = 10.sp,
                                        fontWeight = FontWeight.Bold,
                                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                    )
                                }
                            }
                        }

                        // Connected network row
                        scan.connected_ssid?.let { ssid ->
                            Text(
                                text = "Connected: $ssid (Link speed: ${scan.link_speed_mbps ?: "N/A"} Mbps, Freq: ${scan.frequency_mhz ?: "N/A"} MHz)",
                                fontSize = 12.sp,
                                color = MaterialTheme.colorScheme.primary,
                                fontWeight = FontWeight.SemiBold
                            )
                        }

                        // Strongest AP summary
                        val best5G = scan.readings.filter { it.band == "5GHz" }.maxByOrNull { it.rssi_dbm }
                        val best24G = scan.readings.filter { it.band == "2.4GHz" }.maxByOrNull { it.rssi_dbm }

                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    text = "BEST 5 GHz",
                                    fontSize = 10.sp,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f),
                                    fontWeight = FontWeight.Bold
                                )
                                Text(
                                    text = best5G?.let { "${it.rssi_dbm} dBm (${it.ap_name ?: it.ssid ?: "5G"})" } ?: "None",
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.SemiBold
                                )
                            }
                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    text = "BEST 2.4 GHz",
                                    fontSize = 10.sp,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f),
                                    fontWeight = FontWeight.Bold
                                )
                                Text(
                                    text = best24G?.let { "${it.rssi_dbm} dBm (${it.ap_name ?: it.ssid ?: "2.4G"})" } ?: "None",
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.SemiBold
                                )
                            }
                        }
                    }
                }
            }

            // Wi-Fi Signal Quality Guide
            item {
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    shape = RoundedCornerShape(8.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(10.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text(
                            text = "SIGNAL QUALITY GUIDE",
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
                        )
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text("● ≥ -55: Excellent", fontSize = 10.sp, fontWeight = FontWeight.SemiBold, color = Color(0xFF2E7D32))
                            Text("● -56..-67: Good", fontSize = 10.sp, fontWeight = FontWeight.SemiBold, color = Color(0xFF1565C0))
                            Text("● -68..-75: Fair", fontSize = 10.sp, fontWeight = FontWeight.SemiBold, color = Color(0xFFE65100))
                            Text("● < -75: Poor", fontSize = 10.sp, fontWeight = FontWeight.SemiBold, color = Color(0xFFC62828))
                        }
                    }
                }
            }

            // Dedicated Column Header Row
            item {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 4.dp, vertical = 2.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "NETWORK / ACCESS POINT",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
                    )
                    Text(
                        text = "SIGNAL QUALITY (dBm)",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
                    )
                }
            }

            // Heard BSSID items (Ranked Best to Worst)
            itemsIndexed(sortedReadings) { index, bssidItem ->
                BssidReadingItemView(reading = bssidItem, rank = index + 1)
            }
        }
    }
}

@Composable
fun BssidReadingItemView(reading: ScannedBssid, rank: Int) {
    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        shape = RoundedCornerShape(8.dp),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .padding(10.dp)
                .fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = "#$rank",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = reading.ssid ?: "<Hidden SSID>",
                        fontWeight = FontWeight.SemiBold,
                        fontSize = 13.sp
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    ClassificationBadge(reading.classification, reading.ap_name)
                }
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = "${reading.bssid}  |  ${reading.band} Ch ${reading.channel} (${reading.width_mhz} MHz)",
                    fontSize = 11.sp,
                    color = Color.Gray
                )
            }
            Column(horizontalAlignment = Alignment.End) {
                val (qualityLabel, qualityColor) = when {
                    reading.rssi_dbm >= -55 -> "EXCELLENT" to Color(0xFF2E7D32)
                    reading.rssi_dbm >= -67 -> "GOOD" to Color(0xFF1565C0)
                    reading.rssi_dbm >= -75 -> "FAIR" to Color(0xFFE65100)
                    else -> "POOR" to Color(0xFFC62828)
                }
                Text(
                    text = "${reading.rssi_dbm} dBm",
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp,
                    color = qualityColor
                )
                Text(
                    text = "● $qualityLabel",
                    fontSize = 9.sp,
                    fontWeight = FontWeight.Bold,
                    color = qualityColor
                )
            }
        }
    }
}

@Composable
fun ClassificationBadge(classification: String, apName: String? = null) {
    val (label, bg, fg) = when (classification) {
        BssidClassifier.OWN_MANAGED_AP -> Triple(
            apName ?: "Managed AP",
            Color(0xFFE8F5E9),
            Color(0xFF2E7D32)
        )
        BssidClassifier.SONOSNET_MESH -> Triple(
            "SonosNet",
            Color(0xFFE3F2FD),
            Color(0xFF1565C0)
        )
        BssidClassifier.ROGUE_OWN_RADIO -> Triple(
            apName ?: "Rogue Radio",
            Color(0xFFFFEBEE),
            Color(0xFFC62828)
        )
        else -> Triple(
            "Neighbor",
            Color(0xFFF5F5F5),
            Color(0xFF616161)
        )
    }
    Surface(
        color = bg,
        shape = RoundedCornerShape(4.dp),
        modifier = Modifier.padding(2.dp)
    ) {
        Text(
            text = label,
            color = fg,
            fontSize = 10.sp,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(horizontal = 4.dp, vertical = 2.dp)
        )
    }
}
