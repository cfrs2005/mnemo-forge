from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Iterable

from .models import MemoryRecord, MemoryStatus


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def age_days(record: MemoryRecord, now: datetime) -> float:
    anchor = record.last_activated_at or record.created_at
    elapsed = _utc(now) - _utc(anchor)
    return max(0.0, elapsed.total_seconds() / 86_400)


def decay_score(record: MemoryRecord, now: datetime, half_life_days: float = 30.0) -> float:
    if half_life_days <= 0:
        raise ValueError("half_life_days must be positive")
    return math.exp(-math.log(2) * age_days(record, now) / half_life_days)


def lifecycle_state(record: MemoryRecord, now: datetime) -> MemoryStatus:
    if record.status == MemoryStatus.TOMBSTONED:
        return MemoryStatus.TOMBSTONED
    age = age_days(record, now)
    if age >= 180:
        return MemoryStatus.DORMANT
    if age >= 90:
        return MemoryStatus.COOLING
    return MemoryStatus.ACTIVE


def token_set(text: str) -> set[str]:
    return {token.casefold() for token in text.split() if token.strip()}


def lexical_score(query: str, content: str) -> float:
    query_tokens = token_set(query)
    content_tokens = token_set(content)
    if not query_tokens:
        return 0.0
    return len(query_tokens & content_tokens) / len(query_tokens)


def cosine_similarity(left: Iterable[float], right: Iterable[float]) -> float:
    left_values = tuple(left)
    right_values = tuple(right)
    if len(left_values) != len(right_values) or not left_values:
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left_values))
    right_norm = math.sqrt(sum(value * value for value in right_values))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return sum(a * b for a, b in zip(left_values, right_values)) / (left_norm * right_norm)


def feedback_weight(value: float) -> float:
    return max(-1.0, min(1.0, value))
