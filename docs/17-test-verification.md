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
  - accessibility and UX workflow state machines
  - diagnostics redaction and packaging manifest generation

### Integration tests (IT-###)
- Exercise adapters and process boundaries.
- Focus:
  - Python worker IPC and caching
  - FFmpeg process + progress parsing + cancel
  - Segment render → encode → concat
  - Secure storage helper end-to-end
  - YouTube upload client against mock server (Phase 5)
  - Analytics ingestion against mock API (Phase 6)
  - onboarding and export operations UX integration (Phase 7)
  - diagnostics and supportability flows (Phase 7)

### Acceptance tests (AT-###)
- End-to-end phase gates.
- Must pass before proceeding to the next phase.
- Includes AT-007 for UX and productization gate coverage.

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
- TS-011 UX token/component state validation
- TS-012 Guided workflow state transitions
- TS-013 Command palette dispatch and history
- TS-014 Accessibility keyboard/focus/contrast checks
- TS-015 Diagnostics redaction + support bundle schema
- TS-016 Packaging manifest determinism

### Integration (IT)
- IT-001 Python analysis worker IPC + caching
- IT-002 FFmpeg progress parsing + cancel
- IT-003 Segment render → encode → concat (crash/resume)
- IT-004 Secure storage helper (keyring) end-to-end
- IT-005 Template rendering (metadata + typography vars)
- IT-006 Resumable upload client (mock server)
- IT-007 Analytics/Reporting ingestion (mock API + DB storage)
- IT-008 First-run onboarding path on clean environment
- IT-009 Export command center recoverability UX
- IT-010 Asset relink + provenance remediation flow
- IT-011 Preset migration UX with mixed schema versions
- IT-012 Accessibility smoke path across critical workflows

### Acceptance (AT)
- AT-001 Phase 1 end-to-end bundle (determinism + resume)
- AT-002 Phase 2 visual modes parity + optional ML
- AT-003 Phase 3 mixer bounce (loop-safe + deterministic)
- AT-004 Phase 4 batch + remix guardrails
- AT-005 Phase 5 YouTube pipeline (OAuth + resumable + quota)
- AT-006 Phase 6 analytics/revenue/niche (official APIs only + privacy)
- AT-007 Phase 7 UX/productization (onboarding + accessibility + supportability)

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
./scripts/test/acceptance_phase_07.sh
```

## V2 Train 0 governance command (required for V2 activation)

```bash
bash scripts/ci/v2_train0_gate.sh
```

Reference:
- `docs/20-phase-blueprint-v2.md`
- `docs/26-v2-test-verification.md`

## Capstone audit automation (post-Phase-7)

```bash
./scripts/test/capstone_baseline.sh
./scripts/test/determinism_rerun.sh
./scripts/test/reliability_longrun.sh
./scripts/test/security_audit.sh
./scripts/test/repo_hygiene_audit.sh
./scripts/test/capstone_audit.sh
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

### Phase 7 (AT-007)
Must verify:
- Onboarding/readiness flow guides first successful export path.
- Export command center provides actionable failure/recovery UX.
- Keyboard-only critical workflow path is complete and free of traps.
- Accessibility checks pass for focus order and contrast policy.
- Diagnostics export remains redacted and support-package schema valid.
- Packaging dry-run emits deterministic manifest output.

## Manual runbooks (required for release confidence)
In addition to automated tests, maintain runbooks:
- Crash/kill/resume export during segment render and during FFmpeg encode.
- Disk full simulation during export.
- Network interruption during resumable upload.
- Keychain locked/unavailable scenarios.
