from __future__ import annotations

from datetime import datetime
from uuid import UUID

from .models import FeedbackEvent, FeedbackType, MemoryRecord, SearchResult
from .repository import InMemoryMemoryRepository


class MemoryService:
    """Application policy layer shared by every transport adapter."""

    def __init__(self, repository: InMemoryMemoryRepository) -> None:
        self.repository = repository

    def write(self, **kwargs: object) -> MemoryRecord:
        return self.repository.write(MemoryRecord(**kwargs))

    def search(self, tenant_id: str, subject_id: str, scope: str, query: str, now: datetime, query_embedding: tuple[float, ...] | None = None, limit: int = 10) -> list[SearchResult]:
        return self.repository.search(tenant_id, subject_id, scope, query, now, query_embedding, limit)

    def feedback(self, tenant_id: str, memory_id: UUID, feedback_id: str, feedback_type: FeedbackType, service: str, created_at: datetime, note: str | None = None) -> FeedbackEvent:
        return self.repository.add_feedback(FeedbackEvent(feedback_id, memory_id, tenant_id, feedback_type, service, created_at, note))

    def restore(self, tenant_id: str, memory_id: UUID, now: datetime, service: str) -> MemoryRecord:
        return self.repository.restore(tenant_id, memory_id, now, service)
