CREATE TABLE IF NOT EXISTS dr_rehearsal_runs (
  id                 TEXT PRIMARY KEY,
  project_id         TEXT NOT NULL,
  quarter_label      TEXT NOT NULL,
  status             TEXT NOT NULL CHECK (status IN ('passed', 'failed')),
  summary_json       TEXT NOT NULL DEFAULT '{}',
  created_at         INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS dr_rehearsal_steps (
  id                 TEXT PRIMARY KEY,
  run_id             TEXT NOT NULL REFERENCES dr_rehearsal_runs(id) ON DELETE CASCADE,
  step_name          TEXT NOT NULL,
  status             TEXT NOT NULL CHECK (status IN ('passed', 'failed')),
  sequence           INTEGER NOT NULL,
  detail_json        TEXT NOT NULL DEFAULT '{}',
  created_at         INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dr_rehearsal_steps_run_sequence
  ON dr_rehearsal_steps(run_id, sequence);

CREATE TABLE IF NOT EXISTS anomaly_triage_reports (
  id                 TEXT PRIMARY KEY,
  project_id         TEXT NOT NULL,
  signal_id          TEXT NOT NULL,
  severity           TEXT NOT NULL,
  context_json       TEXT NOT NULL DEFAULT '{}',
  recommendations_json TEXT NOT NULL DEFAULT '[]',
  created_at         INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_anomaly_triage_reports_project_time
  ON anomaly_triage_reports(project_id, created_at DESC);

CREATE TABLE IF NOT EXISTS preset_trust_ui_events (
  id                 TEXT PRIMARY KEY,
  preset_id          TEXT NOT NULL,
  actor_id           TEXT NOT NULL,
  state              TEXT NOT NULL,
  signature_valid    INTEGER NOT NULL DEFAULT 0,
  provenance_json    TEXT NOT NULL DEFAULT '{}',
  created_at         INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_preset_trust_ui_events_preset_time
  ON preset_trust_ui_events(preset_id, created_at DESC);

CREATE TABLE IF NOT EXISTS scheduler_simulation_runs (
  id                 TEXT PRIMARY KEY,
  plan_id            TEXT NOT NULL,
  provider           TEXT NOT NULL,
  status             TEXT NOT NULL,
  timeline_json      TEXT NOT NULL DEFAULT '[]',
  quota_overlay_json TEXT NOT NULL DEFAULT '{}',
  created_at         INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_scheduler_simulation_runs_plan_provider
  ON scheduler_simulation_runs(plan_id, provider);

CREATE TABLE IF NOT EXISTS collaboration_timeline_views (
  id                 TEXT PRIMARY KEY,
  project_id         TEXT NOT NULL,
  event_count        INTEGER NOT NULL,
  filters_json       TEXT NOT NULL DEFAULT '{}',
  generated_at       INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_collaboration_timeline_views_project_time
  ON collaboration_timeline_views(project_id, generated_at DESC);

CREATE TABLE IF NOT EXISTS provider_feature_flags (
  provider           TEXT PRIMARY KEY,
  enabled            INTEGER NOT NULL DEFAULT 0,
  rollout_stage      TEXT NOT NULL DEFAULT 'canary',
  candidate          INTEGER NOT NULL DEFAULT 1,
  updated_at         INTEGER NOT NULL
);

INSERT OR IGNORE INTO provider_feature_flags(provider, enabled, rollout_stage, candidate, updated_at)
VALUES
  ('youtube', 1, 'stable', 0, strftime('%s','now')),
  ('tiktok', 1, 'stable', 0, strftime('%s','now')),
  ('instagram', 1, 'stable', 0, strftime('%s','now')),
  ('facebook_reels', 1, 'stable', 0, strftime('%s','now')),
  ('x', 1, 'stable', 0, strftime('%s','now')),
  ('linkedin', 0, 'canary', 1, strftime('%s','now')),
  ('snapchat', 0, 'canary', 1, strftime('%s','now'));

CREATE TABLE IF NOT EXISTS residency_policy_templates (
  id                 TEXT PRIMARY KEY,
  display_name       TEXT NOT NULL,
  template_json      TEXT NOT NULL DEFAULT '{}',
  created_at         INTEGER NOT NULL,
  updated_at         INTEGER NOT NULL
);

INSERT OR IGNORE INTO residency_policy_templates(id, display_name, template_json, created_at, updated_at)
VALUES
  ('tpl_us_default', 'US Default', '{"home_region":"us-west-1","active_regions":["us-west-1","us-east-1"],"dr_region":"eu-west-1","allowed_regions":["us-west-1","us-east-1","eu-west-1"],"compliance_profile":"us_default"}', strftime('%s','now'), strftime('%s','now')),
  ('tpl_eu_strict', 'EU Strict', '{"home_region":"eu-west-1","active_regions":["eu-west-1"],"dr_region":"us-east-1","allowed_regions":["eu-west-1","us-east-1"],"compliance_profile":"eu_strict"}', strftime('%s','now'), strftime('%s','now')),
  ('tpl_global_balanced', 'Global Balanced', '{"home_region":"us-west-1","active_regions":["us-west-1","us-east-1","eu-west-1"],"dr_region":"eu-west-1","allowed_regions":["us-west-1","us-east-1","eu-west-1"],"compliance_profile":"global_balanced"}', strftime('%s','now'), strftime('%s','now'));

CREATE TABLE IF NOT EXISTS audit_dashboard_exports (
  id                 TEXT PRIMARY KEY,
  project_id         TEXT NOT NULL,
  export_path        TEXT NOT NULL,
  manifest_json      TEXT NOT NULL DEFAULT '{}',
  created_at         INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_dashboard_exports_project_time
  ON audit_dashboard_exports(project_id, created_at DESC);
