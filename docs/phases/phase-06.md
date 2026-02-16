# Phase 6 — Analytics, Niche Research, Revenue

## Objectives
- Close the loop with local analytics dashboards and revenue tracking.
- Provide niche research support that is quota-aware and works offline.
- Maintain privacy and policy compliance: **official APIs only**, no scraping.

## Included modules / features
- **O** Niche analyzer
- **P** Analytics dashboard
- **Q** Revenue tracking
- **J** Asset usage analytics extensions

## Deliverables (testable)

### D1 — Local analytics dashboards (RQ-029)
- Dashboards load from local SQLite instantly.
- Provide last-synced timestamps and manual sync triggers.

### D2 — Bulk analytics ingestion (RQ-030)
- Reporting API bulk CSV ingestion for historical storage.
- Backfill workflow for 90 days.

### D3 — Revenue tracking with graceful fallback (RQ-031)
- Store revenue metrics where accessible.
- Manual CSV import path when revenue metrics are unavailable.
- Clear labeling of data sources and limitations.

### D4 — Niche analyzer notebook (RQ-032)
- Keyword notebook + competitor notes work offline.
- Optional API-assisted search/list:
  - explicit quota accounting
  - user-invoked only

### D5 — Privacy + retention controls
- Pruning tools for analytics data and caches.
- Diagnostics export sanitization confirmed.

## Acceptance criteria (measurable)

### A1 — Dashboard performance and offline behavior
- Dashboard loads from local DB instantly (no network required to view).
- Sync runs incrementally and does not corrupt stored data.

### A2 — Backfill reliability
- One channel, 90 days of data ingested and stored without corruption.
- Incremental sync avoids duplicates.

### A3 — Policy compliance
- No scraping of YouTube Studio.
- Only official APIs are used.

### A4 — Privacy
- No tokens or PII in logs.
- Diagnostics export contains no secrets.

## Verification plan

### Automated
- Integration:
  - IT-007 mock API ingestion into SQLite
- Acceptance:
  - **AT-006**
- Regression:
  - AT-001..AT-005 must still pass (no regressions)

### Manual checks
- Account with limited revenue access:
  - confirm graceful “not available” UX
- Large DB:
  - run prune operations and verify integrity

## Dependencies / prerequisites
- Phase 5 OAuth + channel bindings (L/M).
- Stable SQLite schema and migrations.

## Risks + mitigation tasks
- Data availability varies:
  - degrade gracefully and label clearly
- Storage growth:
  - prune and archive options
- Quota constraints:
  - budget model + user-invoked operations

## Explicit out-of-scope
- UX platform and productization enhancements (Phase 7).
