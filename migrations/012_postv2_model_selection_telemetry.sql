CREATE TABLE IF NOT EXISTS model_hw_benchmarks (
  id                 TEXT PRIMARY KEY,
  model_id           TEXT NOT NULL REFERENCES model_registry(id) ON DELETE CASCADE,
  profile_class      TEXT NOT NULL CHECK (profile_class IN ('low', 'mid', 'high')),
  avg_fps            REAL NOT NULL,
  p95_latency_ms     REAL NOT NULL,
  memory_mb          REAL NOT NULL,
  success_rate       REAL NOT NULL,
  notes_json         TEXT NOT NULL DEFAULT '{}',
  created_at         INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_model_hw_benchmarks_model_profile_created
  ON model_hw_benchmarks(model_id, profile_class, created_at);

CREATE TABLE IF NOT EXISTS model_selection_events (
  id                 TEXT PRIMARY KEY,
  model_family       TEXT NOT NULL,
  selected_model_id  TEXT,
  profile_class      TEXT NOT NULL CHECK (profile_class IN ('low', 'mid', 'high')),
  hardware_json      TEXT NOT NULL DEFAULT '{}',
  candidates_json    TEXT NOT NULL DEFAULT '[]',
  outcome            TEXT NOT NULL CHECK (outcome IN ('selected', 'fallback')),
  reason             TEXT NOT NULL DEFAULT '',
  created_at         INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_model_selection_events_family_profile_created
  ON model_selection_events(model_family, profile_class, created_at);
