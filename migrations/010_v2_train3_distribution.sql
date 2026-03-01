CREATE TABLE IF NOT EXISTS distribution_providers (
  id                 TEXT PRIMARY KEY,
  provider           TEXT NOT NULL UNIQUE CHECK (provider IN ('youtube', 'tiktok', 'instagram')),
  display_name       TEXT NOT NULL,
  enabled            INTEGER NOT NULL DEFAULT 1,
  created_at         INTEGER NOT NULL,
  updated_at         INTEGER NOT NULL
);

INSERT OR IGNORE INTO distribution_providers(id, provider, display_name, enabled, created_at, updated_at)
VALUES
  ('provider_youtube', 'youtube', 'YouTube', 1, strftime('%s','now'), strftime('%s','now')),
  ('provider_tiktok', 'tiktok', 'TikTok', 1, strftime('%s','now'), strftime('%s','now')),
  ('provider_instagram', 'instagram', 'Instagram', 1, strftime('%s','now'), strftime('%s','now'));

CREATE TABLE IF NOT EXISTS distribution_publish_jobs (
  id                 TEXT PRIMARY KEY,
  provider           TEXT NOT NULL CHECK (provider IN ('youtube', 'tiktok', 'instagram')),
  channel_profile_id TEXT NOT NULL,
  request_json       TEXT NOT NULL DEFAULT '{}',
  status             TEXT NOT NULL CHECK (status IN ('queued', 'succeeded', 'failed')),
  error_code         TEXT NOT NULL DEFAULT '',
  retryable          INTEGER NOT NULL DEFAULT 0,
  publish_ref        TEXT NOT NULL DEFAULT '',
  created_at         INTEGER NOT NULL,
  updated_at         INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_distribution_publish_jobs_provider_time
  ON distribution_publish_jobs(provider, created_at);

CREATE TABLE IF NOT EXISTS provider_policy_cache (
  id                 TEXT PRIMARY KEY,
  provider           TEXT NOT NULL CHECK (provider IN ('youtube', 'tiktok', 'instagram')),
  policy_json        TEXT NOT NULL DEFAULT '{}',
  fetched_at         INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_provider_policy_cache_provider_time
  ON provider_policy_cache(provider, fetched_at);

CREATE TABLE IF NOT EXISTS connector_diagnostics (
  id                 TEXT PRIMARY KEY,
  connector          TEXT NOT NULL,
  severity           TEXT NOT NULL CHECK (severity IN ('info', 'warn', 'error')),
  payload_json       TEXT NOT NULL DEFAULT '{}',
  created_at         INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_connector_diagnostics_connector_time
  ON connector_diagnostics(connector, created_at);
