CREATE TABLE IF NOT EXISTS cloud_sync_state (
  project_id        TEXT PRIMARY KEY,
  last_sequence     INTEGER NOT NULL DEFAULT 0,
  updated_at        INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS cloud_sync_queue (
  id                TEXT PRIMARY KEY,
  project_id        TEXT NOT NULL,
  envelope_json     TEXT NOT NULL,
  status            TEXT NOT NULL CHECK (status IN ('queued', 'replayed', 'failed')),
  error_code        TEXT NOT NULL DEFAULT '',
  created_at        INTEGER NOT NULL,
  updated_at        INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cloud_sync_queue_project_status_created
  ON cloud_sync_queue(project_id, status, created_at);

CREATE TABLE IF NOT EXISTS cloud_sync_replay_log (
  id                TEXT PRIMARY KEY,
  project_id        TEXT NOT NULL,
  queue_id          TEXT NOT NULL REFERENCES cloud_sync_queue(id) ON DELETE CASCADE,
  sequence          INTEGER NOT NULL,
  status            TEXT NOT NULL CHECK (status IN ('succeeded', 'failed')),
  detail_json       TEXT NOT NULL DEFAULT '{}',
  created_at        INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cloud_sync_replay_log_project_created
  ON cloud_sync_replay_log(project_id, created_at);

CREATE TABLE IF NOT EXISTS collaboration_members (
  project_id        TEXT NOT NULL,
  user_id           TEXT NOT NULL,
  role              TEXT NOT NULL CHECK (role IN ('owner', 'editor', 'viewer')),
  updated_at        INTEGER NOT NULL,
  PRIMARY KEY (project_id, user_id)
);

CREATE TABLE IF NOT EXISTS collaboration_conflicts (
  id                TEXT PRIMARY KEY,
  project_id        TEXT NOT NULL,
  resource_id       TEXT NOT NULL,
  winner_actor_id   TEXT NOT NULL,
  winner_sequence   INTEGER NOT NULL,
  resolution_json   TEXT NOT NULL DEFAULT '{}',
  created_at        INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_collaboration_conflicts_project_created
  ON collaboration_conflicts(project_id, created_at);

CREATE TABLE IF NOT EXISTS cloud_objects (
  id                TEXT PRIMARY KEY,
  project_id        TEXT NOT NULL,
  object_key        TEXT NOT NULL,
  schema_version    INTEGER NOT NULL,
  storage_ref       TEXT NOT NULL,
  checksum          TEXT NOT NULL,
  size_bytes        INTEGER NOT NULL,
  created_at        INTEGER NOT NULL,
  updated_at        INTEGER NOT NULL,
  UNIQUE(project_id, object_key)
);

CREATE INDEX IF NOT EXISTS idx_cloud_objects_project_schema
  ON cloud_objects(project_id, schema_version, updated_at);
