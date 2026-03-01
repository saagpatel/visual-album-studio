# V2 Train Execution Board (Single-Owner Program)

## Purpose
Track full V2 execution from current baseline to 100% completion (`AT-V2-000` .. `AT-V2-501`) with explicit milestones, dependencies, and gate evidence.

## Post-V2 Program Extension (Wave 0 Kickoff, 2026-03-01)
The V2 train program is complete; execution now extends to Post-V2 backlog closure using the Wave plan in `docs/36-postv2-phase-blueprint.md`.

Post-V2 wave tracking issues:
- `#19` - `PV2-001` adaptive model auto-selection completion (`completed`)
- `#20` - `PV2-002` style-transfer preset exchange
- `#21` - `PV2-101` provider expansion (Facebook Reels, X)
- `#22` - `PV2-102` scheduling optimization engine
- `#23` - `PV2-201` multi-region replication/residency mobility
- `#24` - `PV2-202` audit dashboards/anomaly detection

Post-V2 control-plane artifacts:
- `docs/36-postv2-phase-blueprint.md`
- `docs/37-postv2-requirements-traceability.md`
- `docs/38-postv2-test-verification.md`
- `scripts/test/acceptance_pv2_001.sh`
- `scripts/test/acceptance_pv2_002.sh`
- `scripts/test/acceptance_pv2_101.sh`
- `scripts/test/acceptance_pv2_102.sh`
- `scripts/test/acceptance_pv2_201.sh`
- `scripts/test/acceptance_pv2_202.sh`
- `docs/39-postv2-ops-runbook.md`

## Program Constants
- Owner: `saagar210`
- Model: `single-owner`
- Target horizon: `12-14 months`
- Completion definition: V2 GA + closeout artifacts on one canonical `V2_CLOSEOUT_SHA`

## Baseline Snapshot (2026-03-01)
- Branch/SHA baseline for kickoff: `main` / `f51a8bb3452aa109d254d929f1f14cd50c0844da`
- Already complete:
  - V1 closeout + release tag `closeout-2026-03-01`
  - V2 Train 0 gate baseline (`AT-V2-000`)
  - V2 Train 1 partial implementation and passing acceptance scaffolding (`AT-V2-101` current suite)
- Program blockers to final completion:
  - Train 2-5 feature/test implementation not yet delivered
  - External provider approvals (TikTok/Instagram)
  - Cloud production readiness and closeout evidence for Train 4/5

## Milestone Board

### M0 - Program Rebaseline (Weeks 1-2)
Status: `completed`
Dependencies: none
Tracking issue: `#7`
Tasks:
- [x] Refresh V2 tracker docs with canonical SHA and active train context
- [x] Complete command catalog for Trains 2-5 in `docs/26-v2-test-verification.md`
- [x] Add gate command wrappers:
  - `scripts/test/acceptance_v2_train2.sh`
  - `scripts/test/acceptance_v2_train3.sh`
  - `scripts/test/acceptance_v2_train4.sh`
  - `scripts/test/acceptance_v2_train5.sh`
- [x] Publish train-by-train GitHub issue board (`AT-V2-*` mapped)
Exit criteria:
- [x] `AT-V2-000` still pass
- [x] No missing train gate command contracts for Trains 2-5

### M1 - Train 1 Full Closure (Months 1-2)
Status: `completed`
Dependencies: M0
Tracking issue: `#8`
Scope: `RQ-V2-101..105`, `PV1-003`, `PV1-005`
Tasks:
- [x] Harden 4K lane release profile and determinism boundary documentation
- [x] Packaging/signing promotion readiness, key rotation runbook, provenance verification contract
- [x] Publish Train 1 evidence pack and rollback playbook
Exit criteria:
- [x] `AT-V2-101` pass with final Train 1 evidence pack
- [x] strict verify + strict capstone pass

