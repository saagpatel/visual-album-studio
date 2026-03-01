# V2 Test and Verification Plan

This document defines V2 test IDs, gate scenarios, and command contracts layered on top of existing strict v1 verification.

## Command baseline
Carry-forward mandatory commands:
- `env VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh`
- `env VAS_SECURITY_STRICT=1 VAS_YT_TEST_VIDEO_PATH=/Users/d/Projects/visual-album-studio/out/fixtures/live_test_video_large.mp4 ./scripts/test/capstone_audit.sh`

Train 0 governance contract:
- `bash scripts/ci/v2_train0_gate.sh`

Train 1 acceptance contract:
- `bash scripts/test/acceptance_v2_train1.sh`
  - uses `VAS_RELEASE_SIGNING_KEY` when available
  - falls back to CI-local deterministic key only for test execution

## V2 gate catalog

### Train 0
- `AT-V2-000`: governance and specification readiness
- Required checks:
  - V2 docs baseline files present
  - cloud/conflict ADRs present
  - governance workflows present
  - quality pipeline includes Train 0 gate

### Train 1
- `AT-V2-101`: 4K lane + packaging/signing
- Required checks:
  - 4K determinism fixture reruns
  - 4K long-run interruption/resume
  - signed package verification and channel promotion checks
  - command: `bash scripts/test/acceptance_v2_train1.sh`

### Train 2
- `AT-V2-201`: rendering/ML expansion
- Required checks:
  - parity + determinism for new modes
  - model provenance/license policy checks
  - fallback behavior for missing model assets

### Train 3
- `AT-V2-301`: provider expansion
- Required checks:
  - TikTok publish lane end-to-end
  - Instagram publish lane end-to-end
  - quota/policy failure taxonomy assertions
  - privacy/redaction checks across connector logs/diagnostics

### Train 4
- `AT-V2-401`: collaboration and cloud GA
- Required checks:
  - offline edits and reconnect replay
  - deterministic conflict resolution scenarios
  - RBAC enforcement assertions
  - cloud outage fail-safe fallback to local mode

### Train 5
- `AT-V2-501`: final candidate closeout
- Required checks:
  - all prior `AT-V2-*` green
  - carry-forward v1 strict verify + capstone green on same SHA
  - accessibility, provenance, and security gates green

## Scenario matrix (mandatory)
1. 4K 2h export interruption/resume.
2. Signed package build/verify/promote/rollback.
3. Concurrent edits with deterministic conflict outcomes.
4. Offline edit then reconnect replay without data loss.
5. Provider quota exhaustion and policy failure behavior.
6. Cloud outage while local workflows continue.
7. Sensitive-data leak regression scans.
8. Keyboard-only critical workflow verification.

## Release blockers
- Any required gate result is `fail` or `not-run`.
- Any open critical/high security issue without explicit temporary RC waiver.
- Any unresolved determinism drift on baseline fixtures.
- Any unresolved critical accessibility issue on core workflows.
