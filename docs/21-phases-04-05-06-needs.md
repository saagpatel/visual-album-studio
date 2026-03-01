# Phase 4-6 Delivery Needs (Post-Phase-0 Baseline)

This document defines what must be in place to execute Phase 4, Phase 5, and Phase 6 with production-ready evidence quality.

Status reference:
- Baseline hardening and gate integrity are tracked in `docs/STATUS.md`.
- Risk context is tracked in `docs/19-risk-register.md`.
- Acceptance contracts are defined in `docs/phases/phase-04.md`, `docs/phases/phase-05.md`, and `docs/phases/phase-06.md`.
- Closeout constants:
  - `CLOSEOUT_DATE_UTC=2026-03-01`
  - `CLOSEOUT_EVIDENCE_SHA=241dd383d7d63ed19c333873949a59902e5b29cc`
  - `CLOSEOUT_TARGET_TAG=closeout-2026-03-01`

## Phase 4 (Automation: Batch + Remix + Guardrails)

### Objective
Ship deterministic, recoverable high-volume automation (`AT-004`) with clear anti-spam guardrails and reviewer output.

### What we need before execution
1. Pinned-toolchain CI acceptance lane for `AT-001` and `AT-007` to detect regressions before batch/remix changes.
2. Determinism evidence policy for repeated run comparisons (same input + same pin = stable manifests/checkpoints).
3. Batch failure triage rubric (retryable vs non-retryable) linked to runbook IDs.
4. Reviewer report schema validation in CI for batch outputs.

### Required implementation/gate outputs
1. `AT-004` pass on product path with reviewer report generated.
2. Determinism rerun pass after any batch/remix change.
3. Reliability longrun pass after queue/scheduler changes.
4. Risk controls validated for:
   - `RSK-001` determinism drift
   - `RSK-006` template spam/reuse risk
   - `RSK-024` release artifact nondeterminism

### Exit criteria
1. Full capstone remains green after Phase 4 changes.
2. Batch reviewer report is deterministic for fixed inputs/toolchain.
3. No new high/critical security findings.

## Phase 5 (Optional YouTube Publishing + Multi-Channel)

### Objective
Maintain reliable publish flows under real provider conditions while preserving token privacy and wrong-channel protections.

### What we need before execution
1. Stable live validation credentials in `scripts/test/live.env` with periodic refresh owner.
2. Test video fixture path set for resumable interruption/resume validation (`VAS_YT_TEST_VIDEO_PATH`).
3. Channel-binding policy assertions in acceptance coverage (wrong-channel prevention).
4. Quota budget test matrix (normal, near-limit, exhausted).

### Required implementation/gate outputs
1. `AT-005` pass on product path.
2. `scripts/test/live_phase_05.sh` pass, with only policy-allowed skips.
3. `scripts/test/live_closeout.sh` pass in capstone context.
4. Strict security audit pass with no plaintext token storage regressions.

### Exit criteria
1. OAuth + publish + metadata flows pass with retryable/non-retryable errors mapped correctly.
2. Resumable upload survives interruption and resumes correctly.
3. Channel guard failure path is explicit and test-proven.

## Phase 6 (Analytics + Niche + Revenue)

### Objective
Provide quota-aware, privacy-safe analytics/revenue features that degrade gracefully when APIs are unavailable.

### What we need before execution
1. Live analytics account permissions verified for metrics and reporting endpoints.
2. Documented skip policy for account-limited APIs (e.g., revenue metric 403).
3. Backfill/storage integrity checks for 90-day windows.
4. Privacy redaction checks included in analytics diagnostics paths.

### Required implementation/gate outputs
1. `AT-006` pass on product path.
2. `scripts/test/live_phase_06.sh` pass, with any skips documented and policy-accepted.
3. Capstone pass with `live_closeout=pass` (or explicit owner+expiry pending waiver if provider outage blocks run).
4. No regressions in retention/pruning behavior or diagnostics redaction.

### Exit criteria
1. Analytics dashboard paths behave correctly for both available and unavailable account states.
2. Revenue paths are stable when data exists and safe when access is denied.
3. Privacy and token handling remain compliant with security contract.

## Cross-Phase Dependencies (4 -> 5 -> 6)

1. Phase 4 release engineering controls must be active before final Phase 5/6 certification.
2. Live validation reliability (credential + TLS trust + environment) must stay green throughout Phase 5/6.
3. Any required gate with `fail` or `not-run` blocks progression unless a time-boxed waiver is documented with owner and expiry.

## PM Go/No-Go Checklist for 4-6

1. Are pinned-toolchain CI smoke checks active and green?
2. Are strict security scans green with no active temporary waivers?
3. Is live closeout passing from capstone on the current candidate SHA?
4. Are all required AT gates (`AT-004`, `AT-005`, `AT-006`) green on product paths?
5. Are remaining open risks only Low/accepted with owners and dates?

## Final PM Go/No-Go Decision (2026-03-01)

Candidate evaluated: `241dd383d7d63ed19c333873949a59902e5b29cc`

Decision: **GO-COMPLETE**

Checklist outcomes:
1. Pinned-toolchain CI smoke checks active and green?
   - **Yes**
   - Evidence: `docs/STATUS.md` (Phase Evidence + Pinned toolchain verification), `.github/workflows/quality-gates.yml`
2. Strict security scans green with no active temporary waivers?
   - **Yes**
   - Evidence: `env VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh` pass, `docs/security-waivers.json` empty
3. Live closeout passing from capstone on candidate SHA?
   - **Yes**
   - Evidence: `out/logs/capstone_baseline/capstone_summary.txt` with `result[live_closeout]=pass`, capstone finish `2026-03-01T06:14:50Z`
4. Required AT gates (`AT-004`, `AT-005`, `AT-006`) green on product paths?
   - **Yes**
   - Evidence: capstone summary includes `result[acceptance_phase_04]=pass`, `result[acceptance_phase_05]=pass`, `result[acceptance_phase_06]=pass`
5. Remaining open risks only Low/accepted with owners and dates?
   - **Yes**
   - Evidence: owners remain assigned in `docs/19-risk-register.md`; residual-risk acceptance captured in `docs/22-project-closeout-report.md`
