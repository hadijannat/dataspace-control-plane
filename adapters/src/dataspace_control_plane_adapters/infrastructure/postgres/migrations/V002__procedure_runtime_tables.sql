-- V002__procedure_runtime_tables.sql
-- Durable HTTP idempotency state and coarse procedure runtime projection.

CREATE TABLE IF NOT EXISTS http_idempotency_keys (
    tenant_id           TEXT        NOT NULL,
    procedure_type      TEXT        NOT NULL,
    idempotency_key     TEXT        NOT NULL,
    request_fingerprint TEXT        NOT NULL,
    workflow_id         TEXT        NOT NULL,
    run_id              TEXT,
    response_json       JSONB       NOT NULL,
    status              TEXT        NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, procedure_type, idempotency_key)
);

CREATE INDEX IF NOT EXISTS http_idempotency_keys_workflow_idx
    ON http_idempotency_keys (workflow_id);

CREATE TABLE IF NOT EXISTS procedures (
    workflow_id        TEXT        PRIMARY KEY,
    procedure_type     TEXT        NOT NULL,
    tenant_id          TEXT        NOT NULL,
    status             TEXT        NOT NULL,
    phase              TEXT,
    progress_percent   INTEGER,
    result             JSONB,
    failure_message    TEXT,
    search_attributes  JSONB       NOT NULL DEFAULT '{}'::jsonb,
    links              JSONB       NOT NULL DEFAULT '{}'::jsonb,
    started_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS procedures_tenant_status_idx
    ON procedures (tenant_id, status, started_at DESC);

CREATE INDEX IF NOT EXISTS procedures_tenant_type_idx
    ON procedures (tenant_id, procedure_type, started_at DESC);

ALTER TABLE http_idempotency_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE procedures ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'http_idempotency_keys' AND policyname = 'tenant_isolation'
    ) THEN
        CREATE POLICY tenant_isolation ON http_idempotency_keys
            USING (tenant_id = current_setting('app.current_tenant', TRUE));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'procedures' AND policyname = 'tenant_isolation'
    ) THEN
        CREATE POLICY tenant_isolation ON procedures
            USING (tenant_id = current_setting('app.current_tenant', TRUE));
    END IF;
END;
$$;
