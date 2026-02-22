# Visual Album Studio — STATUS

**Project:** Visual Album Studio
**Current state:** Phase 7 complete on product paths; production-hardening sprint in progress on `codex/bootstrap-tests-docs-v1` (not yet merged to `main`)
**Last updated:** 2026-02-22

## Rebaseline Summary
- Historical harness-based acceptance passes were previously recorded, but they are not treated as final phase closure for product-grade runtime criteria.
- Authoritative closure is now based on product-path execution through Godot core services (`app/src/core`) and adapters (`app/src/adapters`) as defined in docs.
- Gate policy remains strict: no phase advancement until the current phase acceptance gate passes and prior gates remain green.

## Hardening Sprint Snapshot (2026-02-22)
- [x] CI quality workflow aligned to repo-native verification flow (`.github/workflows/quality-gates.yml` no longer uses Node lockfile-dependent install steps).
- [x] Security audit strict mode (`VAS_SECURITY_STRICT=1`) now passes with no active waiver entries in `docs/security-waivers.json`.
- [x] FFmpeg checksum placeholders removed from `tools/ffmpeg/checksums.json`; bootstrap enforces non-placeholder checksum policy and verifies managed binary when present.
- [x] YouTube runtime adapter upgraded from mock-only methods to a production envelope contract (`ok`, `error_code`, `http_status`, `retryable`, `data`) via `scripts/youtube_adapter.py` bridge.
- [x] Publish core received upload step APIs (`start_upload_session`, `resume_upload_step`, `finalize_upload`) wired to adapter contract.
- [x] Legacy core_py security findings remediated (mapping eval removed, subprocess boundaries validated, assert runtime guards replaced).
- [x] Live validation TLS trust path hardened in `scripts/test/live_validation.py` (CA bundle resolution via `VAS_SSL_CA_BUNDLE`/`SSL_CERT_FILE`/`certifi`).
- [x] Regression confidence rerun:
  - `bash .codex/scripts/run_verify_commands.sh` passed
  - `./scripts/test/capstone_audit.sh` passed with `live_closeout=pass` when `scripts/test/live.env` is present

## Historical Note (non-gating)
- Legacy harness suites in `app/tests_py/**` and acceptance wrappers in `scripts/test/acceptance_phase_0*.sh` previously passed on 2026-02-16.
- These historical results are retained for regression context only and do not count as product-grade gate completion.

## Phase Gate Status

## Active Review Gate (Phase 7)
- Goal: Implement UX platform + productization scope while preserving all Phases 1-6 reliability and security guarantees.
- Success metrics: `AT-007` passes and `AT-001..AT-006` remain green.
- Constraints: no business logic in UI, no plaintext secrets, no regressions in segment-resume/export correctness.
- Must in scope: design-system baseline, onboarding/readiness, guided workflow, command center, accessibility baseline, diagnostics redaction UX, packaging dry-run.
- Deferred from this gate: any scope outside `docs/phases/phase-07.md` and `RQ-056..RQ-066`.
- Stop conditions: export reliability regression, accessibility gate failures, diagnostics redaction leakage.
- Verification commands:
  - `./scripts/test/unit.sh`
  - `./scripts/test/integration.sh`
  - `./scripts/test/acceptance_phase_07.sh`

### Stage A — Rebaseline and Hygiene Correction
- [x] STATUS truth reset to product-grade re-gating
- [x] Historical harness-pass note preserved as non-gating
- [x] Repo hygiene verified for generated artifacts (`out/**`, keyring target, caches)
- [x] Acceptance flow fully de-coupled from harness-only closure semantics

### Stage B — Runtime Migration (Godot Core Authoritative)
- [x] Domain logic migrated from `app/src/core_py/vas_studio/*.py` to `app/src/core/*.gd` for phase-gated paths
- [x] Python reserved to worker scope only (`worker/vas_audio_worker`) for product-path gates
- [x] Product-path test harness established and runnable headless via Godot
- [x] AT scripts execute product path as primary gate path

