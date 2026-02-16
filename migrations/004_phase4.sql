-- Phase 4: batch execution reliability + originality evidence

CREATE TABLE IF NOT EXISTS batch_executions (
  id               TEXT PRIMARY KEY,
  batch_id         TEXT NOT NULL REFERENCES batch_plans(id) ON DELETE CASCADE,
  status           TEXT NOT NULL CHECK (status IN ('queued','running','paused','failed','succeeded','canceled')),
  max_concurrent   INTEGER NOT NULL,
  retry_limit      INTEGER NOT NULL DEFAULT 2,
  backoff_seconds  INTEGER NOT NULL DEFAULT 30,
  circuit_open     INTEGER NOT NULL DEFAULT 0,
  created_at       INTEGER NOT NULL,
  updated_at       INTEGER NOT NULL
);

ALTER TABLE batch_items ADD COLUMN attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE batch_items ADD COLUMN last_error_json TEXT;
ALTER TABLE batch_items ADD COLUMN scheduled_at INTEGER;

CREATE INDEX IF NOT EXISTS idx_batch_items_batch_status ON batch_items(batch_id, status);
CREATE INDEX IF NOT EXISTS idx_batch_items_status_created ON batch_items(status, created_at);

CREATE TABLE IF NOT EXISTS originality_events (
  id               TEXT PRIMARY KEY,
  export_id        TEXT,
  batch_id         TEXT,
  variant_spec_id  TEXT,
  distance_score   REAL NOT NULL,
  changed_params_json TEXT NOT NULL,
  structural_change INTEGER NOT NULL DEFAULT 0,
  created_at       INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_originality_events_batch ON originality_events(batch_id, created_at);
