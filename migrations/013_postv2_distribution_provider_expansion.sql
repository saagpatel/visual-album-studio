-- Expand provider constraints to include Post-V2 PV2-101 lanes.

ALTER TABLE distribution_providers RENAME TO distribution_providers_old;

CREATE TABLE distribution_providers (
  id                 TEXT PRIMARY KEY,
  provider           TEXT NOT NULL UNIQUE CHECK (provider IN ('youtube', 'tiktok', 'instagram', 'facebook_reels', 'x')),
  display_name       TEXT NOT NULL,
  enabled            INTEGER NOT NULL DEFAULT 1,
  created_at         INTEGER NOT NULL,
  updated_at         INTEGER NOT NULL
);

INSERT INTO distribution_providers(id, provider, display_name, enabled, created_at, updated_at)
SELECT id, provider, display_name, enabled, created_at, updated_at
FROM distribution_providers_old;

INSERT OR IGNORE INTO distribution_providers(id, provider, display_name, enabled, created_at, updated_at)
VALUES
  ('provider_facebook_reels', 'facebook_reels', 'Facebook Reels', 1, strftime('%s','now'), strftime('%s','now')),
  ('provider_x', 'x', 'X', 1, strftime('%s','now'), strftime('%s','now'));

DROP TABLE distribution_providers_old;

ALTER TABLE distribution_publish_jobs RENAME TO distribution_publish_jobs_old;

CREATE TABLE distribution_publish_jobs (
  id                 TEXT PRIMARY KEY,
  provider           TEXT NOT NULL CHECK (provider IN ('youtube', 'tiktok', 'instagram', 'facebook_reels', 'x')),
  channel_profile_id TEXT NOT NULL,
  request_json       TEXT NOT NULL DEFAULT '{}',
  status             TEXT NOT NULL CHECK (status IN ('queued', 'succeeded', 'failed')),
  error_code         TEXT NOT NULL DEFAULT '',
  retryable          INTEGER NOT NULL DEFAULT 0,
  publish_ref        TEXT NOT NULL DEFAULT '',
  created_at         INTEGER NOT NULL,
  updated_at         INTEGER NOT NULL
);

INSERT INTO distribution_publish_jobs(id, provider, channel_profile_id, request_json, status, error_code, retryable, publish_ref, created_at, updated_at)
SELECT id, provider, channel_profile_id, request_json, status, error_code, retryable, publish_ref, created_at, updated_at
FROM distribution_publish_jobs_old;

DROP TABLE distribution_publish_jobs_old;

CREATE INDEX IF NOT EXISTS idx_distribution_publish_jobs_provider_time
  ON distribution_publish_jobs(provider, created_at);

ALTER TABLE provider_policy_cache RENAME TO provider_policy_cache_old;

CREATE TABLE provider_policy_cache (
  id                 TEXT PRIMARY KEY,
  provider           TEXT NOT NULL CHECK (provider IN ('youtube', 'tiktok', 'instagram', 'facebook_reels', 'x')),
  policy_json        TEXT NOT NULL DEFAULT '{}',
  fetched_at         INTEGER NOT NULL
);

INSERT INTO provider_policy_cache(id, provider, policy_json, fetched_at)
SELECT id, provider, policy_json, fetched_at
FROM provider_policy_cache_old;

DROP TABLE provider_policy_cache_old;

CREATE INDEX IF NOT EXISTS idx_provider_policy_cache_provider_time
  ON provider_policy_cache(provider, fetched_at);
