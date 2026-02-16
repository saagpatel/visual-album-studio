-- Phase 2: visual-mode governance + optional model provenance

CREATE TABLE IF NOT EXISTS mode_families (
  id            TEXT PRIMARY KEY,
  mode_id       TEXT NOT NULL,
  family_type   TEXT NOT NULL CHECK (family_type IN ('layout','palette','camera','typography','particle')),
  family_name   TEXT NOT NULL,
  description   TEXT,
  created_at    INTEGER NOT NULL,
  UNIQUE(mode_id, family_type, family_name)
);

CREATE TABLE IF NOT EXISTS preset_family_bindings (
  preset_id     TEXT NOT NULL REFERENCES presets(id) ON DELETE CASCADE,
  family_id     TEXT NOT NULL REFERENCES mode_families(id) ON DELETE CASCADE,
  created_at    INTEGER NOT NULL,
  PRIMARY KEY (preset_id, family_id)
);

CREATE INDEX IF NOT EXISTS idx_mode_families_mode_type ON mode_families(mode_id, family_type);

CREATE TABLE IF NOT EXISTS model_download_events (
  id            TEXT PRIMARY KEY,
  model_id      TEXT NOT NULL REFERENCES model_registry(id) ON DELETE CASCADE,
  source_url    TEXT NOT NULL,
  expected_sha256 TEXT NOT NULL,
  actual_sha256 TEXT,
  status        TEXT NOT NULL CHECK (status IN ('started','verified','failed')),
  created_at    INTEGER NOT NULL,
  updated_at    INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_model_download_events_model ON model_download_events(model_id, created_at);
