# Analytics & Revenue (Phase 6)

Phase 6 closes the loop with local dashboards, quota-aware sync, and optional revenue tracking.

## Goals
- Dashboards load instantly from local SQLite.
- Sync uses **official APIs only**:
  - YouTube Analytics API (query-style)
  - YouTube Reporting API (bulk CSV reports)
- Quota-aware behavior and graceful degradation.
- No scraping of YouTube Studio.

## Data sources

### YouTube Analytics API
- Used for targeted queries that power dashboards:
  - views, watch time, subscribers, CTR, etc.
- Pull cadence:
  - on-demand or scheduled sync
- Store results as snapshots for reproducibility and offline viewing.

### YouTube Reporting API
- Used for bulk historical data (CSV report files).
- Pull cadence:
  - periodic backfills
- Store:
  - report file metadata + SHA-256
  - imported results in SQLite (either normalized tables or stored-as-JSON snapshots plus indices)

### Revenue metrics
- Availability varies by account/program eligibility.
- Strategy:
  - If API provides revenue metrics: store in `revenue_records` (source=api)
  - Else: allow manual CSV import (source=manual_import) with clear labeling.

## Local storage model
- `analytics_snapshots` for dashboard-friendly aggregates.
- `reporting_files` for bulk report artifacts + hashes.
- `revenue_records` keyed by channel + date.

Retention policy:
- Keep snapshots indefinitely by default (local-first).
- Offer pruning tools (RQ-053).

## Dashboards (minimum set)
- Channel overview (last 7/28/90 days):
  - views
  - watch time
  - subscribers gained/lost
  - top videos (by views/watch time)
- Video drilldown:
  - performance over time
  - upload date, publish schedule
  - template/preset lineage (ties back to provenance/originality ledger)

## Comparisons and experiments
- Compare presets/templates:
  - aggregate by template_id and preset_id from build_manifest snapshots
- Batch reports:
  - correlate variant distance metrics with performance (Phase 4 + Phase 6)

## Quota-aware sync
- Track daily budget and used units.
- Avoid high-cost operations (e.g., search.list) unless explicitly requested.
- Provide “sync plan” preview showing estimated quota cost.

## Privacy + security
- Do not store tokens in DB.
- Do not log API responses containing PII beyond what is required.
- Diagnostics export must sanitize channel identifiers unless user opts in.

## Verification (Phase 6 acceptance AT-006)
- Backfill test:
  - one channel, 90 days of data
  - stored locally without corruption
- Privacy tests:
  - no tokens or PII in logs
- Offline dashboard test:
  - dashboards load with network disabled using local DB
