from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Iterable
from uuid import UUID, uuid4

from .models import AccessEvent, FeedbackEvent, FeedbackType, MemoryRecord, MemoryStatus, SearchResult
from .policy import cosine_similarity, decay_score, feedback_weight, lexical_score, lifecycle_state


class TenantAccessError(PermissionError):
    """Raised when a write tries to use an empty tenant boundary."""


class InMemoryMemoryRepository:
    """Deterministic repository used by the POC tests and local examples."""

    def __init__(self) -> None:
        self.records: dict[UUID, MemoryRecord] = {}
        self.access_events: list[AccessEvent] = []
        self.feedback_events: dict[str, FeedbackEvent] = {}
        self._lineage_versions: defaultdict[UUID, list[UUID]] = defaultdict(list)

    def write(self, record: MemoryRecord) -> MemoryRecord:
        if not record.tenant_id.strip():
            raise TenantAccessError("tenant_id is required")
        if record.supersedes is not None:
            previous = self.records.get(record.supersedes)
            if previous is None or previous.tenant_id != record.tenant_id:
                raise TenantAccessError("superseded record is outside the tenant")
            if previous.superseded_by is not None:
                raise ValueError("record has already been superseded")
            record.version = previous.version + 1
            previous.superseded_by = record.memory_id
            self._lineage_versions[previous.memory_id].append(record.memory_id)
        self.records[record.memory_id] = record
        return record

    def get(self, tenant_id: str, memory_id: UUID, include_history: bool = False) -> MemoryRecord | None:
        record = self.records.get(memory_id)
        if record is None or record.tenant_id != tenant_id:
            return None
        if not include_history and record.superseded_by is not None:
            return None
        return record

    def search(
        self,
        tenant_id: str,
        subject_id: str,
        scope: str,
        query: str,
        now: datetime,
        query_embedding: tuple[float, ...] | None = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        candidates: list[SearchResult] = []
        for record in self.records.values():
            if record.tenant_id != tenant_id or record.subject_id != subject_id or record.scope != scope:
                continue
            if record.status == MemoryStatus.TOMBSTONED or record.superseded_by is not None:
                continue
            lexical = lexical_score(query, record.content)
            semantic = 0.0
            if query_embedding is not None and record.embedding is not None:
                semantic = max(0.0, cosine_similarity(query_embedding, record.embedding))
            decay = decay_score(record, now)
            lifecycle = lifecycle_state(record, now)
            feedback = feedback_weight(record.feedback_score)
            score = (0.45 * lexical) + (0.30 * semantic) + (0.15 * decay) + (0.10 * record.confidence) + (0.05 * feedback)
            if query.strip() and lexical == 0.0 and semantic == 0.0:
                continue
            candidates.append(SearchResult(
                memory=record,
                score=score,
                lexical_score=lexical,
                semantic_score=semantic,
                decay_score=decay,
                feedback_score=feedback,
                activation_reason=f"tenant and scope matched; lifecycle={lifecycle.value}",
            ))
        candidates.sort(key=lambda item: (item.score, item.memory.created_at), reverse=True)
        return candidates[:limit]

    def record_access(self, tenant_id: str, memory_id: UUID, service: str, reason: str, occurred_at: datetime) -> AccessEvent:
        record = self.get(tenant_id, memory_id, include_history=True)
        if record is None or record.status == MemoryStatus.TOMBSTONED:
            raise KeyError("memory not found")
        record.last_activated_at = occurred_at
        record.activation_count += 1
        record.status = MemoryStatus.ACTIVE
        event = AccessEvent(uuid4(), memory_id, tenant_id, service, occurred_at, reason)
        self.access_events.append(event)
        return event

    def add_feedback(self, event: FeedbackEvent) -> FeedbackEvent:
        record = self.get(event.tenant_id, event.memory_id, include_history=True)
        if record is None:
            raise KeyError("memory not found")
        if event.feedback_id in self.feedback_events:
            return self.feedback_events[event.feedback_id]
        adjustment = {
            FeedbackType.ACCEPTED: 0.20,
            FeedbackType.USEFUL: 0.10,
            FeedbackType.REJECTED: -0.25,
            FeedbackType.CORRECTED: -0.15,
        }[event.feedback_type]
        record.feedback_score = feedback_weight(record.feedback_score + adjustment)
        self.feedback_events[event.feedback_id] = event
        return event

    def restore(self, tenant_id: str, memory_id: UUID, now: datetime, service: str) -> MemoryRecord:
        record = self.get(tenant_id, memory_id, include_history=True)
        if record is None:
            raise KeyError("memory not found")
        if record.status == MemoryStatus.TOMBSTONED:
            raise ValueError("tombstoned memory cannot be restored")
        record.status = MemoryStatus.ACTIVE
        self.record_access(tenant_id, memory_id, service, "explicit restore", now)
        return record

    def history(self, tenant_id: str, memory_id: UUID) -> list[MemoryRecord]:
        record = self.get(tenant_id, memory_id, include_history=True)
        if record is None:
            return []
        root = record
        while root.supersedes is not None:
            parent = self.records.get(root.supersedes)
            if parent is None:
                break
            root = parent
        result = [candidate for candidate in self.records.values() if candidate.tenant_id == tenant_id and (candidate.memory_id == root.memory_id or candidate.supersedes is not None and self._belongs_to(root.memory_id, candidate.memory_id))]
        result.sort(key=lambda item: item.version)
        return result

    def _belongs_to(self, root_id: UUID, candidate_id: UUID) -> bool:
        current = self.records.get(candidate_id)
        while current is not None and current.supersedes is not None:
            if current.supersedes == root_id:
                return True
            current = self.records.get(current.supersedes)
        return False
