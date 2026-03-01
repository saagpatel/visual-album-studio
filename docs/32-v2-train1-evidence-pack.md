# V2 Train 1 Evidence Pack

## Objective
Provide auditable evidence that Train 1 (`AT-V2-101`) is closed and compatible with carry-forward strict gates.

## Candidate Context
- Train 1 closure evidence SHA: `e123149a492cf5548352ecbadc93c9c040f9070a`
- Date (UTC): `2026-03-01`

## Commands and Results
1. Train 1 acceptance gate:
   - Command: `bash scripts/test/acceptance_v2_train1.sh`
   - Result: pass (`1 passed`)
2. Strict verify:
   - Command: `env VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh`
   - Result: pass
3. Strict capstone:
   - Command: `env VAS_SECURITY_STRICT=1 VAS_YT_TEST_VIDEO_PATH=/Users/d/Projects/visual-album-studio/out/fixtures/live_test_video_large.mp4 ./scripts/test/capstone_audit.sh`
   - Result: pass
   - `result[live_closeout]=pass`
   - `capstone_finished=2026-03-01T14:26:37Z`

## Evidence Artifacts
- `out/logs/acceptance_v2_train1.log`
- `out/logs/capstone_baseline/capstone_summary.txt`
- `out/logs/capstone_baseline/security_audit_report.txt`
- `out/logs/capstone_baseline/repo_hygiene_report.txt`

## Test/Code References
- `app/tests_py/acceptance/test_atv2101_train1.py`
- `app/tests_py/unit/test_tsv2_101_packaging_signature.py`
- `app/tests_py/integration/test_itv2_103_release_channel_promotion.py`
- `scripts/test/acceptance_v2_train1.sh`

## Exit Criteria Status (Issue #8)
- [x] 4K determinism boundary documentation finalized (see `docs/31-v2-train1-release-runbook.md`)
- [x] Packaging/signing promotion flow + rollback runbook documented
- [x] Key rotation + provenance verification contract documented
- [x] AT-V2-101 evidence pack finalized
- [x] `bash scripts/test/acceptance_v2_train1.sh` pass
- [x] strict verify pass
- [x] strict capstone pass
