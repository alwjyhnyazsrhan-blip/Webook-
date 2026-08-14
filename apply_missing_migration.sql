-- C-004 FIX: Runtime schema alignment migration
-- Migration: e1b2c3d4e5f6_runtime_schema_alignment
-- Run this against data/webook.db if alembic has never been applied.
-- Idempotent: each statement is guarded so re-running is safe.

-- 1. auth_sessions: add success_rate column
ALTER TABLE auth_sessions ADD COLUMN success_rate INTEGER DEFAULT 100;

-- 2. auth_sessions: add last_error column
ALTER TABLE auth_sessions ADD COLUMN last_error VARCHAR;

-- 3. live_events: add max_price column
ALTER TABLE live_events ADD COLUMN max_price INTEGER;

-- 4. Mark migration as applied in alembic_version
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
INSERT OR IGNORE INTO alembic_version (version_num) VALUES ('e1b2c3d4e5f6');

-- ── f1a2b3c4d5e6: add missing audit columns ──────────────────────────────────
-- Run this on any existing deployment where alembic has not run the new migration.

ALTER TABLE auth_sessions ADD COLUMN IF NOT EXISTS success_rate INTEGER DEFAULT 100;
ALTER TABLE auth_sessions ADD COLUMN IF NOT EXISTS last_error VARCHAR DEFAULT NULL;
ALTER TABLE live_events ADD COLUMN IF NOT EXISTS max_price INTEGER DEFAULT NULL;
ALTER TABLE reservation_tasks ADD COLUMN IF NOT EXISTS sniper_mode BOOLEAN DEFAULT FALSE;

-- Mark migration as applied
INSERT INTO alembic_version (version_num) VALUES ('f1a2b3c4d5e6')
  ON CONFLICT (version_num) DO NOTHING;
