# Next-Cycle Test and Verification Plan

## Carry-forward strict commands (mandatory)
- `env VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh`
- `env VAS_SECURITY_STRICT=1 VAS_YT_TEST_VIDEO_PATH=/Users/d/Projects/visual-album-studio/out/fixtures/live_test_video_large.mp4 ./scripts/test/capstone_audit.sh`

## Next-cycle acceptance command catalog
- `bash scripts/test/acceptance_nc_001.sh` -> `AT-NC-001`
- `bash scripts/test/acceptance_nc_002.sh` -> `AT-NC-002`
- `bash scripts/test/acceptance_nc_003.sh` -> `AT-NC-003`
- `bash scripts/test/acceptance_nc_101.sh` -> `AT-NC-101`
- `bash scripts/test/acceptance_nc_102.sh` -> `AT-NC-102`
- `bash scripts/test/acceptance_nc_103.sh` -> `AT-NC-103`
- `bash scripts/test/acceptance_nc_201.sh` -> `AT-NC-201`
- `bash scripts/test/acceptance_nc_202.sh` -> `AT-NC-202`
- `bash scripts/test/acceptance_nc_203.sh` -> `AT-NC-203`

## Gate order for each item
1. Item acceptance command(s)
2. `env VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh`
3. `env VAS_SECURITY_STRICT=1 VAS_YT_TEST_VIDEO_PATH=/Users/d/Projects/visual-album-studio/out/fixtures/live_test_video_large.mp4 ./scripts/test/capstone_audit.sh`

## Cycle-start delivered tests
### NC-003
- `app/tests_py/unit/test_tsnc_003_provider_policy_diff.py`
- `app/tests_py/integration/test_itnc_003_provider_policy_changelog.py`
- `app/tests_py/acceptance/test_atnc_003_provider_policy_diff_watcher.py`
- `scripts/test/acceptance_nc_003.sh`

## Evidence paths
- `out/logs/acceptance_nc_003.log`
- `out/logs/capstone_baseline/capstone_summary.txt`
- `out/logs/capstone_baseline/security_audit_report.txt`
- `out/logs/capstone_baseline/repo_hygiene_report.txt`
