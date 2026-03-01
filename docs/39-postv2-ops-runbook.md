# Post-V2 Operations Runbook

This runbook defines operational procedures for Post-V2 backlog execution.

## Scope
- Wave 1 (`PV2-001`) model auto-selection operations
- Wave 2 (`PV2-101`) provider expansion operations
- Future sections for Waves 3-6 are appended as each wave closes

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
