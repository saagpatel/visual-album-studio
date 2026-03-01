# Phase Blueprint V2 (Master Plan)

This document defines V2 execution phases, train gates, and cross-phase invariants for the full post-v1 backlog.

Scope source:
- `docs/23-post-v1-backlog.md` (`PV1-001..PV1-008`)
- `docs/22-project-closeout-report.md` (v1 completion baseline)

## V2 order (authoritative)
Train 0 -> Train 1 -> Train 2 -> Train 3 -> Train 4 -> Train 5

## Hard Gate Rules

### Global go/no-go
- `STOP` when any required gate is `fail` or `not-run`.
- `GO` only when train acceptance tests pass and all prior train regression gates remain green.
- `STOP` when any unresolved architecture decision blocks implementation safety.
- `STOP` when a release candidate includes unresolved critical/high security findings.

### Carry-forward v1 invariants
The following must stay green for every V2 release candidate:
- strict verify: `env VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh`
- strict capstone: `env VAS_SECURITY_STRICT=1 VAS_YT_TEST_VIDEO_PATH=/Users/d/Projects/visual-album-studio/out/fixtures/live_test_video_large.mp4 ./scripts/test/capstone_audit.sh`
- `result[acceptance_phase_01..07]=pass`
- `result[live_closeout]=pass`

## Train summaries

### Train 0 — Foundation and Control Plane (Months 1-2)
- Objective: lock V2 requirements, traceability, architecture ADRs, and governance workflows.
- Backlog activation: `PV1-001..PV1-008` promoted from deferred to active V2 scope.
- Gate: `AT-V2-000` (governance and specification readiness).
- Deliverables:
  - `docs/03-requirements-v2.md`
  - `docs/18-traceability-matrix-v2.md`
  - `docs/20-phase-blueprint-v2.md`
  - `docs/25-ui-ux-standards-v2.md`
  - `docs/28-v2-cloud-region-and-residency.md`
  - ADRs for cloud sync + conflict resolution
  - CI workflows for code scanning, dependency review, provenance controls

### Train 1 — 4K + Packaging/Signing (`v2.0`)
- Objective: production-safe 4K lane and signed release flow.
- Scope: `PV1-003`, `PV1-005`
- Gate: `AT-V2-101` (4K determinism + signed package verification).

### Train 2 — Rendering and ML Expansion (`v2.1`)
- Objective: advanced visual modes and ML model manager with provenance safety.
- Scope: `PV1-001`, `PV1-002`
- Gate: `AT-V2-201` (mode parity + ML provenance/safety).

### Train 3 — Distribution and Connector Expansion (`v2.2`)
- Objective: provider abstraction and first two platform expansions.
- Scope: `PV1-004`, `PV1-006`
- Priority providers: TikTok first, Instagram second.
- Gate: `AT-V2-301` (provider publish reliability + policy/privacy compliance).

### Train 4 — Collaboration and Cloud GA (`v2.3`)
- Objective: Supabase-backed sync/collaboration with local-first safety.
- Scope: `PV1-007`, `PV1-008`
- Gate: `AT-V2-401` (collaboration GA + offline-recovery guarantees).

### Train 5 — Hardening and Final GA (`v2.4`)
- Objective: defect burn-down, full rehearse, and immutable V2 closeout.
- Scope: stabilization + evidence closeout.
- Gate: `AT-V2-501` (all V2 suites green on a canonical SHA).

## Required completion conditions for V2
V2 is complete only when all are true:
1. `PV1-001..PV1-008` are delivered and trace-mapped.
2. All `AT-V2-*` gates pass on one canonical SHA.
3. Carry-forward v1 strict verify/capstone pass on same canonical SHA.
4. Security, provenance, and accessibility gates are all green.
5. V2 closeout docs are published and consistent.

## Cross-train invariants
- No plaintext secret storage in DB/files/logs.
- No bypass of deterministic export safety in local workflows.
- Forward-only schema migrations with backup-safe recovery behavior.
- Bundle and manifest schemas remain versioned and backward-readable.
- UI critical states must remain covered: loading, empty, error, success, disabled, focus-visible, keyboard-only.
