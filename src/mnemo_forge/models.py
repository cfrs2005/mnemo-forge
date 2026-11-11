from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MemoryStatus(StrEnum):
    ACTIVE = "active"
    COOLING = "cooling"
    DORMANT = "dormant"
    TOMBSTONED = "tombstoned"


class FeedbackType(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CORRECTED = "corrected"
    USEFUL = "useful"


@dataclass(slots=True)
class MemoryRecord:
    tenant_id: str
    subject_id: str
    scope: str
    kind: str
    content: str
    source_event_id: str
    source_service: str
    created_at: datetime = field(default_factory=utc_now)
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    confidence: float = 1.0
    status: MemoryStatus = MemoryStatus.ACTIVE
    version: int = 1
    supersedes: UUID | None = None
    memory_id: UUID = field(default_factory=uuid4)
    superseded_by: UUID | None = None
    last_activated_at: datetime | None = None
    activation_count: int = 0
    feedback_score: float = 0.0
    embedding: tuple[float, ...] | None = None

    def __post_init__(self) -> None:
        if self.valid_from is None:
            self.valid_from = self.created_at
        if self.last_activated_at is None:
            self.last_activated_at = self.created_at
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class SourceEvent:
    event_id: str
    tenant_id: str
    source_service: str
    event_type: str
    payload: dict[str, Any]
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class AccessEvent:
    event_id: UUID
    memory_id: UUID
    tenant_id: str
    service: str
    occurred_at: datetime
    reason: str


@dataclass(frozen=True, slots=True)
class FeedbackEvent:
    feedback_id: str
    memory_id: UUID
    tenant_id: str
    feedback_type: FeedbackType
    service: str
    created_at: datetime
    note: str | None = None


@dataclass(frozen=True, slots=True)
class SearchResult:
    memory: MemoryRecord
    score: float
    lexical_score: float
    semantic_score: float
    decay_score: float
    feedback_score: float
    activation_reason: str
