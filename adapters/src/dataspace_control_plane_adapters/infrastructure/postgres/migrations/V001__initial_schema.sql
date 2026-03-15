-- V001__initial_schema.sql
-- Initial schema for the dataspace control-plane PostgreSQL adapter.
-- All multi-tenant tables use Row-Level Security (RLS) to enforce tenant isolation.
-- The GUC app.current_tenant must be set via SET LOCAL before any DML.
--
-- Conventions:
--   - id columns are TEXT (UUID strings) to avoid Postgres UUID casting overhead.
--   - payload_json is JSONB — stores the full aggregate blob without ORM field mapping.
--   - version columns support optimistic concurrency (incremented on each save).
--   - All timestamps are TIMESTAMPTZ (UTC-normalised).
--   - Append-only tables (audit_records) have no UPDATE or DELETE.

-- ---------------------------------------------------------------------------
-- Audit records (append-only; no UPDATE or DELETE ever)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS audit_records (
    id               TEXT        PRIMARY KEY,
    tenant_id        TEXT        NOT NULL,
    category         TEXT        NOT NULL,
    action           TEXT        NOT NULL,
    outcome          TEXT        NOT NULL,
    actor_json       JSONB       NOT NULL,
    correlation_json JSONB,
    payload_json     JSONB,
    retention_class  TEXT        NOT NULL DEFAULT 'standard',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS audit_records_tenant_created_idx
    ON audit_records (tenant_id, created_at DESC);

CREATE INDEX IF NOT EXISTS audit_records_tenant_category_idx
    ON audit_records (tenant_id, category);

-- ---------------------------------------------------------------------------
-- Negotiations
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS negotiations (
    id              TEXT        PRIMARY KEY,
    tenant_id       TEXT        NOT NULL,
    legal_entity_id TEXT        NOT NULL,
    status          TEXT        NOT NULL,
    payload_json    JSONB       NOT NULL,
    version         INTEGER     NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS negotiations_tenant_legal_entity_idx
    ON negotiations (tenant_id, legal_entity_id);

CREATE INDEX IF NOT EXISTS negotiations_tenant_status_idx
    ON negotiations (tenant_id, status);

-- ---------------------------------------------------------------------------
-- Entitlements
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS entitlements (
    id              TEXT        PRIMARY KEY,
    tenant_id       TEXT        NOT NULL,
    legal_entity_id TEXT        NOT NULL,
    agreement_id    TEXT        NOT NULL,
    asset_id        TEXT        NOT NULL,
    status          TEXT        NOT NULL,
    payload_json    JSONB       NOT NULL,
    version         INTEGER     NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS entitlements_tenant_agreement_idx
    ON entitlements (tenant_id, agreement_id);

CREATE INDEX IF NOT EXISTS entitlements_tenant_legal_entity_status_idx
    ON entitlements (tenant_id, legal_entity_id, status);

-- ---------------------------------------------------------------------------
-- Operator grants read model
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS operator_grants (
    grant_id    TEXT        PRIMARY KEY,
    tenant_id   TEXT        NOT NULL,
    subject     TEXT        NOT NULL,
    role_name   TEXT        NOT NULL,
    scope_json  JSONB       NOT NULL,
    expires_at  TIMESTAMPTZ,
    granted_by  TEXT        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status      TEXT        NOT NULL DEFAULT 'active'
);

CREATE INDEX IF NOT EXISTS operator_grants_subject_status_idx
    ON operator_grants (subject, status);

CREATE INDEX IF NOT EXISTS operator_grants_tenant_subject_idx
    ON operator_grants (tenant_id, subject);

-- ---------------------------------------------------------------------------
-- Transactional outbox
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS outbox_entries (
    id             TEXT        PRIMARY KEY,
    tenant_id      TEXT        NOT NULL,
    aggregate_type TEXT        NOT NULL,
    aggregate_id   TEXT        NOT NULL,
    event_type     TEXT        NOT NULL,
    payload_json   JSONB       NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at   TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS outbox_entries_unpublished_idx
    ON outbox_entries (created_at ASC)
    WHERE published_at IS NULL;

-- ---------------------------------------------------------------------------
-- Row-Level Security — tenant isolation
-- The GUC app.current_tenant must be set via SET LOCAL in every transaction.
-- The TRUE flag on current_setting prevents errors when the GUC is unset
-- (e.g. during superuser maintenance sessions).
-- ---------------------------------------------------------------------------

ALTER TABLE audit_records    ENABLE ROW LEVEL SECURITY;
ALTER TABLE negotiations     ENABLE ROW LEVEL SECURITY;
ALTER TABLE entitlements     ENABLE ROW LEVEL SECURITY;
ALTER TABLE operator_grants  ENABLE ROW LEVEL SECURITY;

-- Drop and recreate policies idempotently (CREATE POLICY errors if it exists).
DO $$
BEGIN
    -- audit_records
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'audit_records' AND policyname = 'tenant_isolation'
    ) THEN
        CREATE POLICY tenant_isolation ON audit_records
            USING (tenant_id = current_setting('app.current_tenant', TRUE));
    END IF;

    -- negotiations
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'negotiations' AND policyname = 'tenant_isolation'
    ) THEN
        CREATE POLICY tenant_isolation ON negotiations
            USING (tenant_id = current_setting('app.current_tenant', TRUE));
    END IF;

    -- entitlements
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'entitlements' AND policyname = 'tenant_isolation'
    ) THEN
        CREATE POLICY tenant_isolation ON entitlements
            USING (tenant_id = current_setting('app.current_tenant', TRUE));
    END IF;

    -- operator_grants
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'operator_grants' AND policyname = 'tenant_isolation'
    ) THEN
        CREATE POLICY tenant_isolation ON operator_grants
            USING (tenant_id = current_setting('app.current_tenant', TRUE));
    END IF;
END;
$$;

-- Outbox entries are not RLS-protected (publisher process runs as superuser
-- or with a role that bypasses RLS for cross-tenant outbox relay).
