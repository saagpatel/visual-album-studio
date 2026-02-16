-- Phase 3: mixer persistence + deterministic bounce metadata

CREATE TABLE IF NOT EXISTS mixer_master_params (
  project_id      TEXT PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
  master_gain_db  REAL NOT NULL DEFAULT 0.0,
  limiter_enabled INTEGER NOT NULL DEFAULT 0,
  limiter_preset  TEXT,
  params_json     TEXT NOT NULL DEFAULT '{}',
  updated_at      INTEGER NOT NULL
);

ALTER TABLE project_tracks ADD COLUMN muted INTEGER NOT NULL DEFAULT 0;
ALTER TABLE project_tracks ADD COLUMN solo INTEGER NOT NULL DEFAULT 0;

ALTER TABLE audio_bounces ADD COLUMN duration_ms INTEGER;
ALTER TABLE audio_bounces ADD COLUMN ffmpeg_manifest_json TEXT;

CREATE INDEX IF NOT EXISTS idx_project_tracks_project_sort ON project_tracks(project_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_audio_bounces_project_created ON audio_bounces(project_id, created_at);
