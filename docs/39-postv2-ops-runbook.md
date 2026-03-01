# Post-V2 Operations Runbook

This runbook defines operational procedures for Post-V2 backlog execution.

## Scope
- Wave 1 (`PV2-001`) model auto-selection operations
- Wave 2 (`PV2-101`) provider expansion operations
- Wave 3 (`PV2-102`) scheduling optimization operations
- Wave 4 (`PV2-002`) preset exchange operations
- Wave 5 (`PV2-201`) multi-region operations
- Wave 6 (`PV2-202`) audit dashboard operations

## Wave 1 Model Selection Operations (`PV2-001`)

### Service surfaces
- `ModelRegistryServiceV2`
- `PhotoAnimator.resolve_auto_model_or_fallback(...)`
- Telemetry tables:
  - `model_eval_runs`
  - `model_hw_benchmarks`
  - `model_selection_events`

### Key health checks
1. Recommendation path returns deterministic result for identical profile + model set.
2. Selection events include both `selected` and `fallback` outcomes when applicable.
3. Drift detector reports no checksum mismatch for active models.
4. Fallback path returns `tier0` with explicit reason code when no compatible model exists.

### Incident classes and response

| Incident code | Trigger | User impact | Immediate response | Recovery criteria |
|---|---|---|---|---|
| `E_MODEL_NOT_INSTALLED` | Active registry entry missing local artifact | Auto-selection fallback to `tier0` | Verify model artifact path, reinstall candidate, rerun recommendation | Drift detector count returns 0 for target model |
| `E_MODEL_CHECKSUM_MISMATCH` | Local model bytes do not match expected checksum | Auto-selection fallback; model blocked from compatibility | Reinstall model from trusted source and verify checksum | `detect_model_artifact_drift(...)` shows no checksum incident |
| `E_MODEL_NO_COMPATIBLE` | No candidate passes compatibility/safety/perf checks | Fallback mode only | Review hardware profile thresholds and benchmark telemetry | Recommendation returns `ok=true` for expected profile |

### Verification commands
- `bash scripts/test/acceptance_pv2_001.sh`
- `env VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh`
- `env VAS_SECURITY_STRICT=1 VAS_YT_TEST_VIDEO_PATH=/Users/d/Projects/visual-album-studio/out/fixtures/live_test_video_large.mp4 ./scripts/test/capstone_audit.sh`

### Rollback procedure
1. Revert to last known-good Post-V2 commit for model selection lane.
2. Re-run strict verify and strict capstone.
3. Keep `PV2-001` issue open until root cause and fix evidence are published.

### Ownership
- Program owner: `saagar210`
- Security review owner: `saagar210`
- Escalation artifact: `out/logs/security/security_ownership_map.md`

## Wave 2 Provider Expansion Operations (`PV2-101`)

### Service surfaces
- `DistributionServiceV2`
- `DistributionAdapter` implementations:
  - `TikTokDistributionAdapter`
  - `InstagramDistributionAdapter`
  - `FacebookReelsDistributionAdapter`
  - `XDistributionAdapter`
- Migration for provider constraints:
  - `migrations/013_postv2_distribution_provider_expansion.sql`

### Key health checks
1. Provider preflight blocks quota and policy violations before publish dispatch.
2. Provider publish results preserve normalized error shape (`error_code`, `retryable`, `http_status`).
3. Diagnostics redaction removes sensitive token markers from connector payloads.
4. `distribution_publish_jobs` records provider events for all configured providers.

### Incident classes and response

| Incident code | Trigger | User impact | Immediate response | Recovery criteria |
|---|---|---|---|---|
| `E_PROVIDER_QUOTA_EXCEEDED` | Estimated units exceed remaining quota | Publish blocked | Adjust budget/schedule; retry after quota window | Preflight returns `ok=true` |
| `E_*_POLICY_BLOCKED` | Provider policy block simulation/live policy rejection | Publish blocked | Correct metadata/content policy settings and retry | Publish returns `succeeded` |
| `E_*_TRANSIENT` | Retryable provider-side transient error | Publish delayed | Backoff and retry according to policy | Retry succeeds or escalates with non-retryable code |

### Verification commands
- `bash scripts/test/acceptance_pv2_101.sh`
- `env VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh`
- `env VAS_SECURITY_STRICT=1 VAS_YT_TEST_VIDEO_PATH=/Users/d/Projects/visual-album-studio/out/fixtures/live_test_video_large.mp4 ./scripts/test/capstone_audit.sh`

## Wave 3 Scheduling Optimization Operations (`PV2-102`)

### Service surfaces
- `DistributionSchedulingServiceV1`
- `distribution_schedule_plans` telemetry table

### Key health checks
1. Quota forecast marks over-budget jobs as deferred.
2. Retryable jobs emit backoff policy with bounded retry windows.
3. Blackout-window policies defer jobs deterministically.
4. Schedule-plan telemetry rows are persisted for all considered jobs.

### Incident classes and response