### Phase 1 Re-Gate (AT-001)
- [x] SQLite migration runner and schema validation on product path
- [x] Asset import/dedupe/provenance gating on product path
- [x] Worker IPC + analysis cache on product path
- [x] Mapping registry + deterministic evaluator on product path
- [x] Motion Poster mode v1 presets + deterministic checkpoints
- [x] Segment render -> encode -> concat -> bundle on product path
- [x] AT-001 pass (product path)

### Phase 2 Re-Gate (AT-002)
- [x] Particles, Landscape, Photo Tier-0 on product path
- [x] Mapping/preset v2 validation + migration rules
- [x] Migration `002_phase2.sql` implemented and tested
- [x] AT-002 pass (product path)
- [x] AT-001 regression pass

### Phase 3 Re-Gate (AT-003)
- [x] Mixer model/UI + persistence on product path
- [x] Deterministic bounce integration in export path
- [x] Migration `003_phase3.sql` implemented and tested
- [x] AT-003 pass (product path)
- [x] AT-001/AT-002 regression pass

### Phase 4 Re-Gate (AT-004)
- [x] Variant graph + batch planner/executor + guardrails
- [x] Queue reliability upgrades and stress suite
- [x] Migration `004_phase4.sql` implemented and tested
- [x] AT-004 pass (product path)
- [x] AT-001..AT-003 regression pass

### Phase 5 Re-Gate (AT-005)
- [x] OAuth + PKCE + loopback flow on product path
- [x] Keyring-backed token lifecycle (no plaintext)
- [x] Resumable upload persistence/restart recovery
- [x] Migration `005_phase5.sql` implemented and tested
- [x] AT-005 pass (product path; live validation cleared)
- [x] AT-001..AT-004 regression pass

### Phase 6 Re-Gate (AT-006)
- [x] Analytics/revenue/niche product-path implementations
- [x] Retention/pruning/backup paths + privacy validation
- [x] Migration `006_phase6.sql` implemented and tested
- [x] AT-006 pass (product path; live validation cleared)
- [x] AT-001..AT-005 regression pass

### Phase 7 (AT-007)
- [x] UX platform and design-system implementation
- [x] Guided onboarding + workflow acceleration
- [x] Export Command Center UX and recovery surfaces
- [x] Accessibility baseline and command palette
- [x] Diagnostics/supportability UX + packaging readiness
- [x] AT-007 pass (product path)
- [x] AT-001..AT-006 regression pass

## Phase Evidence
- Verification commands run:
  - `./scripts/test/unit.sh`
  - `./scripts/test/integration.sh`
  - `./scripts/test/acceptance_phase_01.sh`
  - `./scripts/test/acceptance_phase_02.sh`
  - `./scripts/test/acceptance_phase_03.sh`
  - `./scripts/test/acceptance_phase_04.sh`
  - `./scripts/test/acceptance_phase_05.sh`
  - `./scripts/test/acceptance_phase_06.sh`
  - `./scripts/test/acceptance_phase_07.sh`
  - `./scripts/test/determinism_rerun.sh`
  - `./scripts/test/reliability_longrun.sh`
  - `./scripts/test/security_audit.sh`
  - `./scripts/test/repo_hygiene_audit.sh`
  - `./scripts/test/capstone_audit.sh`
- Product-path logs:
  - `out/logs/acceptance_phase_01_product.log`
  - `out/logs/acceptance_phase_02_product.log`
  - `out/logs/acceptance_phase_03_product.log`
  - `out/logs/acceptance_phase_04_product.log`
  - `out/logs/acceptance_phase_05_product.log`
  - `out/logs/acceptance_phase_06_product.log`
  - `out/logs/acceptance_phase_07_product.log`
  - `out/logs/capstone_baseline/capstone_summary.txt`
  - `out/logs/capstone_baseline/security_audit_report.txt`
  - `out/logs/capstone_baseline/repo_hygiene_report.txt`
  - `out/logs/capstone_baseline/determinism_rerun.log`
  - `out/logs/capstone_baseline/reliability_longrun.log`
