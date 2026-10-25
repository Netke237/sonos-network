package de.wutanglan.sonosnetwork

import android.Manifest
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import de.wutanglan.sonosnetwork.data.connectivity.RealConnectivityManager
import de.wutanglan.sonosnetwork.data.network.RealSonosNetworkClient
import de.wutanglan.sonosnetwork.data.queue.AutoSyncCoordinator
import de.wutanglan.sonosnetwork.data.queue.SqliteSurveyQueueManager
import de.wutanglan.sonosnetwork.data.wifi.RealWifiScanner
import de.wutanglan.sonosnetwork.theme.SonosNetworkTheme
import de.wutanglan.sonosnetwork.ui.MainApp
import de.wutanglan.sonosnetwork.ui.actions.ActionsViewModel
import de.wutanglan.sonosnetwork.ui.health.HouseHealthViewModel
import de.wutanglan.sonosnetwork.ui.walkthrough.WalkthroughViewModel

class MainActivity : ComponentActivity() {

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { _ ->
        // Permissions will be checked by RealWifiScanner dynamically
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val permissions = mutableListOf(
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION
        )
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions.add(Manifest.permission.NEARBY_WIFI_DEVICES)
        }
        requestPermissionLauncher.launch(permissions.toTypedArray())

        val connectivityManager = RealConnectivityManager(this)
        val networkClient = RealSonosNetworkClient(connectivityManager)
        val wifiScanner = RealWifiScanner(this)
        val surveyQueue = SqliteSurveyQueueManager(this)
        val autoSyncCoordinator = AutoSyncCoordinator(surveyQueue, networkClient, connectivityManager)

        val walkthroughViewModel = WalkthroughViewModel(
            wifiScanner = wifiScanner,
            surveyQueue = surveyQueue,
            networkClient = networkClient,
            connectivityPort = connectivityManager,
            autoSyncCoordinator = autoSyncCoordinator
        )

        val houseHealthViewModel = HouseHealthViewModel(networkClient)
        val actionsViewModel = ActionsViewModel(networkClient)

        setContent {
            SonosNetworkTheme {
                Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
                    MainApp(
                        walkthroughViewModel = walkthroughViewModel,
                        houseHealthViewModel = houseHealthViewModel,
                        actionsViewModel = actionsViewModel
                    )
                }
            }
        }
    }
}
