# Post-V2 Backlog

## Source of deferred items
This backlog captures work intentionally deferred beyond V2 GA after delivery of `PV1-001..PV1-008`. Source set:
- `docs/23-post-v1-backlog.md`
- `docs/20-phase-blueprint-v2.md`
- Train 3/4 execution notes and closeout follow-ups

## Execution status
- Wave 0 control-plane kickoff (2026-03-01):
  - governance docs published:
    - `docs/36-postv2-phase-blueprint.md`
    - `docs/37-postv2-requirements-traceability.md`
    - `docs/38-postv2-test-verification.md`
  - acceptance gate stubs published:
    - `scripts/test/acceptance_pv2_001.sh`
    - `scripts/test/acceptance_pv2_002.sh`
    - `scripts/test/acceptance_pv2_101.sh`
    - `scripts/test/acceptance_pv2_102.sh`
    - `scripts/test/acceptance_pv2_201.sh`
    - `scripts/test/acceptance_pv2_202.sh`
  - tracking issue board opened:
    - `#19` (`PV2-001`)
    - `#20` (`PV2-002`)
    - `#21` (`PV2-101`)
    - `#22` (`PV2-102`)
    - `#23` (`PV2-201`)
    - `#24` (`PV2-202`)
- `PV2-001`: complete (wave 1 closure on 2026-03-01)
  - initial slice delivered:
    - hardware profile contract (`HardwareProfileV1`)
    - adaptive model recommendation logic in `ModelRegistryServiceV2`
    - auto-selection fallback path in `PhotoAnimator`
    - tests:
      - `app/tests_py/unit/test_tspv2_001_hardware_profile_selection.py`
      - `app/tests_py/integration/test_itpv2_001_adaptive_model_selection.py`
  - stacked slice delivered:
    - benchmark telemetry persistence (`model_hw_benchmarks`) and selection event history (`model_selection_events`)
    - benchmark-weighted ranking path for hardware-specific model recommendation
    - animator-level selection/fallback event logging through registry hooks
    - migration:
      - `migrations/012_postv2_model_selection_telemetry.sql`
  - stacked slice delivered:
    - installation-aware recommendation filter now excludes models with missing local artifacts (`installed=false`)
    - auto-selection telemetry now records final outcome after model-path resolution (`selected` vs `fallback`)
    - added regression for missing-model drift to ensure fallback + telemetry accuracy:
      - `app/tests_py/integration/test_itpv2_001_adaptive_model_selection.py::test_itpv2_001_missing_model_file_forces_fallback_event`
  - wave 1 closure additions:
    - evaluation-to-benchmark auto-ingestion and profile telemetry normalization in `ModelRegistryServiceV2.record_evaluation(...)`
    - checksum/missing-artifact drift detection via `ModelRegistryServiceV2.detect_model_artifact_drift(...)`
    - deterministic tie-break policy for equal-rank candidates
    - new closure test/evidence suites:
      - `app/tests_py/unit/test_tspv2_001_selection_policy.py`
      - `app/tests_py/integration/test_itpv2_001_eval_ingestion_and_drift_guard.py`
      - `app/tests_py/acceptance/test_atpv2_001_model_autoselection_completion.py`
      - `scripts/test/acceptance_pv2_001.sh`
    - operations runbook section:
      - `docs/39-postv2-ops-runbook.md`
- `PV2-101`: complete (wave 2 closure on 2026-03-01)
  - provider adapters added:
    - `facebook_reels`
    - `x`
  - migration added for expanded provider constraints:
    - `migrations/013_postv2_distribution_provider_expansion.sql`
  - closure test/evidence suites:
    - `app/tests_py/integration/test_itpv2_101_facebook_reels_publish_flow.py`
    - `app/tests_py/integration/test_itpv2_101_x_publish_flow.py`
    - `app/tests_py/integration/test_itpv2_101_provider_policy_redaction.py`
    - `app/tests_py/acceptance/test_atpv2_101_provider_expansion.py`
    - `scripts/test/acceptance_pv2_101.sh`
