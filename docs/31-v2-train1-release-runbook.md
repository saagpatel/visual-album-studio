# V2 Train 1 Release Runbook (4K + Packaging/Signing)

## Purpose
Operational runbook for Train 1 (`AT-V2-101`) release promotion, rollback, and signing/provenance handling.

## Scope
- Requirements:
  - `RQ-V2-101` 4K determinism boundary
  - `RQ-V2-102` 4K long-run reliability
  - `RQ-V2-103` signed artifact production
  - `RQ-V2-104` canary -> beta -> stable promotion controls
  - `RQ-V2-105` ReleaseManifest v2 provenance fields
- Acceptance gate:
  - `bash scripts/test/acceptance_v2_train1.sh`

## Preconditions
1. Working tree clean on candidate branch/SHA.
2. `docs/security-waivers.json` has no active GA waivers.
3. Signing key available as environment secret (`VAS_RELEASE_SIGNING_KEY`).

## Train 1 Execution Sequence
1. Run Train 1 acceptance:
   - `bash scripts/test/acceptance_v2_train1.sh`
2. Run strict verify baseline:
   - `env VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh`
3. Run strict capstone with live validation:
   - `env VAS_SECURITY_STRICT=1 VAS_YT_TEST_VIDEO_PATH=/Users/d/Projects/visual-album-studio/out/fixtures/live_test_video_large.mp4 ./scripts/test/capstone_audit.sh`
4. Confirm gate outcomes:
   - `AT-V2-101` pass
   - strict verify pass
   - `result[live_closeout]=pass`

## 4K Determinism Boundary (Train 1)
1. Determinism assertions are validated by:
   - `app/tests_py/acceptance/test_atv2101_train1.py`
2. Boundary statement:
   - Same input fixtures + same pinned toolchain + same seed path must produce stable checkpoint outputs and equivalent segment plans.
3. Non-goal:
   - Cross-toolchain or cross-driver bit-for-bit guarantees outside pinned baseline are not claimed by Train 1.

## Promotion Controls
1. Allowed forward progression:
   - `canary -> beta -> stable`
2. Promotion must include a passing gate report (`AT-V2-101`) and signature verification.
3. Reference implementation checks:
   - `app/tests_py/integration/test_itv2_103_release_channel_promotion.py`
   - `app/tests_py/unit/test_tsv2_101_packaging_signature.py`

## Rollback Procedure
1. Trigger rollback when:
   - signature verification fails,
   - release gate report invalid,
   - post-promotion smoke indicates regression.
2. Roll back one step only:
   - `stable -> beta` or `beta -> canary`
3. Re-run:
   - Train 1 acceptance + strict verify.

## Signing and Provenance Contract
1. Release manifest schema must be v2 and include provenance fields.
2. Signature payload requirements:
   - manifest digest recorded,
   - signer id recorded,
   - verification-required policy true for promotion.
3. Key rotation policy (single-owner baseline):
   - rotate key before each major release train or immediately upon compromise suspicion.
   - post-rotation: rerun `AT-V2-101` and strict verify.

## Failure Handling (RCA)
1. Stop promotion immediately on any failed required gate.
2. Document RCA in `docs/STATUS.md`.
3. Apply minimal safe fix.
4. Re-run failed gate and downstream strict verify/capstone before resuming.
