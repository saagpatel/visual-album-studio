# Post-V2 Next Backlog Seed

This document captures optional next-cycle ideas after completion of Post-V2 backlog scope.

## Reliability and Operations
1. Add automated DR rehearsal runner for quarterly multi-region failover drills.
2. Add anomaly-event auto-triage enrichment (historical trend context and recommended remediations).
3. Add provider policy diff watcher with automated changelog ingestion.

## UX and Workflow
1. Add guided UI for preset exchange trust/verification metadata.
2. Add scheduler simulation dashboard with side-by-side provider timeline previews.
3. Add collaboration timeline visualizer for conflict/replay events.

## Platform and Integrations
1. Add provider expansion candidates behind feature flags (future channels only after policy readiness).
2. Add regional residency policy templates by compliance profile.
3. Add export of audit dashboards as shareable support bundles.

## Prioritization Guidance
- Priority `P1`: DR rehearsal automation, provider-policy diff watcher, scheduler simulation dashboard.
- Priority `P2`: anomaly-event enrichment, preset trust UX, residency policy templates.
- Priority `P3`: collaboration timeline visualizer, additional provider explorations, dashboard export polish.

## Execution Kickoff (2026-03-01)
- Next-cycle control-plane docs published:
  - `docs/42-next-cycle-blueprint.md`
  - `docs/43-next-cycle-requirements-traceability.md`
  - `docs/44-next-cycle-test-verification.md`
- Next-cycle acceptance command stubs published:
  - `scripts/test/acceptance_nc_001.sh`
  - `scripts/test/acceptance_nc_002.sh`
  - `scripts/test/acceptance_nc_003.sh`
  - `scripts/test/acceptance_nc_101.sh`
  - `scripts/test/acceptance_nc_102.sh`
  - `scripts/test/acceptance_nc_103.sh`
  - `scripts/test/acceptance_nc_201.sh`
  - `scripts/test/acceptance_nc_202.sh`
  - `scripts/test/acceptance_nc_203.sh`
- Next-cycle issue board opened:
  - `#29` (`NC-001`)
  - `#30` (`NC-002`)
  - `#31` (`NC-003`)
  - `#32` (`NC-101`)
  - `#33` (`NC-102`)
  - `#34` (`NC-103`)
  - `#35` (`NC-201`)
  - `#36` (`NC-202`)
  - `#37` (`NC-203`)
- First P1 slice delivered:
  - `NC-003` provider policy diff watcher (`ProviderPolicyWatcherV1`)
  - migration: `migrations/015_nextcycle_provider_policy_watch.sql`
  - tests:
    - `app/tests_py/unit/test_tsnc_003_provider_policy_diff.py`
    - `app/tests_py/integration/test_itnc_003_provider_policy_changelog.py`
    - `app/tests_py/acceptance/test_atnc_003_provider_policy_diff_watcher.py`

## Next-Cycle Closure Snapshot (2026-03-01)
- Remaining next-cycle backlog items completed in this execution wave:
  - `NC-001`, `NC-002`, `NC-101`, `NC-102`, `NC-103`, `NC-201`, `NC-202`, `NC-203`
- Delivered implementation surfaces:
  - `DRRehearsalRunnerV1`
  - `AnomalyTriageServiceV1`
  - `PresetTrustUiServiceV1`
  - `SchedulerSimulationDashboardV1`
  - `CollaborationTimelineServiceV1`
  - `ProviderFeatureFlagsV1` with `DistributionServiceV2` enforcement
  - `ResidencyPolicyTemplateServiceV1`
  - `AuditDashboardExportServiceV1`
- Gate evidence:
  - `bash scripts/test/acceptance_nc_001.sh` => pass
  - `bash scripts/test/acceptance_nc_002.sh` => pass
  - `bash scripts/test/acceptance_nc_003.sh` => pass
  - `bash scripts/test/acceptance_nc_101.sh` => pass
  - `bash scripts/test/acceptance_nc_102.sh` => pass
  - `bash scripts/test/acceptance_nc_103.sh` => pass
  - `bash scripts/test/acceptance_nc_201.sh` => pass
  - `bash scripts/test/acceptance_nc_202.sh` => pass
  - `bash scripts/test/acceptance_nc_203.sh` => pass
  - `env VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh` => pass
  - `env VAS_SECURITY_STRICT=1 VAS_YT_TEST_VIDEO_PATH=/Users/d/Projects/visual-album-studio/out/fixtures/live_test_video_large.mp4 ./scripts/test/capstone_audit.sh` => pass
  - `result[live_closeout]=pass`
  - `capstone_finished=2026-03-01T18:56:40Z`
