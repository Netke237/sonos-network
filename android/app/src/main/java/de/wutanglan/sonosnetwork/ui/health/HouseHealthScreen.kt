package de.wutanglan.sonosnetwork.ui.health

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import de.wutanglan.sonosnetwork.data.models.FloorMatrixItemDto
import de.wutanglan.sonosnetwork.data.models.RoomMatrixItemDto

@Composable
fun HouseHealthScreen(
    viewModel: HouseHealthViewModel,
    modifier: Modifier = Modifier
) {
    val state by viewModel.uiState.collectAsState()

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        // Title & View Toggle
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "🏠 House Health",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onBackground
            )

            // 1-tap view mode toggle
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                FilterChip(
                    selected = state.activeViewMode == HouseViewMode.ACCORDION_CARDS,
                    onClick = { viewModel.setViewMode(HouseViewMode.ACCORDION_CARDS) },
                    label = { Text("Cards") }
                )
                FilterChip(
                    selected = state.activeViewMode == HouseViewMode.TOPOLOGY_CANVAS,
                    onClick = { viewModel.setViewMode(HouseViewMode.TOPOLOGY_CANVAS) },
                    label = { Text("Canvas") }
                )
            }
        }

        // Overall House Health Banner
        val overview = state.overview
        val diagReport = state.houseDiagnostics
        val overallGrade = diagReport?.overall_health_grade ?: "GOOD"

        Card(
            colors = CardDefaults.cardColors(
                containerColor = when (overallGrade.uppercase()) {
                    "EXCELLENT" -> Color(0xFFE8F5E9)
                    "GOOD" -> Color(0xFFE3F2FD)
                    "MARGINAL" -> Color(0xFFFFF3E0)
                    else -> Color(0xFFFFEBEE)
                }
            ),
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Row(
                modifier = Modifier
                    .padding(14.dp)
                    .fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "Household Health: $overallGrade",
                        fontWeight = FontWeight.Bold,
                        fontSize = 15.sp,
                        color = Color.Black
                    )
                    Text(
                        text = "14 Sonos Players  |  11 Rooms  |  STP Root: ${overview?.designated_stp_root ?: "9000.542a1b63fe6e"}",
                        fontSize = 11.sp,
                        color = Color.DarkGray
                    )
                }
                HealthGradeBadge(overallGrade)
            }
        }

        if (state.isLoading) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
            return
        }

        // View Mode 1: Floor Accordion Cards
        if (state.activeViewMode == HouseViewMode.ACCORDION_CARDS) {
            val floors = overview?.floors ?: emptyList()
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                items(floors) { floor ->
                    FloorAccordionCard(
                        floor = floor,
                        onRoomClick = { roomSlug -> viewModel.openRoomDiagnostic(roomSlug) }
                    )
                }
            }
        } else {
            // View Mode 2: Interactive Pan / Zoom Topological Canvas
            TopologyCanvasView(
                nodesCount = state.topology?.total_nodes ?: 0,
                edgesCount = state.topology?.total_edges ?: 0,
                onNodeClick = { slug -> viewModel.openRoomDiagnostic(slug) }
            )
        }
    }

    // Room 3-Pillar Diagnostic Sheet
    if (state.isDiagnosticSheetOpen) {
        RoomDiagnosticModalSheet(
            diagnostic = state.selectedRoomDiagnostic,
            isLoading = state.isLoadingRoomDiagnostic,
            onDismiss = { viewModel.closeDiagnosticSheet() }
        )
    }
}

@Composable
fun FloorAccordionCard(
    floor: FloorMatrixItemDto,
    onRoomClick: (String) -> Unit
) {
    var expanded by remember { mutableStateOf(true) }

    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
        shape = RoundedCornerShape(12.dp),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable { expanded = !expanded },
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "${floor.name} (${floor.rooms.size} rooms)",
                    fontWeight = FontWeight.Bold,
                    fontSize = 15.sp
                )
                Text(if (expanded) "▲" else "▼", fontSize = 12.sp, color = Color.Gray)
            }

            if (expanded) {
                Spacer(modifier = Modifier.height(8.dp))
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    for (room in floor.rooms) {
                        RoomItemCard(room = room, onClick = { onRoomClick(room.slug) })
                    }
                }
            }
        }
    }
}

@Composable
fun RoomItemCard(
    room: RoomMatrixItemDto,
    onClick: () -> Unit
) {
    Surface(
        color = MaterialTheme.colorScheme.surface,
        shape = RoundedCornerShape(8.dp),
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
    ) {
        Column(modifier = Modifier.padding(10.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(text = room.name, fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
                HealthGradeBadge(room.health_grade)
            }

            Text(
                text = "Wi-Fi: ${room.best_5ghz_dbm?.let { "$it dBm" } ?: "N/A"} (${room.best_ap_name ?: "Auto"})  |  Sonos: ${room.devices.count { it.device_role == "SONOS_PLAYER" }} player(s)",
                fontSize = 12.sp,
                color = Color.DarkGray
            )

            Text(
                text = "Tap to inspect 3-Pillar Diagnostics & Proposals →",
                fontSize = 11.sp,
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.Medium
            )
        }
    }
}

@Composable
fun TopologyCanvasView(
    nodesCount: Int,
    edgesCount: Int,
    onNodeClick: (String) -> Unit
) {
    var scale by remember { mutableFloatStateOf(1f) }
    var offset by remember { mutableStateOf(Offset.Zero) }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF181818), shape = RoundedCornerShape(12.dp))
            .pointerInput(Unit) {
                detectTransformGestures { _, pan, zoom, _ ->
                    scale = (scale * zoom).coerceIn(0.5f, 3.0f)
                    offset += pan
                }
            }
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val w = size.width
            val h = size.height

            // Center origin with offset
            val cx = (w / 2) + offset.x
            val cy = (h / 2) + offset.y

            // Sample topology graph nodes & edges rendering
            val rRoot = Offset(cx, cy - 120 * scale)
            val rAp1 = Offset(cx - 140 * scale, cy + 20 * scale)
            val rAp2 = Offset(cx + 140 * scale, cy + 20 * scale)
            val rSonos = Offset(cx, cy + 120 * scale)

            // Edges
            drawLine(Color(0xFF4CAF50), rRoot, rAp1, strokeWidth = 3f * scale)
            drawLine(Color(0xFF4CAF50), rRoot, rAp2, strokeWidth = 3f * scale)
            drawLine(Color(0xFF2196F3), rRoot, rSonos, strokeWidth = 3f * scale)

            // Blocked link (dashed)
            val dashEffect = PathEffect.dashPathEffect(floatArrayOf(10f, 10f), 0f)
            drawLine(
                Color(0xFFFF9800),
                rAp1,
                rSonos,
                strokeWidth = 2f * scale,
                pathEffect = dashEffect
            )

            // Nodes
            drawCircle(Color(0xFF4CAF50), radius = 18f * scale, center = rRoot)
            drawCircle(Color(0xFF2196F3), radius = 14f * scale, center = rAp1)
            drawCircle(Color(0xFF2196F3), radius = 14f * scale, center = rAp2)
            drawCircle(Color(0xFF9C27B0), radius = 14f * scale, center = rSonos)
        }

        Column(
            modifier = Modifier
                .align(Alignment.BottomStart)
                .padding(12.dp)
        ) {
            Text(
                text = "Vector Topology Graph ($nodesCount nodes, $edgesCount edges)",
                color = Color.White,
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = "Pinch to zoom, drag to pan. Solid = Active, Dashed = STP Blocked",
                color = Color.Gray,
                fontSize = 11.sp
            )
        }
    }
}
