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

## Cycle completion delivered tests (2026-03-01)
### NC-001
- `app/tests_py/unit/test_tsnc_001_dr_rehearsal_runner.py`
- `app/tests_py/integration/test_itnc_001_dr_rehearsal_report_persistence.py`
- `app/tests_py/acceptance/test_atnc_001_dr_rehearsal_runner.py`
- `scripts/test/acceptance_nc_001.sh`

### NC-002
- `app/tests_py/unit/test_tsnc_002_anomaly_triage_recommendations.py`
- `app/tests_py/integration/test_itnc_002_anomaly_triage_history.py`
- `app/tests_py/acceptance/test_atnc_002_anomaly_auto_triage.py`
- `scripts/test/acceptance_nc_002.sh`

### NC-101
- `app/tests_py/unit/test_tsnc_101_preset_trust_state_matrix.py`
- `app/tests_py/integration/test_itnc_101_preset_trust_with_exchange.py`
- `app/tests_py/acceptance/test_atnc_101_preset_exchange_trust_ui.py`
- `scripts/test/acceptance_nc_101.sh`

### NC-102
- `app/tests_py/unit/test_tsnc_102_scheduler_dashboard_timeline.py`
- `app/tests_py/integration/test_itnc_102_scheduler_dashboard_policy_overlay.py`
- `app/tests_py/acceptance/test_atnc_102_scheduler_simulation_dashboard.py`
- `scripts/test/acceptance_nc_102.sh`

### NC-103
- `app/tests_py/unit/test_tsnc_103_timeline_ordering.py`
- `app/tests_py/integration/test_itnc_103_timeline_conflict_replay.py`
- `app/tests_py/acceptance/test_atnc_103_collab_timeline_visualizer.py`
- `scripts/test/acceptance_nc_103.sh`

### NC-201
- `app/tests_py/unit/test_tsnc_201_provider_feature_flags.py`
- `app/tests_py/integration/test_itnc_201_distribution_feature_flag_enforcement.py`
- `app/tests_py/acceptance/test_atnc_201_provider_feature_flags.py`
- `scripts/test/acceptance_nc_201.sh`

### NC-202
- `app/tests_py/unit/test_tsnc_202_residency_templates_validation.py`
- `app/tests_py/integration/test_itnc_202_apply_residency_template.py`
- `app/tests_py/acceptance/test_atnc_202_residency_policy_templates.py`
- `scripts/test/acceptance_nc_202.sh`

### NC-203
- `app/tests_py/unit/test_tsnc_203_audit_export_manifest.py`
- `app/tests_py/integration/test_itnc_203_audit_export_generation.py`
- `app/tests_py/acceptance/test_atnc_203_audit_dashboard_export_bundle.py`
- `scripts/test/acceptance_nc_203.sh`

## Evidence paths
- `out/logs/acceptance_nc_003.log`
- `out/logs/acceptance_nc_001.log`
- `out/logs/acceptance_nc_002.log`
- `out/logs/acceptance_nc_101.log`
- `out/logs/acceptance_nc_102.log`
- `out/logs/acceptance_nc_103.log`
- `out/logs/acceptance_nc_201.log`
- `out/logs/acceptance_nc_202.log`
- `out/logs/acceptance_nc_203.log`
- `out/logs/capstone_baseline/capstone_summary.txt`
- `out/logs/capstone_baseline/security_audit_report.txt`
- `out/logs/capstone_baseline/repo_hygiene_report.txt`