- Pinned toolchain verification:
  - `PATH="/Users/d/Projects/visual-album-studio/out/tools/godot44/bin:$PATH" ./scripts/test/unit.sh`
  - `PATH="/Users/d/Projects/visual-album-studio/out/tools/godot44/bin:$PATH" ./scripts/test/integration.sh`
  - `PATH="/Users/d/Projects/visual-album-studio/out/tools/godot44/bin:$PATH" ./scripts/test/acceptance_phase_01.sh` … `acceptance_phase_06.sh`
  - Result: all passed on `Godot v4.4.stable.official.4c311cbee`

## Live Validation Automation
- Added executable live validation scripts:
  - `scripts/test/live_phase_05.sh`
  - `scripts/test/live_phase_06.sh`
  - `scripts/test/live_closeout.sh`
  - `scripts/test/live_validation.py`
  - `scripts/test/live.env.example`
- Latest run results:
  - `./scripts/test/live_phase_05.sh` => passed (exit 0)
  - `./scripts/test/live_phase_06.sh` => passed (exit 0)
  - `./scripts/test/live_closeout.sh` => passed (exit 0)
- Evidence files:
  - `out/logs/live_phase_05_report.json`
  - `out/logs/live_phase_06_report.json`
  - `out/logs/live_phase_05.log`
  - `out/logs/live_phase_06.log`

## Pending Live Validation
- Cleared on 2026-02-16 after successful live matrix execution for Phase 5 and Phase 6.
- Phase 5 report summary: `pass=2`, `fail=0`, `skip=1` (`youtube_resumable_upload` skipped because `VAS_YT_TEST_VIDEO_PATH` was unset).
- Phase 6 report summary: `pass=2`, `fail=0`, `skip=1` (`youtube_revenue_metric` skipped with `403`, allowed by matrix policy).
- Capstone rerun note: `./scripts/test/capstone_audit.sh` executed `live_closeout.sh` in pending-prerequisites mode due missing local env vars on that run; this does not reopen Phase 5/6 because live validation was already cleared above.

## Risk Closure Updates
- Closed: branch hygiene cleanup complete; local branches reduced to `main` only.
- Closed: pinned Godot `4.4.x` gate rerun completed successfully.
- Closed: live provider validation blocker for Phase 5/6.
- Closed: strict Bandit waiver burn-down complete; strict security audit now passes without `bandit_findings` waiver.
- Closed: capstone live-closeout pending state on credentialed environments (`scripts/test/capstone_audit.sh` now sources `scripts/test/live.env` when available).
- Open follow-up (LOW): Rust transitive advisory lifecycle tracking issue [#1](https://github.com/saagar210/visual-album-studio/issues/1) for warning-level upstream maintenance advisories in the keyring dependency graph.
- Open follow-up (MEDIUM): mainline truth drift remains; hardening changes currently exist on `codex/bootstrap-tests-docs-v1` and require merge/sync to `main`.

## Assumptions made (append-only)
- ASM-200: Python harness remains temporarily as non-gating support while product-path gates are migrated to Godot.
- ASM-201: Phase 5 and Phase 6 may be provisionally marked `PENDING_LIVE_VALIDATION` when live API validation is unavailable.
- ASM-202: Final 100% completion requires all `PENDING_LIVE_VALIDATION` tags to be cleared.
- ASM-203: No new product requirements are introduced beyond `docs/**`.
- ASM-204: Continuous execution proceeds phase-by-phase, with blocker-aware parallelization inside phase boundaries only.
- ASM-205: Strict security mode in CI permits only explicit time-boxed waivers documented in `docs/security-waivers.json`.
