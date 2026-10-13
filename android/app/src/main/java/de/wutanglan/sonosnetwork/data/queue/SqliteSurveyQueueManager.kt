package de.wutanglan.sonosnetwork.data.queue

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.withContext

class SqliteSurveyQueueManager(
    context: Context,
    databaseName: String = DATABASE_NAME
) : SQLiteOpenHelper(context, databaseName, null, DATABASE_VERSION), SurveyQueuePort {

    companion object {
        const val DATABASE_NAME = "sonos_survey_cache.db"
        const val DATABASE_VERSION = 1
        const val TABLE_PENDING_SURVEYS = "pending_surveys"

        const val COL_ID = "id"
        const val COL_ROOM_SLUG = "room_slug"
        const val COL_TIMESTAMP = "timestamp"
        const val COL_LABEL = "label"
        const val COL_TRIGGER_MODE = "trigger_mode"
        const val COL_CONNECTED_BSSID = "connected_bssid"
        const val COL_CONNECTED_SSID = "connected_ssid"
        const val COL_LINK_SPEED_MBPS = "link_speed_mbps"
        const val COL_FREQUENCY_MHZ = "frequency_mhz"
        const val COL_READINGS_JSON = "readings_json"
        const val COL_SYNC_STATUS = "sync_status"
    }

    private val _pendingCount = MutableStateFlow(0)

    init {
        refreshPendingCount()
    }

    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL(
            """
            CREATE TABLE IF NOT EXISTS $TABLE_PENDING_SURVEYS (
                $COL_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                $COL_ROOM_SLUG TEXT NOT NULL,
                $COL_TIMESTAMP TEXT NOT NULL,
                $COL_LABEL TEXT NOT NULL,
                $COL_TRIGGER_MODE TEXT NOT NULL DEFAULT 'STORE_AND_FORWARD',
                $COL_CONNECTED_BSSID TEXT,
                $COL_CONNECTED_SSID TEXT,
                $COL_LINK_SPEED_MBPS INTEGER,
                $COL_FREQUENCY_MHZ INTEGER,
                $COL_READINGS_JSON TEXT NOT NULL,
                $COL_SYNC_STATUS TEXT NOT NULL DEFAULT 'PENDING'
            )
            """.trimIndent()
        )
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        db.execSQL("DROP TABLE IF EXISTS $TABLE_PENDING_SURVEYS")
        onCreate(db)
    }

    private fun refreshPendingCount() {
        try {
            val db = readableDatabase
            val cursor = db.rawQuery(
                "SELECT COUNT(*) FROM $TABLE_PENDING_SURVEYS WHERE $COL_SYNC_STATUS = 'PENDING'",
                null
            )
            var count = 0
            if (cursor.moveToFirst()) {
                count = cursor.getInt(0)
            }
            cursor.close()
            _pendingCount.value = count
        } catch (_: Exception) {
            _pendingCount.value = 0
        }
    }

    override suspend fun enqueueSurvey(survey: PendingSurveyEntity): Long = withContext(Dispatchers.IO) {
        val db = writableDatabase
        val values = ContentValues().apply {
            put(COL_ROOM_SLUG, survey.room_slug)
            put(COL_TIMESTAMP, survey.timestamp)
            put(COL_LABEL, survey.label)
            put(COL_TRIGGER_MODE, survey.trigger_mode)
            put(COL_CONNECTED_BSSID, survey.connected_bssid)
            put(COL_CONNECTED_SSID, survey.connected_ssid)
            if (survey.link_speed_mbps != null) put(COL_LINK_SPEED_MBPS, survey.link_speed_mbps) else putNull(COL_LINK_SPEED_MBPS)
            if (survey.frequency_mhz != null) put(COL_FREQUENCY_MHZ, survey.frequency_mhz) else putNull(COL_FREQUENCY_MHZ)
            put(COL_READINGS_JSON, survey.readings_json)
            put(COL_SYNC_STATUS, survey.sync_status)
        }
        val id = db.insert(TABLE_PENDING_SURVEYS, null, values)
        refreshPendingCount()
        id
    }

    override suspend fun getPendingSurveys(): List<PendingSurveyEntity> = withContext(Dispatchers.IO) {
        val list = mutableListOf<PendingSurveyEntity>()
        val db = readableDatabase
        val cursor = db.query(
            TABLE_PENDING_SURVEYS,
            null,
            "$COL_SYNC_STATUS = ?",
            arrayOf("PENDING"),
            null,
            null,
            "$COL_ID ASC"
        )
        while (cursor.moveToNext()) {
            val id = cursor.getLong(cursor.getColumnIndexOrThrow(COL_ID))
            val roomSlug = cursor.getString(cursor.getColumnIndexOrThrow(COL_ROOM_SLUG))
            val timestamp = cursor.getString(cursor.getColumnIndexOrThrow(COL_TIMESTAMP))
            val label = cursor.getString(cursor.getColumnIndexOrThrow(COL_LABEL))
            val triggerMode = cursor.getString(cursor.getColumnIndexOrThrow(COL_TRIGGER_MODE))
            val connectedBssid = cursor.getString(cursor.getColumnIndexOrThrow(COL_CONNECTED_BSSID))
            val connectedSsid = cursor.getString(cursor.getColumnIndexOrThrow(COL_CONNECTED_SSID))
            val linkSpeed = if (cursor.isNull(cursor.getColumnIndexOrThrow(COL_LINK_SPEED_MBPS))) null
            else cursor.getInt(cursor.getColumnIndexOrThrow(COL_LINK_SPEED_MBPS))
            val freq = if (cursor.isNull(cursor.getColumnIndexOrThrow(COL_FREQUENCY_MHZ))) null
            else cursor.getInt(cursor.getColumnIndexOrThrow(COL_FREQUENCY_MHZ))
            val readingsJson = cursor.getString(cursor.getColumnIndexOrThrow(COL_READINGS_JSON))
            val syncStatus = cursor.getString(cursor.getColumnIndexOrThrow(COL_SYNC_STATUS))

            list.add(
                PendingSurveyEntity(
                    id = id,
                    room_slug = roomSlug,
                    timestamp = timestamp,
                    label = label,
                    trigger_mode = triggerMode,
                    connected_bssid = connectedBssid,
                    connected_ssid = connectedSsid,
                    link_speed_mbps = linkSpeed,
                    frequency_mhz = freq,
                    readings_json = readingsJson,
                    sync_status = syncStatus
                )
            )
        }
        cursor.close()
        list
    }

    override suspend fun markSurveySynced(id: Long): Unit = withContext(Dispatchers.IO) {
        val db = writableDatabase
        val values = ContentValues().apply {
            put(COL_SYNC_STATUS, "SYNCED")
        }
        db.update(TABLE_PENDING_SURVEYS, values, "$COL_ID = ?", arrayOf(id.toString()))
        refreshPendingCount()
    }

    override suspend fun getPendingCount(): Flow<Int> = _pendingCount.asStateFlow()

    override suspend fun purgeSyncedSurveys(): Unit = withContext(Dispatchers.IO) {
        val db = writableDatabase
        db.delete(TABLE_PENDING_SURVEYS, "$COL_SYNC_STATUS = ?", arrayOf("SYNCED"))
        refreshPendingCount()
    }
}
