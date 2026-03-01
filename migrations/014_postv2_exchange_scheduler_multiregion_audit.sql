CREATE TABLE IF NOT EXISTS preset_exchange_events (
  id                 TEXT PRIMARY KEY,
  source_project_id  TEXT NOT NULL,
  target_project_id  TEXT NOT NULL,
  preset_id          TEXT NOT NULL,
  actor_user_id      TEXT NOT NULL,
  status             TEXT NOT NULL CHECK (status IN ('imported', 'failed')),
  error_code         TEXT NOT NULL DEFAULT '',
  bundle_json        TEXT NOT NULL DEFAULT '{}',
  created_at         INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_preset_exchange_events_target_time
  ON preset_exchange_events(target_project_id, created_at);

CREATE TABLE IF NOT EXISTS distribution_schedule_plans (
  id                 TEXT PRIMARY KEY,
  provider           TEXT NOT NULL,
  job_id             TEXT NOT NULL,
  status             TEXT NOT NULL CHECK (status IN ('scheduled', 'deferred')),
  scheduled_at       INTEGER NOT NULL,
  detail_json        TEXT NOT NULL DEFAULT '{}',
  created_at         INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_distribution_schedule_plans_provider_time
  ON distribution_schedule_plans(provider, scheduled_at);

CREATE TABLE IF NOT EXISTS project_residency_policies (
  project_id         TEXT PRIMARY KEY,
  home_region        TEXT NOT NULL,
  active_regions_json TEXT NOT NULL DEFAULT '[]',
  dr_region          TEXT NOT NULL,
  allowed_regions_json TEXT NOT NULL DEFAULT '[]',
  updated_at         INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS cloud_replication_checkpoints (
  id                 TEXT PRIMARY KEY,
  project_id         TEXT NOT NULL,
  sequence           INTEGER NOT NULL,
  region             TEXT NOT NULL,
  status             TEXT NOT NULL CHECK (status IN ('succeeded', 'pending')),
  detail_json        TEXT NOT NULL DEFAULT '{}',
  created_at         INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cloud_replication_checkpoints_project_sequence
  ON cloud_replication_checkpoints(project_id, sequence, region);

CREATE TABLE IF NOT EXISTS audit_anomaly_events (
  id                 TEXT PRIMARY KEY,
  project_id         TEXT NOT NULL,
  signal_type        TEXT NOT NULL,
  severity           TEXT NOT NULL CHECK (severity IN ('info', 'warn', 'error', 'critical')),
  metric_name        TEXT NOT NULL,
  metric_value       REAL NOT NULL,
  threshold_value    REAL NOT NULL,
  owner              TEXT NOT NULL,
  status             TEXT NOT NULL CHECK (status IN ('open', 'acknowledged', 'resolved')),
  detail_json        TEXT NOT NULL DEFAULT '{}',
  created_at         INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_anomaly_events_project_time
  ON audit_anomaly_events(project_id, created_at);

CREATE TABLE IF NOT EXISTS audit_ownership_map (
  id                 TEXT PRIMARY KEY,
  signal_type        TEXT NOT NULL UNIQUE,
  owner              TEXT NOT NULL,
  channel            TEXT NOT NULL,
  updated_at         INTEGER NOT NULL
);

INSERT OR IGNORE INTO audit_ownership_map(id, signal_type, owner, channel, updated_at)
VALUES
  ('audit_owner_001', 'connector_error_spike', 'saagar210', 'ops', strftime('%s','now')),
  ('audit_owner_002', 'sync_replay_failures', 'saagar210', 'ops', strftime('%s','now')),
  ('audit_owner_003', 'conflict_spike', 'saagar210', 'ops', strftime('%s','now'));