- `PV2-102`: complete (wave 3 closure on 2026-03-01)
  - scheduling optimization service delivered:
    - `app/src/core_py/vas_studio/distribution_scheduler_v1.py`
  - closure test/evidence suites:
    - `app/tests_py/unit/test_tspv2_102_quota_forecast.py`
    - `app/tests_py/integration/test_itpv2_102_backoff_and_retry_taxonomy.py`
    - `app/tests_py/acceptance/test_atpv2_102_scheduler_optimization.py`
    - `scripts/test/acceptance_pv2_102.sh`
- `PV2-002`: complete (wave 4 closure on 2026-03-01)
  - preset exchange service delivered:
    - `app/src/core_py/vas_studio/preset_exchange_v1.py`
  - closure test/evidence suites:
    - `app/tests_py/unit/test_tspv2_002_preset_bundle_schema.py`
    - `app/tests_py/integration/test_itpv2_002_permission_and_signature_paths.py`
    - `app/tests_py/acceptance/test_atpv2_002_style_exchange.py`
    - `scripts/test/acceptance_pv2_002.sh`
- `PV2-201`: complete (wave 5 closure on 2026-03-01)
  - multi-region replication service delivered:
    - `app/src/core_py/vas_studio/multi_region_v1.py`
    - `migrations/014_postv2_exchange_scheduler_multiregion_audit.sql`
  - closure test/evidence suites:
    - `app/tests_py/integration/test_itpv2_201_residency_routing.py`
    - `app/tests_py/resilience/test_rtpv2_201_failover_replay.py`
    - `app/tests_py/acceptance/test_atpv2_201_multiregion_replication.py`
    - `scripts/test/acceptance_pv2_201.sh`
- `PV2-202`: complete (wave 6 closure on 2026-03-01)
  - audit dashboard and anomaly escalation service delivered:
    - `app/src/core_py/vas_studio/audit_dashboard_v1.py`
  - closure test/evidence suites:
    - `app/tests_py/unit/test_tspv2_202_audit_aggregate_contract.py`
    - `app/tests_py/integration/test_itpv2_202_anomaly_escalation_workflow.py`
    - `app/tests_py/acceptance/test_atpv2_202_audit_dashboard_anomaly.py`
    - `scripts/test/acceptance_pv2_202.sh`

## Rendering and ML enhancements
| Item | Description | Reason deferred | Priority | Suggested phase/quarter | Dependency notes |
|---|---|---|---|---|---|
| PV2-001 | Adaptive model auto-selection by hardware profile | Requires expanded benchmark matrix and wider hardware telemetry | P1 | Post-V2 Q2 | Needs model-eval harness expansion |
| PV2-002 | Cross-project style transfer preset exchange | UX governance and safety policy not finalized in V2 | P2 | Post-V2 Q3 | Depends on collaboration permissions extensions |

## Distribution and platform expansions
| Item | Description | Reason deferred | Priority | Suggested phase/quarter | Dependency notes |
|---|---|---|---|---|---|
| PV2-101 | Additional platform adapters beyond TikTok/Instagram/YouTube | V2 focused on first two provider expansions | P1 | Post-V2 Q2 | Reuse `DistributionAdapter` contract |
| PV2-102 | Provider-specific scheduling optimization engine | Initial quota/policy controls meet V2 scope | P2 | Post-V2 Q3 | Requires production telemetry sample size |

## Collaboration and cloud features
| Item | Description | Reason deferred | Priority | Suggested phase/quarter | Dependency notes |
|---|---|---|---|---|---|
| PV2-201 | Multi-region replication + residency mobility | Explicitly deferred by residency baseline | P1 | Post-V2 Q3 | Requires ADR + migration plan |
| PV2-202 | Team-level audit dashboards and anomaly detection | V2 shipped core conflict/audit records only | P2 | Post-V2 Q4 | Depends on cloud telemetry aggregation |