| Incident code | Trigger | User impact | Immediate response | Recovery criteria |
|---|---|---|---|---|
| `E_PROVIDER_QUOTA_EXCEEDED` | Pending units exceed provider budget | Job deferred | Reduce pending volume or wait for quota refresh | Quota forecast returns `within_budget=true` |
| `E_PROVIDER_BLACKOUT` | Provider blackout-hour window active | Job deferred | Re-schedule outside blackout window | Job appears in scheduled set on next run |
| `E_*_TRANSIENT` | Retryable provider transient failures | Delayed dispatch | Allow bounded exponential backoff retries | Retry policy converges to success or non-retryable state |

### Verification commands
- `bash scripts/test/acceptance_pv2_102.sh`
- `env VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh`
- `env VAS_SECURITY_STRICT=1 VAS_YT_TEST_VIDEO_PATH=/Users/d/Projects/visual-album-studio/out/fixtures/live_test_video_large.mp4 ./scripts/test/capstone_audit.sh`

## Wave 4 Preset Exchange Operations (`PV2-002`)

### Service surfaces
- `PresetExchangeServiceV1`
- `preset_exchange_events` audit table

### Key health checks
1. Bundle compatibility check enforces schema/version and required fields.
2. Signature verification rejects tampered payloads.
3. Permission gating rejects non-authorized actor imports.
4. Exchange events persist imported/failed outcomes with error taxonomy.

### Incident classes and response

| Incident code | Trigger | User impact | Immediate response | Recovery criteria |
|---|---|---|---|---|
| `E_PRESET_SCHEMA_INCOMPATIBLE` | Unsupported bundle schema | Import blocked | Re-export preset on supported schema | Compatibility report returns `ok=true` |
| `E_PRESET_SIGNATURE_INVALID` | Payload tampering/signature mismatch | Import blocked | Re-acquire trusted bundle and verify digest | Signature verification returns `ok=true` |
| `E_PRESET_PERMISSION_DENIED` | Actor lacks share/edit rights | Import blocked | Update sharing allowlist or target-project role | Import succeeds for authorized actor |

### Verification commands
- `bash scripts/test/acceptance_pv2_002.sh`
- `env VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh`
- `env VAS_SECURITY_STRICT=1 VAS_YT_TEST_VIDEO_PATH=/Users/d/Projects/visual-album-studio/out/fixtures/live_test_video_large.mp4 ./scripts/test/capstone_audit.sh`

## Wave 5 Multi-Region Operations (`PV2-201`)

### Service surfaces
- `MultiRegionReplicationServiceV1`
- `project_residency_policies`
- `cloud_replication_checkpoints`

### Key health checks
1. Residency routing prefers active regions and falls back to DR when required.
2. Replication checkpoints preserve deterministic replay order by sequence/region.
3. Pending checkpoints are surfaced during regional unavailability.
4. Local-first continuity remains explicit in replication details.

### Incident classes and response

| Incident code | Trigger | User impact | Immediate response | Recovery criteria |
|---|---|---|---|---|
| `E_REGION_UNAVAILABLE` | No eligible region reachable | Cloud write lane degraded to local-only | Keep local queue active; recover region availability | Route resolution returns `ok=true` |
| `pending checkpoints` | Partial region outage during replication | Delayed cross-region consistency | Replay pending checkpoints after region recovery | Pending count converges to 0 |

### Verification commands
- `bash scripts/test/acceptance_pv2_201.sh`
- `env VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh`
- `env VAS_SECURITY_STRICT=1 VAS_YT_TEST_VIDEO_PATH=/Users/d/Projects/visual-album-studio/out/fixtures/live_test_video_large.mp4 ./scripts/test/capstone_audit.sh`

## Wave 6 Audit Dashboard Operations (`PV2-202`)

### Service surfaces
- `AuditDashboardServiceV1`
- `audit_anomaly_events`
- `audit_ownership_map`

### Key health checks
1. Aggregates report connector-error, replay-failure, and conflict metrics correctly.
2. Threshold breaches emit anomaly signals with deterministic severity mapping.
3. Ownership escalation maps each signal to an explicit owner/channel.
4. Open anomaly events are persisted and queryable for triage workflows.

### Incident classes and response

| Incident code | Trigger | User impact | Immediate response | Recovery criteria |
|---|---|---|---|---|
| `connector_error_spike` | Error diagnostics exceed threshold | Provider reliability risk | Pause risky lane, inspect connector diagnostics | Error count drops below threshold |
| `sync_replay_failures` | Replay failures exceed threshold | Collaboration sync degradation | Replay queue triage, adapter health validation | Replay failure count stabilizes |
| `conflict_spike` | Conflict volume exceeds threshold | Collaboration UX friction | Review conflict-resolution traces and user operations | Conflict rate returns to baseline |

### Verification commands
- `bash scripts/test/acceptance_pv2_202.sh`
- `env VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh`
- `env VAS_SECURITY_STRICT=1 VAS_YT_TEST_VIDEO_PATH=/Users/d/Projects/visual-album-studio/out/fixtures/live_test_video_large.mp4 ./scripts/test/capstone_audit.sh`
