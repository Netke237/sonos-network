package de.wutanglan.sonosnetwork.data.queue

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

class FakeSurveyQueueManager : SurveyQueuePort {

    private val queue = mutableListOf<PendingSurveyEntity>()
    private var nextId = 1L
    private val _pendingCount = MutableStateFlow(0)

    override suspend fun enqueueSurvey(survey: PendingSurveyEntity): Long {
        val assignedId = if (survey.id > 0) survey.id else nextId++
        val entry = survey.copy(id = assignedId)
        queue.add(entry)
        refreshCount()
        return assignedId
    }

    override suspend fun getPendingSurveys(): List<PendingSurveyEntity> {
        return queue.filter { it.sync_status == "PENDING" }.sortedBy { it.id }
    }

    override suspend fun markSurveySynced(id: Long) {
        val index = queue.indexOfFirst { it.id == id }
        if (index != -1) {
            queue[index] = queue[index].copy(sync_status = "SYNCED")
            refreshCount()
        }
    }

    override suspend fun getPendingCount(): Flow<Int> = _pendingCount.asStateFlow()

    override suspend fun purgeSyncedSurveys() {
        queue.removeAll { it.sync_status == "SYNCED" }
        refreshCount()
    }

    private fun refreshCount() {
        _pendingCount.value = queue.count { it.sync_status == "PENDING" }
    }
}
