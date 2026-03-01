# Post-V2 Test and Verification Plan

This document defines Post-V2 gate contracts and execution order for `PV2-001/002/101/102/201/202`.

## Command baseline (carry-forward mandatory)
- `bash scripts/ci/v2_train0_gate.sh`
- `bash scripts/test/acceptance_v2_train1.sh`
- `./scripts/test/unit.sh`
- `./scripts/test/integration.sh`
- `./scripts/test/security_audit.sh`
- `./scripts/test/repo_hygiene_audit.sh`
- `env VAS_SECURITY_STRICT=1 VAS_YT_TEST_VIDEO_PATH=/Users/d/Projects/visual-album-studio/out/fixtures/live_test_video_large.mp4 ./scripts/test/capstone_audit.sh`

## Post-V2 acceptance command catalog
- `bash scripts/test/acceptance_pv2_001.sh` -> `AT-PV2-001`
- `bash scripts/test/acceptance_pv2_002.sh` -> `AT-PV2-002`
- `bash scripts/test/acceptance_pv2_101.sh` -> `AT-PV2-101`
- `bash scripts/test/acceptance_pv2_102.sh` -> `AT-PV2-102`
- `bash scripts/test/acceptance_pv2_201.sh` -> `AT-PV2-201`
- `bash scripts/test/acceptance_pv2_202.sh` -> `AT-PV2-202`

## Gate execution order
1. Current wave acceptance command(s).
2. Carry-forward strict verification stack:
   - `env VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh`
3. Strict capstone:
   - `env VAS_SECURITY_STRICT=1 VAS_YT_TEST_VIDEO_PATH=/Users/d/Projects/visual-album-studio/out/fixtures/live_test_video_large.mp4 ./scripts/test/capstone_audit.sh`
4. Confirm capstone markers:
   - `result[live_closeout]=pass`
   - `capstone_finished=<UTC timestamp>`

## Required test assets by backlog item

### PV2-001
- `app/tests_py/acceptance/test_atpv2_001_model_autoselection_completion.py`
- `app/tests_py/unit/test_tspv2_001_selection_policy.py`
- `app/tests_py/integration/test_itpv2_001_eval_ingestion_and_drift_guard.py`

### PV2-002
- `app/tests_py/acceptance/test_atpv2_002_style_exchange.py`
- `app/tests_py/unit/test_tspv2_002_preset_bundle_schema.py`
- `app/tests_py/integration/test_itpv2_002_permission_and_signature_paths.py`

### PV2-101
- `app/tests_py/acceptance/test_atpv2_101_provider_expansion.py`
- `app/tests_py/integration/test_itpv2_101_facebook_reels_publish_flow.py`
- `app/tests_py/integration/test_itpv2_101_x_publish_flow.py`
- `app/tests_py/integration/test_itpv2_101_provider_policy_redaction.py`

### PV2-102
- `app/tests_py/acceptance/test_atpv2_102_scheduler_optimization.py`
- `app/tests_py/unit/test_tspv2_102_quota_forecast.py`
- `app/tests_py/integration/test_itpv2_102_backoff_and_retry_taxonomy.py`

### PV2-201
- `app/tests_py/acceptance/test_atpv2_201_multiregion_replication.py`
- `app/tests_py/integration/test_itpv2_201_residency_routing.py`
- `app/tests_py/resilience/test_rtpv2_201_failover_replay.py`

### PV2-202
- `app/tests_py/acceptance/test_atpv2_202_audit_dashboard_anomaly.py`
- `app/tests_py/unit/test_tspv2_202_audit_aggregate_contract.py`
- `app/tests_py/integration/test_itpv2_202_anomaly_escalation_workflow.py`

## Mandatory scenario matrix
1. Adaptive model selection under benchmark drift and missing artifacts.
2. Preset exchange incompatible schema, permission denial, and signature mismatch.
3. Facebook Reels and X publishing: quota exhaustion, policy rejection, retryable failures.
4. Scheduler behavior under mixed-provider quotas and blackout windows.
5. Multi-region failover/replay with local-first continuity.
6. Residency mobility transitions with audit trail and no data loss.
7. Dashboard anomaly detection and ownership escalation accuracy.
8. Accessibility keyboard-only completion for all new critical workflows.

## Evidence contract
Record and link at minimum:
- `out/logs/capstone_baseline/capstone_summary.txt`
- `out/logs/capstone_baseline/security_audit_report.txt`
- `out/logs/capstone_baseline/repo_hygiene_report.txt`
- `out/logs/live_phase_05_report.json`
- `out/logs/live_phase_06_report.json`

## Release blockers
- Any required gate is `fail` or `not-run`.
- Any open critical/high security finding without explicit temporary RC waiver.
- Any unresolved determinism/reliability regression in mandatory scenarios.
- Any unresolved critical accessibility issue in core workflows.

## Completion snapshot (2026-03-01)
- All Post-V2 acceptance commands are implemented and passing:
  - `acceptance_pv2_001.sh`
  - `acceptance_pv2_101.sh`
  - `acceptance_pv2_102.sh`
  - `acceptance_pv2_002.sh`
  - `acceptance_pv2_201.sh`
  - `acceptance_pv2_202.sh`
- Final strict-gate evidence on closeout candidate:
  - strict verify: pass
  - strict capstone: pass
  - `result[live_closeout]=pass`
  - `capstone_finished=2026-03-01T18:15:22Z`
