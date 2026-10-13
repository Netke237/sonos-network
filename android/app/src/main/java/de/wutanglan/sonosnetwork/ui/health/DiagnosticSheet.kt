package de.wutanglan.sonosnetwork.ui.health

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import de.wutanglan.sonosnetwork.data.models.RoomDiagnosticSummaryDto

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RoomDiagnosticModalSheet(
    diagnostic: RoomDiagnosticSummaryDto?,
    isLoading: Boolean,
    onDismiss: () -> Unit
) {
    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 20.dp, vertical = 10.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            if (isLoading) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(200.dp),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
                return@ModalBottomSheet
            }

            if (diagnostic == null) {
                Text("No diagnostic data available for this room.")
                return@ModalBottomSheet
            }

            // Header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "🔎 ${diagnostic.room_name} 3-Pillar Diagnostics",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "Floor: ${diagnostic.floor_name ?: diagnostic.floor_slug ?: "N/A"}",
                        fontSize = 12.sp,
                        color = Color.Gray
                    )
                }
                HealthGradeBadge(diagnostic.health_grade)
            }

            Divider()

            // Pillar 1: Wi-Fi Pillar
            Card(
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                shape = RoundedCornerShape(10.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text("Pillar 1: Wi-Fi Infrastructure", fontWeight = FontWeight.Bold, fontSize = 14.sp)
                        HealthGradeBadge(diagnostic.wifi_pillar.health_grade)
                    }
                    Text(
                        text = "Covering AP: ${diagnostic.wifi_pillar.covering_ap_name ?: "N/A"}",
                        fontSize = 12.sp
                    )
                    Text(
                        text = "5 GHz: ${diagnostic.wifi_pillar.best_5ghz_dbm?.let { "$it dBm" } ?: "N/A"}  |  2.4 GHz: ${diagnostic.wifi_pillar.best_24ghz_dbm?.let { "$it dBm" } ?: "N/A"}",
                        fontSize = 12.sp
                    )
                    if (diagnostic.wifi_pillar.summary_note.isNotBlank()) {
                        Text(text = diagnostic.wifi_pillar.summary_note, fontSize = 11.sp, color = Color.Gray)
                    }
                }
            }

            // Pillar 2: Sonos Mesh Pillar
            Card(
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                shape = RoundedCornerShape(10.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text("Pillar 2: Sonos Mesh & UPnP", fontWeight = FontWeight.Bold, fontSize = 14.sp)
                        HealthGradeBadge(diagnostic.sonos_pillar.health_grade)
                    }
                    Text(
                        text = "Players in Room: ${diagnostic.sonos_pillar.player_count} (Total reachable: ${diagnostic.sonos_pillar.reachable_count})",
                        fontSize = 12.sp
                    )
                    Text(
                        text = "Designated STP Root: ${diagnostic.sonos_pillar.designated_stp_root}",
                        fontSize = 11.sp,
                        color = Color.DarkGray
                    )

                    for (player in diagnostic.sonos_pillar.players) {
                        Surface(
                            shape = RoundedCornerShape(6.dp),
                            color = MaterialTheme.colorScheme.surface,
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 4.dp)
                        ) {
                            Column(modifier = Modifier.padding(8.dp)) {
                                Text(
                                    text = "${player.zone_name} (${player.connection_mode})",
                                    fontWeight = FontWeight.SemiBold,
                                    fontSize = 12.sp
                                )
                                Text(
                                    text = "ANI: ${player.ofdm_ani_level ?: "N/A"}  |  PHY: ${player.phy_error_rate?.let { String.format("%.1f err/s", it) } ?: "0.0"}  |  STP Cost: ${player.stp_path_cost ?: 0}",
                                    fontSize = 11.sp,
                                    color = Color.Gray
                                )
                            }
                        }
                    }
                }
            }

            // Pillar 3: Wired Switch Pillar
            Card(
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                shape = RoundedCornerShape(10.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text("Pillar 3: Wired Switch & VLAN", fontWeight = FontWeight.Bold, fontSize = 14.sp)
                        HealthGradeBadge(diagnostic.wired_pillar.health_grade)
                    }
                    Text(
                        text = if (diagnostic.wired_pillar.has_vlan10_wall_jack) {
                            "✓ Netgear GS316EP VLAN 10 wall jack available"
                        } else {
                            "No wired switch port patched in this room"
                        },
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Medium
                    )
                    if (diagnostic.wired_pillar.stp_root_guard_required || diagnostic.wired_pillar.stp_root_guard_note.isNotBlank()) {
                        Text(
                            text = "🛡️ STP Guard: ${diagnostic.wired_pillar.stp_root_guard_note.ifBlank { "Disable Wi-Fi on secondary wired speaker to prevent STP root usurpation across BPDU pass-through switch." }}",
                            color = Color(0xFF6A1B9A),
                            fontWeight = FontWeight.SemiBold,
                            fontSize = 11.sp
                        )
                    }
                }
            }

            // Ranked Solution Proposals
            if (diagnostic.solution_proposals.isNotEmpty()) {
                Text(
                    text = "💡 Ranked Solution Proposals (${diagnostic.solution_proposals.size})",
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp
                )

                for (proposal in diagnostic.solution_proposals) {
                    Card(
                        colors = CardDefaults.cardColors(containerColor = Color(0xFFF3E5F5)),
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                            Text(
                                text = "#${proposal.rank}: ${proposal.title}",
                                fontWeight = FontWeight.Bold,
                                color = Color(0xFF4A148C),
                                fontSize = 13.sp
                            )
                            Text(
                                text = proposal.description,
                                fontSize = 12.sp,
                                color = Color(0xFF4A148C)
                            )
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(20.dp))
        }
    }
}

@Composable
fun HealthGradeBadge(grade: String) {
    val (bg, fg) = when (grade.uppercase()) {
        "EXCELLENT" -> Color(0xFFE8F5E9) to Color(0xFF2E7D32)
        "GOOD" -> Color(0xFFE3F2FD) to Color(0xFF1565C0)
        "MARGINAL" -> Color(0xFFFFF3E0) to Color(0xFFE65100)
        else -> Color(0xFFFFEBEE) to Color(0xFFC62828)
    }

    Surface(color = bg, shape = RoundedCornerShape(4.dp)) {
        Text(
            text = grade.uppercase(),
            color = fg,
            fontWeight = FontWeight.Bold,
            fontSize = 11.sp,
            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
        )
    }
}
