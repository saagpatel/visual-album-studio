-- Phase 7: UX platform + productization support tables

CREATE TABLE IF NOT EXISTS ui_preferences (
  id              TEXT PRIMARY KEY,
  preference_json TEXT NOT NULL DEFAULT '{}',
  updated_at      INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS workspace_layouts (
  id              TEXT PRIMARY KEY,
  name            TEXT NOT NULL,
  layout_json     TEXT NOT NULL DEFAULT '{}',
  created_at      INTEGER NOT NULL,
  updated_at      INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS command_history (
  id              TEXT PRIMARY KEY,
  command_id      TEXT NOT NULL,
  args_json       TEXT NOT NULL DEFAULT '{}',
  result_json     TEXT NOT NULL DEFAULT '{}',
  created_at      INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS diagnostics_exports (
  id                    TEXT PRIMARY KEY,
  scope_json            TEXT NOT NULL DEFAULT '{}',
  output_relpath        TEXT NOT NULL,
  redaction_summary_json TEXT NOT NULL DEFAULT '{}',
  created_at            INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS support_reports (
  id              TEXT PRIMARY KEY,
  context_json    TEXT NOT NULL DEFAULT '{}',
  report_json     TEXT NOT NULL DEFAULT '{}',
  created_at      INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS release_profiles (
  id              TEXT PRIMARY KEY,
  channel         TEXT NOT NULL CHECK (channel IN ('stable','beta','dev')),
  manifest_json   TEXT NOT NULL DEFAULT '{}',
  created_at      INTEGER NOT NULL,
  updated_at      INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ui_preferences_updated_at
  ON ui_preferences(updated_at);

CREATE INDEX IF NOT EXISTS idx_workspace_layouts_updated_at
  ON workspace_layouts(updated_at);

CREATE INDEX IF NOT EXISTS idx_command_history_command_time
  ON command_history(command_id, created_at);

CREATE INDEX IF NOT EXISTS idx_diagnostics_exports_scope_time
  ON diagnostics_exports(created_at);

CREATE INDEX IF NOT EXISTS idx_support_reports_created_at
  ON support_reports(created_at);

CREATE INDEX IF NOT EXISTS idx_release_profiles_channel
  ON release_profiles(channel);
