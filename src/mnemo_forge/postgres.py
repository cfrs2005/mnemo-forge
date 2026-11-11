from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from uuid import UUID

from .models import MemoryRecord


class PostgresMemoryRepository:
    """Parameterized SQL adapter. Import psycopg only when this adapter is used."""

    def __init__(self, connection: object) -> None:
        self.connection = connection

    def insert_memory(self, record: MemoryRecord) -> None:
        query = """
            INSERT INTO memory_records (
                memory_id, tenant_id, subject_id, scope, kind, content,
                source_event_id, source_service, created_at, valid_from,
                valid_to, confidence, status, version, supersedes,
                last_activated_at, activation_count, feedback_score, embedding
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params: tuple[object, ...] = (
            record.memory_id, record.tenant_id, record.subject_id, record.scope,
            record.kind, record.content, record.source_event_id, record.source_service,
            record.created_at, record.valid_from, record.valid_to, record.confidence,
            record.status.value, record.version, record.supersedes,
            record.last_activated_at, record.activation_count, record.feedback_score,
            list(record.embedding) if record.embedding is not None else None,
        )
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
        self.connection.commit()

    def search_memory(self, tenant_id: str, subject_id: str, scope: str, query_text: str, limit: int = 10) -> Iterable[tuple[object, ...]]:
        query = """
            SELECT memory_id, tenant_id, subject_id, scope, kind, content, version
            FROM memory_records
            WHERE tenant_id = %s
              AND subject_id = %s
              AND scope = %s
              AND status <> 'tombstoned'
              AND superseded_by IS NULL
              AND search_document @@ plainto_tsquery('simple', %s)
            ORDER BY ts_rank_cd(search_document, plainto_tsquery('simple', %s)) DESC
            LIMIT %s
        """
        params = (tenant_id, subject_id, scope, query_text, query_text, limit)
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
