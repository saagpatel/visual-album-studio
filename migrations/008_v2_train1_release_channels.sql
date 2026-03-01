-- V2 Train 1: release channel progression baseline (canary -> beta -> stable)

ALTER TABLE release_profiles RENAME TO release_profiles_legacy;

CREATE TABLE release_profiles (
  id              TEXT PRIMARY KEY,
  channel         TEXT NOT NULL CHECK (channel IN ('stable','beta','canary')),
  manifest_json   TEXT NOT NULL DEFAULT '{}',
  created_at      INTEGER NOT NULL,
  updated_at      INTEGER NOT NULL
);

INSERT INTO release_profiles(id, channel, manifest_json, created_at, updated_at)
SELECT
  id,
  CASE
    WHEN channel = 'dev' THEN 'canary'
    ELSE channel
  END AS channel,
  manifest_json,
  created_at,
  updated_at
FROM release_profiles_legacy;

DROP TABLE release_profiles_legacy;

CREATE INDEX IF NOT EXISTS idx_release_profiles_channel
  ON release_profiles(channel);
