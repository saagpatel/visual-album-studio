-- Phase 6: analytics retention + backup and ingest run tracking

CREATE TABLE IF NOT EXISTS analytics_ingest_runs (
  id               TEXT PRIMARY KEY,
  channel_row_id   TEXT NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  source           TEXT NOT NULL CHECK (source IN ('analytics_api','reporting_api','manual_import')),
  range_start_ymd  TEXT NOT NULL,
  range_end_ymd    TEXT NOT NULL,
  rows_ingested    INTEGER NOT NULL DEFAULT 0,
  status           TEXT NOT NULL CHECK (status IN ('started','succeeded','failed')),
  details_json     TEXT NOT NULL DEFAULT '{}',
  created_at       INTEGER NOT NULL,
  updated_at       INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS backup_snapshots (
  id               TEXT PRIMARY KEY,
  archive_relpath  TEXT NOT NULL,
  db_sha256        TEXT NOT NULL,
  includes_assets  INTEGER NOT NULL DEFAULT 0,
  created_at       INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS retention_policies (
  id               TEXT PRIMARY KEY,
  policy_scope     TEXT NOT NULL,
  policy_json      TEXT NOT NULL,
  updated_at       INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_analytics_snapshots_channel_range
  ON analytics_snapshots(channel_row_id, range_start_ymd, range_end_ymd);

CREATE UNIQUE INDEX IF NOT EXISTS idx_reporting_files_unique_import
  ON reporting_files(channel_row_id, report_type, range_start_ymd, range_end_ymd, sha256);

CREATE INDEX IF NOT EXISTS idx_niche_notes_keyword_time
  ON niche_notes(keyword_id, updated_at);

CREATE INDEX IF NOT EXISTS idx_ingest_runs_channel_time
  ON analytics_ingest_runs(channel_row_id, created_at);
