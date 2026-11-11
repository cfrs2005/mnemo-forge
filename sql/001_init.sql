CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS memory_records (
    memory_id UUID PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    scope TEXT NOT NULL,
    kind TEXT NOT NULL,
    content TEXT NOT NULL,
    source_event_id TEXT NOT NULL,
    source_service TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_from TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_to TIMESTAMPTZ,
    confidence DOUBLE PRECISION NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    status TEXT NOT NULL CHECK (status IN ('active', 'cooling', 'dormant', 'tombstoned')),
    version INTEGER NOT NULL CHECK (version > 0),
    supersedes UUID REFERENCES memory_records(memory_id),
    superseded_by UUID REFERENCES memory_records(memory_id),
    last_activated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    activation_count BIGINT NOT NULL DEFAULT 0,
    feedback_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    embedding VECTOR(768),
    search_document TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('simple', coalesce(kind, '') || ' ' || coalesce(content, ''))
    ) STORED,
    UNIQUE (tenant_id, source_event_id, version)
);

CREATE INDEX IF NOT EXISTS memory_records_tenant_subject_scope_idx
    ON memory_records (tenant_id, subject_id, scope);
CREATE INDEX IF NOT EXISTS memory_records_search_document_idx
    ON memory_records USING GIN (search_document);
CREATE INDEX IF NOT EXISTS memory_records_embedding_hnsw_idx
    ON memory_records USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS memory_feedback (
    feedback_id TEXT PRIMARY KEY,
    memory_id UUID NOT NULL REFERENCES memory_records(memory_id),
    tenant_id TEXT NOT NULL,
    feedback_type TEXT NOT NULL CHECK (feedback_type IN ('accepted', 'rejected', 'corrected', 'useful')),
    service TEXT NOT NULL,
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS memory_access_events (
    event_id UUID PRIMARY KEY,
    memory_id UUID NOT NULL REFERENCES memory_records(memory_id),
    tenant_id TEXT NOT NULL,
    service TEXT NOT NULL,
    reason TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL
);

ALTER TABLE memory_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_access_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY memory_records_tenant_policy ON memory_records
    USING (tenant_id = current_setting('app.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true));
CREATE POLICY memory_feedback_tenant_policy ON memory_feedback
    USING (tenant_id = current_setting('app.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true));
CREATE POLICY memory_access_events_tenant_policy ON memory_access_events
    USING (tenant_id = current_setting('app.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true));
