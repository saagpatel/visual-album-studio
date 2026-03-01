CREATE TABLE IF NOT EXISTS provider_policy_watch_runs (
  id                 TEXT PRIMARY KEY,
  source             TEXT NOT NULL,
  providers_checked  INTEGER NOT NULL,
  changes_detected   INTEGER NOT NULL,
  created_at         INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS provider_policy_changelog (
  id                    TEXT PRIMARY KEY,
  provider              TEXT NOT NULL,
  previous_policy_json  TEXT NOT NULL DEFAULT '{}',
  current_policy_json   TEXT NOT NULL DEFAULT '{}',
  changed_fields_json   TEXT NOT NULL DEFAULT '[]',
  diff_json             TEXT NOT NULL DEFAULT '{}',
  source                TEXT NOT NULL,
  detected_at           INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_provider_policy_changelog_provider_time
  ON provider_policy_changelog(provider, detected_at DESC);
