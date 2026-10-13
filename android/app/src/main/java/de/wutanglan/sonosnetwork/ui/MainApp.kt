package de.wutanglan.sonosnetwork.ui

import androidx.compose.foundation.layout.padding
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import de.wutanglan.sonosnetwork.ui.actions.ActionsScreen
import de.wutanglan.sonosnetwork.ui.actions.ActionsViewModel
import de.wutanglan.sonosnetwork.ui.health.HouseHealthScreen
import de.wutanglan.sonosnetwork.ui.health.HouseHealthViewModel
import de.wutanglan.sonosnetwork.ui.walkthrough.WalkthroughScreen
import de.wutanglan.sonosnetwork.ui.walkthrough.WalkthroughViewModel

enum class NavigationTab(val title: String, val icon: String) {
    WALKTHROUGH("Walkthrough", "📍"),
    HOUSE_HEALTH("House Health", "🏠"),
    ACTIONS("Actions & Hub", "⚡")
}

@Composable
fun MainApp(
    walkthroughViewModel: WalkthroughViewModel,
    houseHealthViewModel: HouseHealthViewModel,
    actionsViewModel: ActionsViewModel,
    modifier: Modifier = Modifier
) {
    var selectedTab by remember { mutableStateOf(NavigationTab.WALKTHROUGH) }

    Scaffold(
        modifier = modifier,
        bottomBar = {
            NavigationBar {
                NavigationTab.values().forEach { tab ->
                    NavigationBarItem(
                        selected = selectedTab == tab,
                        onClick = { selectedTab = tab },
                        icon = { Text(tab.icon) },
                        label = { Text(tab.title) }
                    )
                }
            }
        }
    ) { innerPadding ->
        when (selectedTab) {
            NavigationTab.WALKTHROUGH -> WalkthroughScreen(
                viewModel = walkthroughViewModel,
                modifier = Modifier.padding(innerPadding)
            )
            NavigationTab.HOUSE_HEALTH -> HouseHealthScreen(
                viewModel = houseHealthViewModel,
                modifier = Modifier.padding(innerPadding)
            )
            NavigationTab.ACTIONS -> ActionsScreen(
                viewModel = actionsViewModel,
                modifier = Modifier.padding(innerPadding)
            )
        }
    }
}
