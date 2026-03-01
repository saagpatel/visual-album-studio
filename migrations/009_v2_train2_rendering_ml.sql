ALTER TABLE model_registry ADD COLUMN license_spdx TEXT NOT NULL DEFAULT '';
ALTER TABLE model_registry ADD COLUMN provenance_json TEXT NOT NULL DEFAULT '{}';
ALTER TABLE model_registry ADD COLUMN status TEXT NOT NULL DEFAULT 'candidate' CHECK (status IN ('candidate', 'active', 'deprecated', 'blocked'));
ALTER TABLE model_registry ADD COLUMN replaced_by_model_id TEXT REFERENCES model_registry(id) ON DELETE SET NULL;
ALTER TABLE model_registry ADD COLUMN updated_at INTEGER NOT NULL DEFAULT 0;

UPDATE model_registry
SET updated_at = installed_at
WHERE updated_at = 0;

CREATE TABLE IF NOT EXISTS model_eval_runs (
  id            TEXT PRIMARY KEY,
  model_id      TEXT NOT NULL REFERENCES model_registry(id) ON DELETE CASCADE,
  fixture_id    TEXT NOT NULL,
  quality_score REAL NOT NULL,
  perf_fps      REAL NOT NULL,
  safety_score  REAL NOT NULL,
  notes_json    TEXT NOT NULL DEFAULT '{}',
  created_at    INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_model_eval_runs_model_id_created ON model_eval_runs(model_id, created_at);

CREATE TABLE IF NOT EXISTS mode_contract_versions (
  id            TEXT PRIMARY KEY,
  mode_id       TEXT NOT NULL,
  contract_version INTEGER NOT NULL,
  parameter_ids_json TEXT NOT NULL,
  created_at    INTEGER NOT NULL,
  UNIQUE(mode_id, contract_version)
);

CREATE INDEX IF NOT EXISTS idx_mode_contract_versions_mode_id_version ON mode_contract_versions(mode_id, contract_version);