### M2 - Train 2 Delivery (Months 3-5)
Status: `completed`
Dependencies: M1
Tracking issue: `#9`
Scope: `RQ-V2-201..205`, `PV1-001`, `PV1-002`
Tasks:
- [x] Implement next-gen mode families with stable parameter contracts
- [x] Implement `ModelRegistryServiceV2` (checksum/license/provenance/rollback)
- [x] Implement deterministic no-model fallback behavior
- [x] Deliver test suites + fixtures for `AT-V2-201`
Progress snapshot (2026-03-01):
- [x] Train 2 migration baseline added (`009_v2_train2_rendering_ml.sql`) with `model_registry` provenance/status fields and evaluation tables.
- [x] Train 2 core scaffolding added (`ModelRegistryServiceV2`, v2 mode presets, mapping namespace contracts, deterministic model fallback path).
- [x] Train 2 required evidence suites added:
  - `app/tests_py/acceptance/test_atv2201_train2.py`
  - `app/tests_py/unit/test_tsv2_201_mode_contracts.py`
  - `app/tests_py/unit/test_tsv2_203_model_eval_harness.py`
  - `app/tests_py/integration/test_itv2_202_model_registry_provenance.py`
  - `app/tests_py/integration/test_itv2_203_model_fallback_behavior.py`
  - `app/tests_py/integration/test_itv2_204_model_eval_harness.py`
- [x] Verification snapshot on branch `codex/v2-m2-mode-model-slice-20260301`:
  - `bash scripts/test/acceptance_v2_train2.sh` => pass
  - `env VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh` => pass
  - `env VAS_SECURITY_STRICT=1 VAS_YT_TEST_VIDEO_PATH=/Users/d/Projects/visual-album-studio/out/fixtures/live_test_video_large.mp4 ./scripts/test/capstone_audit.sh` => pass
  - `result[live_closeout]=pass` (`capstone_finished=2026-03-01T14:51:40Z`)
Exit criteria:
- [x] `AT-V2-201` pass
- [x] strict verify + strict capstone pass

### M3 - Train 3 Delivery (Months 6-8)
Status: `completed`
Dependencies: M2 + provider approvals
Tracking issue: `#10`
Scope: `RQ-V2-301..305`, `PV1-004`, `PV1-006`
Tasks:
- [x] Implement `DistributionAdapter` contracts
- [x] Deliver TikTok first, Instagram second
- [x] Implement provider quota/policy preflight and failure taxonomy
- [x] Expand analytics/revenue connectors with privacy-safe fallback
- [x] Deliver required Train 3 tests/evidence suites:
  - `app/tests_py/acceptance/test_atv2301_train3.py`
  - `app/tests_py/unit/test_tsv2_301_distribution_contracts.py`
  - `app/tests_py/unit/test_tsv2_302_provider_policy_controls.py`
  - `app/tests_py/integration/test_itv2_301_distribution_adapter_contract.py`
  - `app/tests_py/integration/test_itv2_302_tiktok_publish_flow.py`
  - `app/tests_py/integration/test_itv2_303_instagram_publish_flow.py`
  - `app/tests_py/integration/test_itv2_304_provider_quota_policy.py`
  - `app/tests_py/integration/test_itv2_305_connector_privacy_redaction.py`
Progress snapshot (2026-03-01):
- [x] Train 3 migration + service baseline added:
  - `migrations/010_v2_train3_distribution.sql`
  - `app/src/core_py/vas_studio/distribution_v2.py`
- [x] Train 3 gate verification:
  - `bash scripts/test/acceptance_v2_train3.sh` => pass
  - `env VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh` => pass
  - `env VAS_SECURITY_STRICT=1 VAS_YT_TEST_VIDEO_PATH=/Users/d/Projects/visual-album-studio/out/fixtures/live_test_video_large.mp4 ./scripts/test/capstone_audit.sh` => pass
- [x] `result[live_closeout]=pass` on latest rerun (`capstone_finished=2026-03-01T15:54:52Z`)
- [x] Tracking issue `#10` closed after merge/evidence publication
Exit criteria:
- [x] `AT-V2-301` pass
- [x] strict verify + strict capstone pass

