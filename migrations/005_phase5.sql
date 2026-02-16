-- Phase 5: publish auditing + resumable upload reliability metadata

CREATE TABLE IF NOT EXISTS publish_audit_logs (
  id               TEXT PRIMARY KEY,
  job_id           TEXT REFERENCES jobs(id) ON DELETE SET NULL,
  channel_row_id   TEXT REFERENCES channels(id) ON DELETE SET NULL,
  action           TEXT NOT NULL,
  status           TEXT NOT NULL CHECK (status IN ('started','succeeded','failed','skipped')),
  details_json     TEXT NOT NULL DEFAULT '{}',
  created_at       INTEGER NOT NULL
);

ALTER TABLE youtube_uploads ADD COLUMN retry_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE youtube_uploads ADD COLUMN last_error_code TEXT;
ALTER TABLE youtube_uploads ADD COLUMN resumable_etag TEXT;

CREATE TABLE IF NOT EXISTS quota_operation_logs (
  id               TEXT PRIMARY KEY,
  scope            TEXT NOT NULL,
  operation        TEXT NOT NULL,
  estimated_units  INTEGER NOT NULL,
  consumed_units   INTEGER NOT NULL DEFAULT 0,
  status           TEXT NOT NULL CHECK (status IN ('planned','consumed','reverted','skipped')),
  created_at       INTEGER NOT NULL,
  updated_at       INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_publish_audit_channel_time ON publish_audit_logs(channel_row_id, created_at);
CREATE INDEX IF NOT EXISTS idx_quota_operation_scope_day ON quota_operation_logs(scope, created_at);
