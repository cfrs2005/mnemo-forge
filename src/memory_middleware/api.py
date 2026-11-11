from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from .models import FeedbackType
from .repository import InMemoryMemoryRepository
from .service import MemoryService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MemoryWriteRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    content: str = Field(min_length=1)
    source_event_id: str = Field(min_length=1)
    source_service: str = Field(min_length=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    supersedes: UUID | None = None
    embedding: list[float] | None = None


class FeedbackRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    feedback_id: str = Field(min_length=1)
    feedback_type: FeedbackType
    service: str = Field(min_length=1)
    note: str | None = None


class AccessRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    service: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class RestoreRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    service: str = Field(min_length=1)


repository = InMemoryMemoryRepository()
service = MemoryService(repository)
app = FastAPI(title="Memory Middleware", version="0.1.0")


@app.post("/v1/memories")
def write_memory(request: MemoryWriteRequest) -> dict[str, object]:
    record = service.write(
        tenant_id=request.tenant_id,
        subject_id=request.subject_id,
        scope=request.scope,
        kind=request.kind,
        content=request.content,
        source_event_id=request.source_event_id,
        source_service=request.source_service,
        confidence=request.confidence,
        supersedes=request.supersedes,
        embedding=tuple(request.embedding) if request.embedding is not None else None,
    )
    return {"memory_id": str(record.memory_id), "version": record.version, "status": record.status.value}


@app.get("/v1/memories/search")
def search_memory(
    tenant_id: str = Query(min_length=1),
    subject_id: str = Query(min_length=1),
    scope: str = Query(min_length=1),
    q: str = Query(min_length=1),
    limit: int = Query(default=10, ge=1, le=100),
) -> dict[str, object]:
    results = service.search(tenant_id, subject_id, scope, q, utc_now(), limit=limit)
    return {"items": [_serialize_result(item) for item in results]}


@app.get("/v1/memories/{memory_id}")
def get_memory(memory_id: UUID, tenant_id: str = Query(min_length=1), include_history: bool = False) -> dict[str, object]:
    record = repository.get(tenant_id, memory_id, include_history=include_history)
    if record is None:
        raise HTTPException(status_code=404, detail="memory not found")
    return _serialize_record(record)


@app.post("/v1/memories/{memory_id}/access")
def record_access(memory_id: UUID, request: AccessRequest) -> dict[str, object]:
    try:
        event = repository.record_access(request.tenant_id, memory_id, request.service, request.reason, utc_now())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="memory not found") from exc
    return {"event_id": str(event.event_id), "memory_id": str(event.memory_id)}


@app.post("/v1/memories/{memory_id}/feedback")
def record_feedback(memory_id: UUID, request: FeedbackRequest) -> dict[str, object]:
    try:
        event = service.feedback(request.tenant_id, memory_id, request.feedback_id, request.feedback_type, request.service, utc_now(), request.note)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="memory not found") from exc
    return {"feedback_id": event.feedback_id, "type": event.feedback_type.value}


@app.post("/v1/memories/{memory_id}/restore")
def restore_memory(memory_id: UUID, request: RestoreRequest) -> dict[str, object]:
    try:
        record = service.restore(request.tenant_id, memory_id, utc_now(), request.service)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="memory not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _serialize_record(record)


def _serialize_record(record: object) -> dict[str, object]:
    return {
        "memory_id": str(record.memory_id),
        "tenant_id": record.tenant_id,
        "subject_id": record.subject_id,
        "scope": record.scope,
        "kind": record.kind,
        "content": record.content,
        "source_event_id": record.source_event_id,
        "source_service": record.source_service,
        "status": record.status.value,
        "version": record.version,
        "supersedes": str(record.supersedes) if record.supersedes else None,
        "superseded_by": str(record.superseded_by) if record.superseded_by else None,
        "confidence": record.confidence,
        "activation_count": record.activation_count,
        "feedback_score": record.feedback_score,
    }


def _serialize_result(result: object) -> dict[str, object]:
    payload = _serialize_record(result.memory)
    payload.update({
        "score": result.score,
        "lexical_score": result.lexical_score,
        "semantic_score": result.semantic_score,
        "decay_score": result.decay_score,
        "feedback_score": result.feedback_score,
        "activation_reason": result.activation_reason,
    })
    return payload
