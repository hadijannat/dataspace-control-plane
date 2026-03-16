-- V003__schema_migrations.sql
-- Migration bookkeeping for startup/readiness checks.

CREATE TABLE IF NOT EXISTS schema_migrations (
    version      INTEGER     PRIMARY KEY,
    description  TEXT        NOT NULL,
    applied_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO schema_migrations (version, description)
VALUES
    (1, 'initial_schema'),
    (2, 'procedure_runtime_tables'),
    (3, 'schema_migrations')
ON CONFLICT (version) DO NOTHING;
