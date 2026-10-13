package de.wutanglan.sonosnetwork.data.queue

import kotlinx.coroutines.flow.Flow

interface SurveyQueuePort {
    suspend fun enqueueSurvey(survey: PendingSurveyEntity): Long
    suspend fun getPendingSurveys(): List<PendingSurveyEntity>
    suspend fun markSurveySynced(id: Long)
    suspend fun getPendingCount(): Flow<Int>
    suspend fun purgeSyncedSurveys()
}
