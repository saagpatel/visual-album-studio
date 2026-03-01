# V2 Train Execution Board (Single-Owner Program)

## Purpose
Track full V2 execution from current baseline to 100% completion (`AT-V2-000` .. `AT-V2-501`) with explicit milestones, dependencies, and gate evidence.

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
Status: `in_progress`
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
Status: `pending`
Dependencies: M0
Tracking issue: `#8`
Scope: `RQ-V2-101..105`, `PV1-003`, `PV1-005`
Tasks:
- [ ] Harden 4K lane release profile and determinism boundary documentation
- [ ] Packaging/signing promotion readiness, key rotation runbook, provenance verification contract
- [ ] Publish Train 1 evidence pack and rollback playbook
Exit criteria:
- [ ] `AT-V2-101` pass with final Train 1 evidence pack
- [ ] strict verify + strict capstone pass

### M2 - Train 2 Delivery (Months 3-5)
Status: `pending`
Dependencies: M1
Tracking issue: `#9`
Scope: `RQ-V2-201..205`, `PV1-001`, `PV1-002`
Tasks:
- [ ] Implement next-gen mode families with stable parameter contracts
- [ ] Implement `ModelRegistryServiceV2` (checksum/license/provenance/rollback)
- [ ] Implement deterministic no-model fallback behavior
- [ ] Deliver test suites + fixtures for `AT-V2-201`
Exit criteria:
- [ ] `AT-V2-201` pass
- [ ] strict verify + strict capstone pass

### M3 - Train 3 Delivery (Months 6-8)
Status: `pending`
Dependencies: M2 + provider approvals
Tracking issue: `#10`
Scope: `RQ-V2-301..305`, `PV1-004`, `PV1-006`
Tasks:
- [ ] Implement `DistributionAdapter` contracts
- [ ] Deliver TikTok first, Instagram second
- [ ] Implement provider quota/policy preflight and failure taxonomy
- [ ] Expand analytics/revenue connectors with privacy-safe fallback
Exit criteria:
- [ ] `AT-V2-301` pass
- [ ] strict verify + strict capstone pass

### M4 - Train 4 Delivery (Months 9-11)
Status: `pending`
Dependencies: M3 + Supabase production readiness
Tracking issue: `#11`
Scope: `RQ-V2-401..405`, `PV1-007`, `PV1-008`
Tasks:
- [ ] Implement `CloudSyncAdapter`, `ObjectStorageAdapter`, `CollaborationService`
- [ ] Deliver RBAC and deterministic conflict resolution
- [ ] Deliver offline edit + reconnect replay + outage fallback
- [ ] Threat model signoff + residency revalidation
Exit criteria:
- [ ] `AT-V2-401` pass
- [ ] strict verify + strict capstone pass

### M5 - Train 5 Final Hardening + V2 GA (Months 12-14)
Status: `pending`
Dependencies: M1-M4
Tracking issue: `#12`
Scope: `RQ-V2-501..505`
Tasks:
- [ ] Candidate SHA freeze and full-suite rehearsal
- [ ] Security/provenance/a11y all-green verification on one SHA
- [ ] Publish V2 closeout report + post-v2 backlog + release tag
- [ ] Final branch/issue cleanup + STATUS declaration
Exit criteria:
- [ ] `AT-V2-501` pass
- [ ] strict verify + strict capstone pass on same `V2_CLOSEOUT_SHA`
- [ ] no active waivers in `docs/security-waivers.json`

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