### M4 - Train 4 Delivery (Months 9-11)
Status: `completed`
Dependencies: M3 + Supabase production readiness
Tracking issue: `#11`
Scope: `RQ-V2-401..405`, `PV1-007`, `PV1-008`
Tasks:
- [x] Implement `CloudSyncAdapter`, `ObjectStorageAdapter`, `CollaborationService`
- [x] Deliver RBAC and deterministic conflict resolution
- [x] Deliver offline edit + reconnect replay + outage fallback
- [x] Threat model signoff + residency revalidation
- [x] Deliver required Train 4 tests/evidence suites:
  - `app/tests_py/acceptance/test_atv2401_train4.py`
  - `app/tests_py/unit/test_tsv2_401_collaboration_rbac.py`
  - `app/tests_py/unit/test_tsv2_402_conflict_resolution.py`
  - `app/tests_py/unit/test_tsv2_403_storage_reference_versioning.py`
  - `app/tests_py/integration/test_itv2_401_cloud_sync_offline_replay.py`
  - `app/tests_py/integration/test_itv2_402_collaboration_rbac.py`
  - `app/tests_py/integration/test_itv2_403_conflict_resolution_determinism.py`
  - `app/tests_py/integration/test_itv2_404_storage_reference_versioning.py`
  - `app/tests_py/integration/test_itv2_405_cloud_outage_failsafe.py`
  - `app/tests_py/resilience/test_rtv2_401_conflict_chaos.py`
  - `app/tests_py/resilience/test_rtv2_402_cloud_outage_local_continuity.py`
Progress snapshot (2026-03-01):
- [x] Train 4 migration + service baseline added:
  - `migrations/011_v2_train4_cloud_collaboration.sql`
  - `app/src/core_py/vas_studio/cloud_collab_v2.py`
- [x] Threat/residency artifacts updated:
  - `docs/35-v2-train4-threat-model.md`
  - `docs/28-v2-cloud-region-and-residency.md` revalidation note
- [x] Train 4 gate verification:
  - `bash scripts/test/acceptance_v2_train4.sh` => pass
  - `env VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh` => pass
  - `env VAS_SECURITY_STRICT=1 VAS_YT_TEST_VIDEO_PATH=/Users/d/Projects/visual-album-studio/out/fixtures/live_test_video_large.mp4 ./scripts/test/capstone_audit.sh` => pass
- [x] Tracking issue `#11` closed after merge/evidence publication
Exit criteria:
- [x] `AT-V2-401` pass
- [x] strict verify + strict capstone pass

### M5 - Train 5 Final Hardening + V2 GA (Months 12-14)
Status: `completed`
Dependencies: M1-M4
Tracking issue: `#12`
Scope: `RQ-V2-501..505`
Tasks:
- [x] Candidate SHA freeze and full-suite rehearsal
- [x] Security/provenance/a11y all-green verification on one SHA
- [x] Publish V2 closeout report + post-v2 backlog + release tag
- [x] Final branch/issue cleanup + STATUS declaration
- [x] Deliver required Train 5 tests/evidence suites:
  - `app/tests_py/acceptance/test_atv2501_train5.py`
  - `app/tests_py/unit/test_tsv2_510_accessibility_tokens.py`
  - `app/tests_py/integration/test_itv2_510_accessibility_gates.py`
  - `app/tests_py/integration/test_itv2_511_provenance_closeout_bundle.py`
  - `docs/33-v2-closeout-report.md`
  - `docs/34-post-v2-backlog.md`
Progress snapshot (2026-03-01):
- [x] Full acceptance stack pass:
  - `bash scripts/test/acceptance_v2_train1.sh`
  - `bash scripts/test/acceptance_v2_train2.sh`
  - `bash scripts/test/acceptance_v2_train3.sh`
  - `bash scripts/test/acceptance_v2_train4.sh`
  - `bash scripts/test/acceptance_v2_train5.sh`
- [x] strict verify + strict capstone pass with `result[live_closeout]=pass`
- [x] `docs/security-waivers.json` remains empty (`waivers=[]`)
- [x] Tracking issue `#12` closed after merge/evidence publication
Exit criteria:
- [x] `AT-V2-501` pass
- [x] strict verify + strict capstone pass on same `V2_CLOSEOUT_SHA` candidate window
- [x] no active waivers in `docs/security-waivers.json`

## Dependency and Risk Notes
- External blocking dependencies:
  - TikTok/Instagram API approval and audit status
  - Supabase production environment and secret management readiness
  - Signing key/attestation key rotation ops readiness
- Single-owner risk:
  - bus-factor remains 1 and is accepted with weekly ownership-map cadence.

## Evidence Pointers
- `out/logs/capstone_baseline/capstone_summary.txt`
- `out/logs/capstone_baseline/security_audit_report.txt`
- `out/logs/capstone_baseline/repo_hygiene_report.txt`
- `out/logs/security/security_ownership_map.md`
- `out/logs/security/security_ownership_map.json`
