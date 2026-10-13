package de.wutanglan.sonosnetwork.ui.actions

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun ActionsScreen(
    viewModel: ActionsViewModel,
    modifier: Modifier = Modifier
) {
    val state by viewModel.uiState.collectAsState()
    val scrollState = rememberScrollState()

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .padding(16.dp)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Text(
            text = "⚡ Quick Actions & Diagnostics Hub",
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.onBackground
        )

        state.errorMessage?.let { error ->
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

        state.pollSuccessMessage?.let { msg ->
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

        // Action 1: 1-Click Ghost Group Reset
        Card(
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(
                    text = "1-Click Ghost Group Reset",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold
                )
                Text(
                    text = "Flushes detached coordinator group bindings (RINCON_...:counter mismatches), restoring clean cloud and Spotify streaming across all zones.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Button(
                    onClick = { viewModel.flushGhostGroups() },
                    enabled = !state.isFlushingGhostGroups,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    if (state.isFlushingGhostGroups) {
                        CircularProgressIndicator(
                            color = MaterialTheme.colorScheme.onPrimary,
                            modifier = Modifier.size(20.dp),
                            strokeWidth = 2.dp
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Flushing Ghost Groups...")
                    } else {
                        Text("Flush Ghost Groups Now")
                    }
                }
            }
        }

        // Action 2: Poll Live Sonos Mesh Now
        Card(
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(
                    text = "Poll Live Sonos Mesh Now",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold
                )
                Text(
                    text = "Forces an immediate live UPnP and STP telemetry probe across all 14 players on VLAN 10, updating noise floor, ANI, and PHY errors.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Button(
                    onClick = { viewModel.pollNow() },
                    enabled = !state.isPollingNow,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    if (state.isPollingNow) {
                        CircularProgressIndicator(
                            color = MaterialTheme.colorScheme.onPrimary,
                            modifier = Modifier.size(20.dp),
                            strokeWidth = 2.dp
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Polling Household...")
                    } else {
                        Text("Poll Sonos Now")
                    }
                }
            }
        }

        // Action 3: ICMP Ping Sweep
        Card(
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(
                    text = "ICMP Latency Sweep",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold
                )
                Text(
                    text = "Measures network round-trip latency and jitter to all speakers, detecting conditions that trigger Dynamic Packet Concealment (DPC) volume ducking.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Button(
                    onClick = { viewModel.runPingSweep() },
                    enabled = !state.isRunningPingSweep,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    if (state.isRunningPingSweep) {
                        CircularProgressIndicator(
                            color = MaterialTheme.colorScheme.onPrimary,
                            modifier = Modifier.size(20.dp),
                            strokeWidth = 2.dp
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Pinging 14 Players...")
                    } else {
                        Text("Run Ping Sweep")
                    }
                }

                state.pingSweepResult?.let { sweep ->
                    Card(
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                            Text(
                                text = "Ping Sweep Results: ${sweep.reachable_count}/${sweep.total_probed} Reachable",
                                fontWeight = FontWeight.Bold,
                                fontSize = 14.sp
                            )
                            Text(text = "Average RTT: ${String.format("%.1f", sweep.avg_rtt_ms)} ms  |  Max RTT: ${String.format("%.1f", sweep.max_rtt_ms)} ms", fontSize = 13.sp)
                            if (sweep.dpc_risk_zones.isNotEmpty()) {
                                Text(
                                    text = "⚠️ DPC Ducking Risk in: ${sweep.dpc_risk_zones.joinToString()}",
                                    color = MaterialTheme.colorScheme.error,
                                    fontWeight = FontWeight.SemiBold,
                                    fontSize = 12.sp
                                )
                            } else {
                                Text(text = "✓ Zero DPC volume ducking risks detected", color = Color(0xFF2E7D32), fontSize = 12.sp)
                            }
                        }
                    }
                }
            }
        }

        // Action 4: Live RF Velocity Oscilloscope
        Card(
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text(
                    text = "Live RF Velocity Oscilloscope",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold
                )
                Text(
                    text = "Real-time rolling waveform of PHY error rates and OFDM ANI desensitization over WebSocket.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )

                // Room selector chips
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    val rooms = listOf("wohnzimmer" to "Wohnzimmer", "galerie" to "Galerie", "nicolas" to "Nicolas")
                    for ((slug, name) in rooms) {
                        FilterChip(
                            selected = state.selectedOscilloscopeRoom == slug,
                            onClick = { viewModel.selectOscilloscopeRoom(slug) },
                            label = { Text(name) }
                        )
                    }
                }

                // Telemetry metrics
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        text = "PHY Errors: ${state.latestPhyErrPerSec?.let { String.format("%.1f err/s", it) } ?: "N/A"}",
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFF1B5E20),
                        fontSize = 13.sp
                    )
                    Text(
                        text = "ANI Level: ${state.latestAniLevel ?: "N/A"}",
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFFB71C1C),
                        fontSize = 13.sp
                    )
                }

                // Oscilloscope Waveform Canvas
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(140.dp)
                        .background(Color(0xFF1E1E1E), shape = RoundedCornerShape(8.dp))
                        .padding(8.dp)
                ) {
                    Canvas(modifier = Modifier.fillMaxSize()) {
                        val w = size.width
                        val h = size.height

                        // Grid lines
                        drawLine(Color(0xFF333333), Offset(0f, h * 0.25f), Offset(w, h * 0.25f), strokeWidth = 1f)
                        drawLine(Color(0xFF333333), Offset(0f, h * 0.5f), Offset(w, h * 0.5f), strokeWidth = 1f)
                        drawLine(Color(0xFF333333), Offset(0f, h * 0.75f), Offset(w, h * 0.75f), strokeWidth = 1f)

                        val history = state.livePhyHistory
                        if (history.size >= 2) {
                            val maxVal = (history.maxOrNull() ?: 10.0).coerceAtLeast(10.0)
                            val stepX = w / (history.size - 1)

                            val path = Path()
                            history.forEachIndexed { i, value ->
                                val x = i * stepX
                                val y = h - ((value / maxVal) * (h * 0.85f)).toFloat() - (h * 0.05f)
                                if (i == 0) path.moveTo(x, y) else path.lineTo(x, y)
                            }
                            drawPath(path, color = Color(0xFF00E676), style = Stroke(width = 3.dp.toPx()))
                        }
                    }
                }

                Button(
                    onClick = { viewModel.toggleOscilloscopeStream() },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(if (state.isStreamingOscilloscope) "Stop Oscilloscope Stream" else "Start Live Oscilloscope")
                }
            }
        }
    }

    // Ghost Flush Dialog
    if (state.ghostFlushDialogVisible) {
        val result = state.ghostFlushResult
        AlertDialog(
            onDismissRequest = { viewModel.dismissGhostFlushDialog() },
            title = { Text("Ghost Groups Flushed") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("Total zones reset: ${result?.flushed_count ?: 0}")
                    if (result != null && result.flushed_zones.isNotEmpty()) {
                        Text("Zones: ${result.flushed_zones.joinToString()}")
                    } else {
                        Text("All zone coordinators were already in standalone state.")
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { viewModel.dismissGhostFlushDialog() }) {
                    Text("OK")
                }
            }
        )
    }
}
