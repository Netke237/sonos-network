package de.wutanglan.sonosnetwork.data.network

import de.wutanglan.sonosnetwork.data.connectivity.ConnectivityPort
import de.wutanglan.sonosnetwork.data.models.*
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException
import java.util.concurrent.TimeUnit
import kotlin.coroutines.resume

class RealSonosNetworkClient(
    private val connectivityPort: ConnectivityPort,
    private val okHttpClient: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(5, TimeUnit.SECONDS)
        .readTimeout(10, TimeUnit.SECONDS)
        .writeTimeout(10, TimeUnit.SECONDS)
        .build(),
    private val json: Json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        encodeDefaults = true
    }
) : SonosNetworkClientPort {

    private val jsonMediaType = "application/json; charset=utf-8".toMediaType()

    private fun baseUrl(): String = connectivityPort.getActiveEndpointUrl().trimEnd('/')

    private suspend inline fun <reified T> executeGet(url: String): Result<T> {
        val request = Request.Builder().url(url).get().build()
        return executeRequest(request)
    }

    private suspend inline fun <reified T> executePost(url: String, requestBody: RequestBody): Result<T> {
        val request = Request.Builder().url(url).post(requestBody).build()
        return executeRequest(request)
    }

    private suspend inline fun <reified T> executeRequest(request: Request): Result<T> {
        return suspendCancellableCoroutine { continuation ->
            val call = okHttpClient.newCall(request)
            continuation.invokeOnCancellation { call.cancel() }

            call.enqueue(object : Callback {
                override fun onFailure(call: Call, e: IOException) {
                    if (continuation.isActive) {
                        continuation.resume(Result.failure(e))
                    }
                }

                override fun onResponse(call: Call, response: Response) {
                    response.use { res ->
                        if (!res.isSuccessful) {
                            val msg = "HTTP ${res.code}: ${res.message}"
                            if (continuation.isActive) {
                                continuation.resume(Result.failure(IOException(msg)))
                            }
                            return
                        }

                        val bodyStr = res.body?.string()
                        if (bodyStr.isNullOrBlank()) {
                            if (continuation.isActive) {
                                continuation.resume(Result.failure(IOException("Empty response body")))
                            }
                            return
                        }

                        try {
                            val parsed: T = json.decodeFromString(bodyStr)
                            if (continuation.isActive) {
                                continuation.resume(Result.success(parsed))
                            }
                        } catch (e: Exception) {
                            if (continuation.isActive) {
                                continuation.resume(Result.failure(e))
                            }
                        }
                    }
                }
            })
        }
    }

    override suspend fun getOverview(): Result<HouseOverviewDto> {
        val url = "${baseUrl()}/api/overview"
        return executeGet(url)
    }

    override suspend fun getTopology(layer: String?): Result<TopologyGraphDto> {
        val url = if (layer != null) {
            "${baseUrl()}/api/topology?layer=$layer"
        } else {
            "${baseUrl()}/api/topology"
        }
        return executeGet(url)
    }

    override suspend fun getHouseDiagnostics(): Result<HouseDiagnosticReportDto> {
        val url = "${baseUrl()}/api/diagnostics"
        return executeGet(url)
    }

    override suspend fun getRoomDiagnostics(roomSlug: String): Result<RoomDiagnosticSummaryDto> {
        val url = "${baseUrl()}/api/rooms/$roomSlug/diagnostics"
        return executeGet(url)
    }

    override suspend fun getRoomSurveys(roomSlug: String): Result<List<WiFiRoomSurveyDto>> {
        val url = "${baseUrl()}/api/rooms/$roomSlug/surveys"
        return executeGet(url)
    }

    override suspend fun submitRoomSurvey(
        roomSlug: String,
        payload: RoomSurveyInputDto
    ): Result<WiFiRoomSurveyDto> {
        val url = "${baseUrl()}/api/rooms/$roomSlug/surveys"
        val bodyJson = json.encodeToString(payload)
        val body = bodyJson.toRequestBody(jsonMediaType)
        return executePost(url, body)
    }

    override suspend fun flushGhostGroups(zoneIps: List<String>?): Result<GhostFlushResultDto> {
        val url = "${baseUrl()}/api/actions/flush-ghost-groups"
        val payloadObj = mapOf("zone_ips" to zoneIps)
        val bodyJson = json.encodeToString(payloadObj)
        val body = bodyJson.toRequestBody(jsonMediaType)
        return executePost(url, body)
    }

    override suspend fun pollNow(): Result<HouseholdSonosSnapshotDto> {
        val url = "${baseUrl()}/api/actions/poll-now"
        val emptyBody = "{}".toRequestBody(jsonMediaType)
        return executePost(url, emptyBody)
    }

    override suspend fun pingSweep(): Result<PingSweepResultDto> {
        val url = "${baseUrl()}/api/actions/ping-sweep"
        val emptyBody = "{}".toRequestBody(jsonMediaType)
        return executePost(url, emptyBody)
    }

    override fun streamLiveRf(roomSlug: String): Flow<LiveRfFrameDto> = callbackFlow {
        val httpUrl = baseUrl()
        val wsUrl = if (httpUrl.startsWith("https://")) {
            "wss://${httpUrl.removePrefix("https://")}/api/ws/live-rf?room_slug=$roomSlug"
        } else {
            "ws://${httpUrl.removePrefix("http://")}/api/ws/live-rf?room_slug=$roomSlug"
        }

        val request = Request.Builder().url(wsUrl).build()
        val webSocket = okHttpClient.newWebSocket(request, object : WebSocketListener() {
            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val frame: LiveRfFrameDto = json.decodeFromString(text)
                    trySend(frame)
                } catch (_: Exception) {
                }
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                close(t)
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                close()
            }
        })

        awaitClose {
            webSocket.close(1000, "Flow closed")
        }
    }
}
