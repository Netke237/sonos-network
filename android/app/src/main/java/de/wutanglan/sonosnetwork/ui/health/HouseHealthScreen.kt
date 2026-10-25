package de.wutanglan.sonosnetwork.ui.health

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectTapGestures
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
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.time.Duration
import java.time.Instant
import de.wutanglan.sonosnetwork.data.models.FloorMatrixItemDto
import de.wutanglan.sonosnetwork.data.models.RoomMatrixItemDto
import de.wutanglan.sonosnetwork.data.models.TopologyGraphDto

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
                Column(modifier = Modifier.weight(1f)) {
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
                    Spacer(modifier = Modifier.height(4.dp))
                    val sonosFreshness = overview?.latest_sonos_captured_at?.let { formatRelativeTime(it) } ?: "just now"
                    Surface(
                        color = Color.White.copy(alpha = 0.85f),
                        shape = RoundedCornerShape(4.dp),
                        border = BorderStroke(0.5.dp, Color.LightGray)
                    ) {
                        Text(
                            text = "🕒 Sonos telemetry: $sonosFreshness",
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Medium,
                            color = Color(0xFF333333),
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                        )
                    }
                }
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    IconButton(
                        onClick = { viewModel.loadHealthData() },
                        modifier = Modifier.size(36.dp)
                    ) {
                        Text("🔄", fontSize = 16.sp)
                    }
                    HealthGradeBadge(overallGrade)
                }
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
                topology = state.topology,
                onNodeClick = { slug -> viewModel.openRoomDiagnostic(slug) }
            )
        }
    }

    // Room 3-Pillar Diagnostic Sheet
    if (state.isDiagnosticSheetOpen) {
        RoomDiagnosticModalSheet(
            diagnostic = state.selectedRoomDiagnostic,
            isLoading = state.isLoadingRoomDiagnostic,
            isRemediating = state.isRemediating,
            remediationMessage = state.remediationMessage,
            onFlushGhostGroups = { ips -> viewModel.flushGhostGroupsForIps(ips) },
            onDeepReset = { ips -> viewModel.deepResetForIps(ips) },
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
        Column(modifier = Modifier.padding(10.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
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

            // 3-Pillar Status Badges
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(6.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                PillarBadge(label = "Wi-Fi", grade = room.wifi_health_grade)
                if (room.devices.any { it.device_role == "SONOS_PLAYER" }) {
                    PillarBadge(label = "Sonos", grade = room.sonos_health_grade)
                }
                if (room.switch_ports.isNotEmpty()) {
                    PillarBadge(label = "VLAN 10", grade = room.wired_health_grade)
                }
            }

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
fun PillarBadge(label: String, grade: String) {
    val (bg, fg) = when (grade.uppercase()) {
        "EXCELLENT" -> Color(0xFFE8F5E9) to Color(0xFF2E7D32)
        "GOOD" -> Color(0xFFE3F2FD) to Color(0xFF1565C0)
        "MARGINAL" -> Color(0xFFFFF3E0) to Color(0xFFE65100)
        else -> Color(0xFFFFEBEE) to Color(0xFFC62828)
    }

    val icon = when (label) {
        "Wi-Fi" -> "📶"
        "Sonos" -> "🔊"
        else -> "🔌"
    }

    Surface(
        color = bg,
        shape = RoundedCornerShape(4.dp),
        border = BorderStroke(0.5.dp, fg.copy(alpha = 0.35f))
    ) {
        Text(
            text = "$icon $label: ${grade.uppercase()}",
            color = fg,
            fontWeight = FontWeight.SemiBold,
            fontSize = 10.sp,
            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
        )
    }
}

private fun formatRelativeTime(isoString: String?): String {
    if (isoString.isNullOrBlank()) return "just now"
    return try {
        val instant = Instant.parse(isoString)
        val now = Instant.now()
        val seconds = Duration.between(instant, now).seconds
        when {
            seconds < 5 -> "just now"
            seconds < 60 -> "${seconds}s ago"
            seconds < 3600 -> "${seconds / 60}m ago"
            seconds < 86400 -> "${seconds / 3600}h ago"
            else -> "${seconds / 86400}d ago"
        }
    } catch (e: Exception) {
        "recently"
    }
}

@Composable
fun TopologyCanvasView(
    topology: TopologyGraphDto?,
    onNodeClick: (String) -> Unit
) {
    var scale by remember { mutableFloatStateOf(1f) }
    var offset by remember { mutableStateOf(Offset.Zero) }

    val nodes = topology?.nodes ?: emptyList()
    val edges = topology?.edges ?: emptyList()

    // Calculate node base layout offsets
    val nodeBaseCoords = remember(topology) {
        if (nodes.isEmpty()) return@remember emptyMap<String, Offset>()

        val hasNonZeroCoords = nodes.any { (it.pos_x > 0f || it.x > 0f) && (it.pos_y > 0f || it.y > 0f) }
        if (hasNonZeroCoords) {
            val minX = nodes.map { if (it.pos_x > 0f) it.pos_x else it.x }.minOrNull() ?: 0f
            val maxX = nodes.map { if (it.pos_x > 0f) it.pos_x else it.x }.maxOrNull() ?: 1000f
            val minY = nodes.map { if (it.pos_y > 0f) it.pos_y else it.y }.minOrNull() ?: 0f
            val maxY = nodes.map { if (it.pos_y > 0f) it.pos_y else it.y }.maxOrNull() ?: 800f
            val spanX = (maxX - minX).coerceAtLeast(100f)
            val spanY = (maxY - minY).coerceAtLeast(100f)

            nodes.associate { n ->
                val nx = if (n.pos_x > 0f) n.pos_x else n.x
                val ny = if (n.pos_y > 0f) n.pos_y else n.y
                val normX = ((nx - minX) / spanX - 0.5f) * 650f
                val normY = ((ny - minY) / spanY - 0.5f) * 550f
                n.slug to Offset(normX, normY)
            }
        } else {
            // Radial layout fallback
            val rootNode = nodes.find { it.is_stp_root || it.device_role == "ROUTER" }
            val otherNodes = nodes.filter { it != rootNode }
            val map = mutableMapOf<String, Offset>()
            if (rootNode != null) {
                map[rootNode.slug] = Offset(0f, -140f)
            }
            val count = otherNodes.size.coerceAtLeast(1)
            otherNodes.forEachIndexed { idx, n ->
                val angle = (2.0 * Math.PI * idx / count).toFloat()
                val rx = kotlin.math.cos(angle) * 220f
                val ry = kotlin.math.sin(angle) * 160f + 30f
                map[n.slug] = Offset(rx, ry)
            }
            map
        }
    }

    val textPaint = remember {
        android.graphics.Paint().apply {
            color = android.graphics.Color.WHITE
            textAlign = android.graphics.Paint.Align.CENTER
            isAntiAlias = true
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF181818), shape = RoundedCornerShape(12.dp))
            .pointerInput(topology, scale, offset) {
                detectTapGestures { tapOffset ->
                    val w = size.width
                    val h = size.height
                    val cx = (w / 2) + offset.x
                    val cy = (h / 2) + offset.y

                    val tappedNode = nodes.find { node ->
                        val base = nodeBaseCoords[node.slug] ?: Offset.Zero
                        val screenPos = Offset(cx + (base.x * scale), cy + (base.y * scale))
                        val distance = (tapOffset - screenPos).getDistance()
                        distance <= 28f * scale
                    }
                    if (tappedNode != null) {
                        onNodeClick(tappedNode.room_slug ?: tappedNode.slug)
                    }
                }
            }
            .pointerInput(Unit) {
                detectTransformGestures { _, pan, zoom, _ ->
                    scale = (scale * zoom).coerceIn(0.4f, 3.5f)
                    offset += pan
                }
            }
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val w = size.width
            val h = size.height
            val cx = (w / 2) + offset.x
            val cy = (h / 2) + offset.y

            if (nodes.isEmpty()) {
                return@Canvas
            }

            // 1. Draw directed edges
            edges.forEach { edge ->
                val sBase = nodeBaseCoords[edge.source_slug]
                    ?: nodeBaseCoords[edge.source]
                    ?: nodeBaseCoords[edge.source_id]
                val tBase = nodeBaseCoords[edge.target_slug]
                    ?: nodeBaseCoords[edge.target]
                    ?: nodeBaseCoords[edge.target_id]

                if (sBase != null && tBase != null) {
                    val sScreen = Offset(cx + (sBase.x * scale), cy + (sBase.y * scale))
                    val tScreen = Offset(cx + (tBase.x * scale), cy + (tBase.y * scale))

                    val edgeColor = when {
                        edge.layer == "WIRED_LAN" -> Color(0xFF4CAF50)
                        edge.layer == "WIFI_INFRA" -> Color(0xFF2196F3)
                        !edge.is_forwarding || edge.stp_state == "BLOCKING" || edge.line_style == "dashed" -> Color(0xFFFF9800)
                        edge.stp_state == "HT_BOND" -> Color(0xFF00BCD4)
                        else -> Color(0xFF9C27B0)
                    }

                    val isDashed = !edge.is_forwarding || edge.line_style == "dashed" || edge.stp_state == "BLOCKING"
                    val pathEffect = if (isDashed) {
                        PathEffect.dashPathEffect(floatArrayOf(10f * scale, 10f * scale), 0f)
                    } else {
                        null
                    }

                    drawLine(
                        color = edgeColor,
                        start = sScreen,
                        end = tScreen,
                        strokeWidth = (if (edge.is_forwarding) 2.5f else 1.8f) * scale,
                        pathEffect = pathEffect
                    )
                }
            }

            // 2. Draw nodes
            nodes.forEach { node ->
                val base = nodeBaseCoords[node.slug] ?: Offset.Zero
                val screenPos = Offset(cx + (base.x * scale), cy + (base.y * scale))
                val radius = (if (node.is_stp_root) 18f else 13f) * scale

                val nodeColor = when {
                    node.is_stp_root -> Color(0xFFFFD700)
                    node.device_role == "ROUTER" -> Color(0xFFE91E63)
                    node.device_role == "SWITCH" -> Color(0xFF607D8B)
                    node.device_role == "WIFI_AP" -> Color(0xFF2196F3)
                    node.health_grade == "EXCELLENT" || node.health_grade == "GOOD" -> Color(0xFF4CAF50)
                    node.health_grade == "MARGINAL" -> Color(0xFFFF9800)
                    else -> Color(0xFFF44336)
                }

                // Inner circle
                drawCircle(
                    color = nodeColor,
                    radius = radius,
                    center = screenPos
                )

                // STP Root Bridge halo
                if (node.is_stp_root) {
                    drawCircle(
                        color = Color(0xFFFFD700),
                        radius = radius + 6f * scale,
                        center = screenPos,
                        style = Stroke(width = 2.5f * scale)
                    )
                }

                // Ghost Group halo
                if (node.is_ghost_group) {
                    drawCircle(
                        color = Color(0xFFF44336),
                        radius = radius + 6f * scale,
                        center = screenPos,
                        style = Stroke(width = 2.5f * scale)
                    )
                }

                // Node label text
                textPaint.textSize = (9f * scale * density).coerceIn(16f, 36f)
                drawContext.canvas.nativeCanvas.drawText(
                    node.name,
                    screenPos.x,
                    screenPos.y + (radius + 12f * scale),
                    textPaint
                )
            }
        }

        Column(
            modifier = Modifier
                .align(Alignment.BottomStart)
                .padding(12.dp)
        ) {
            Text(
                text = "Vector Topology Graph (${nodes.size} nodes, ${edges.size} edges)",
                color = Color.White,
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = "Green: Wired LAN  |  Blue: Wi-Fi  |  Purple: SonosNet  |  Dashed: STP Blocked",
                color = Color.LightGray,
                fontSize = 11.sp
            )
            Text(
                text = "Pinch to zoom, drag to pan. Tap node to inspect 3-pillar diagnostics.",
                color = Color.Gray,
                fontSize = 10.sp
            )
        }
    }
}
