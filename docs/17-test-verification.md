# Test & Verification Plan

This document defines the verification strategy for every phase, including unit/integration/acceptance tests and golden fixtures.

## Test pyramid

### Unit tests (TS-###)
- Fast, deterministic.
- Run on every change.
- Focus:
  - pure mapping evaluator
  - schema/migrations
  - manifest/provenance validators
  - job state machine
  - quota calculator
  - variant distance metric

### Integration tests (IT-###)
- Exercise adapters and process boundaries.
- Focus:
  - Python worker IPC and caching
  - FFmpeg process + progress parsing + cancel
  - Segment render → encode → concat
  - Secure storage helper end-to-end
  - YouTube upload client against mock server (Phase 5)
  - Analytics ingestion against mock API (Phase 6)

### Acceptance tests (AT-###)
- End-to-end phase gates.
- Must pass before proceeding to the next phase.

## Golden fixtures

### Golden projects (render determinism)
Golden projects are fixed inputs that validate:
- preview/offline parity
- determinism checkpoint hashes
- export correctness

Location (planned):
- `app/tests/fixtures/golden_projects/`

Each golden project includes:
- `project.json` (snapshot)
- referenced assets (small test assets)
- expected checkpoint hashes for the pinned environment
- expected bundle structure + schema validation

## Test IDs (authoritative catalog)

### Unit (TS)
- TS-001 Asset hashing + dedupe
- TS-002 Mapping DSL parse/evaluate determinism
- TS-003 Parameter registry validation + migrations
- TS-004 Job state machine + persistence
- TS-005 Bundle manifest + schema validation
- TS-006 License provenance validator
- TS-007 Variant distance metric + guardrails
- TS-008 SQLite migration runner
- TS-009 Keyring CLI wrapper API
- TS-010 Quota calculator + throttling rules

### Integration (IT)
- IT-001 Python analysis worker IPC + caching
- IT-002 FFmpeg progress parsing + cancel
- IT-003 Segment render → encode → concat (crash/resume)
- IT-004 Secure storage helper (keyring) end-to-end
- IT-005 Template rendering (metadata + typography vars)
- IT-006 Resumable upload client (mock server)
- IT-007 Analytics/Reporting ingestion (mock API + DB storage)

### Acceptance (AT)
- AT-001 Phase 1 end-to-end bundle (determinism + resume)
- AT-002 Phase 2 visual modes parity + optional ML
- AT-003 Phase 3 mixer bounce (loop-safe + deterministic)
- AT-004 Phase 4 batch + remix guardrails
- AT-005 Phase 5 YouTube pipeline (OAuth + resumable + quota)
- AT-006 Phase 6 analytics/revenue/niche (official APIs only + privacy)

## Commands (required)

The implementation must provide these scripts:

```bash
./scripts/test/unit.sh
./scripts/test/integration.sh

./scripts/test/acceptance_phase_01.sh
./scripts/test/acceptance_phase_02.sh
./scripts/test/acceptance_phase_03.sh
./scripts/test/acceptance_phase_04.sh
./scripts/test/acceptance_phase_05.sh
./scripts/test/acceptance_phase_06.sh
```

## Phase-by-phase verification details

### Phase 1 (AT-001)
Must verify:
- Import audio → canonical WAV cache (TS-001, IT-001)
- Analysis cached (BPM + beat grid) with version invalidation (IT-001)
- Motion Poster renders and exports with determinism checkpoints (TS-002/005, AT-001)
- Segment-based resume and cancel safety (IT-002/003, AT-001)
- Bundle schema and provenance gating (TS-005/006, AT-001)

Expected artifacts:
- `out/exports/<export_id>/video.mp4`
- `.../thumbnail.png`
- `.../metadata.json`
- `.../provenance.json`
- `.../build_manifest.json`

### Phase 2 (AT-002)
Must verify:
- Particles mode exports parity + determinism
- Landscape mode exports parity + determinism
- Photo animator Tier 0 works without ML models
- Optional ML tier can be enabled with explicit model download and provenance recording (if implemented)
- Preset migrations preserve output within defined tolerances

### Phase 3 (AT-003)
Must verify:
- Mixer supports 20-track project
- Offline bounce deterministic (hash stable)
- Loop-safe boundary sample-level test passes
- Export muxes bounced WAV correctly and stays in sync

### Phase 4 (AT-004)
Must verify:
- Batch of 100 renders completes with <2% failure rate
- Failures are recoverable via retry
- No orphan temp files beyond threshold
- Guardrails enforce variant distance rules; near-duplicates rejected/flagged
- Reviewer report generated

### Phase 5 (AT-005)
Must verify:
- OAuth installed-app flow uses system browser + loopback redirect
- Tokens stored in keychain only; no plaintext tokens in DB/logs
- Resumable uploads resume after interruption
- Scheduling constraints enforced and publishAt applied correctly
- Wrong-channel prevention: explicit binding required
- Quota estimation and throttling work (mocked or controlled test environment)

### Phase 6 (AT-006)
Must verify:
- Analytics dashboard loads instantly from local DB
- 90-day backfill stored without corruption
- Revenue tracking degrades gracefully with manual import path
- Niche analyzer quota-aware
- No scraping of YouTube Studio
- Privacy tests pass (no tokens/PII in logs/diagnostics)

## Manual runbooks (required for release confidence)
In addition to automated tests, maintain runbooks:
- Crash/kill/resume export during segment render and during FFmpeg encode.
- Disk full simulation during export.
- Network interruption during resumable upload.
- Keychain locked/unavailable scenarios.
