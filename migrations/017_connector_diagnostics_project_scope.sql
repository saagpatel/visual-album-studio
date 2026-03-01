ALTER TABLE connector_diagnostics
  ADD COLUMN project_id TEXT NOT NULL DEFAULT '';

CREATE INDEX IF NOT EXISTS idx_connector_diagnostics_project_time
  ON connector_diagnostics(project_id, created_at);
