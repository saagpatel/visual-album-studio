# Post-V2 Requirements Traceability Matrix

This matrix maps Post-V2 backlog scope to implementation surfaces, waves, and test IDs.

Legend:
- Test IDs:
  - `TS-PV2-*` unit
  - `IT-PV2-*` integration
  - `AT-PV2-*` acceptance
  - `RT-PV2-*` resilience
- Status: `not-started`, `in-progress`, `pass`, `fail`

## Requirement catalog

| RQ ID | Backlog Item | Requirement statement | Wave | Primary modules/interfaces | Planned tests | Status |
|---|---|---|---|---|---|---|
| RQ-PV2-001 | PV2-001 | Adaptive model auto-selection must use hardware profile + telemetry with deterministic fallback and incident traceability. | Wave 1 | `ModelRegistryServiceV2`, `PhotoAnimator` | TS-PV2-001, IT-PV2-001, AT-PV2-001 | pass |
| RQ-PV2-002 | PV2-002 | Cross-project style transfer preset exchange must enforce schema compatibility, permissions, and provenance validation. | Wave 4 | `PresetExchangeServiceV1` (new), collaboration permissions surface | TS-PV2-002, IT-PV2-002, AT-PV2-002 | not-started |
| RQ-PV2-101 | PV2-101 | Distribution adapter layer must support additional provider lanes (Facebook Reels, X) with quota/policy preflight and normalized errors. | Wave 2 | `DistributionAdapter`, `DistributionServiceV2` | IT-PV2-101-A/B, AT-PV2-101 | not-started |
| RQ-PV2-102 | PV2-102 | Scheduler must optimize dispatch across providers using quota/policy constraints and resilient retry/backoff behavior. | Wave 3 | `DistributionSchedulingServiceV1` (new) | TS-PV2-102, IT-PV2-102, AT-PV2-102 | not-started |
| RQ-PV2-201 | PV2-201 | Cloud sync/storage must support US active-active + EU DR replication and residency-aware mobility without breaking local-first continuity. | Wave 5 | `CloudSyncAdapter`, `ObjectStorageAdapter`, `CollaborationService` | IT-PV2-201, RT-PV2-201, AT-PV2-201 | not-started |
| RQ-PV2-202 | PV2-202 | Team audit dashboard must provide anomaly detection, ownership escalation, and accessible investigation workflows. | Wave 6 | audit aggregation and dashboard surfaces (new) | TS-PV2-202, IT-PV2-202, AT-PV2-202 | not-started |

## Non-functional requirements (cross-cutting)

| NFR ID | Requirement | Applies to | Test/Evidence |
|---|---|---|---|
| NFR-PV2-SEC-001 | No plaintext secret/token leakage in logs/diagnostics. | All waves | `./scripts/test/security_audit.sh` + redaction integration tests |
| NFR-PV2-A11Y-001 | Critical workflows meet keyboard/focus-visible accessibility baseline. | Waves 4, 6 | Accessibility integration tests + acceptance evidence |
| NFR-PV2-PROV-001 | Provenance and auditability maintained for artifacts and model/preset exchange. | Waves 1, 4, 6 | provenance tests + closeout evidence |
| NFR-PV2-REL-001 | Local-first continuity preserved during provider/cloud outages. | Waves 2, 3, 5 | resilience tests + capstone reruns |
| NFR-PV2-COMP-001 | Backward compatibility preserved for existing v1/v2 formats and interfaces. | All waves | migration + compatibility integration tests |

## Planned Post-V2 test IDs
- Wave 1 (`PV2-001`): `TS-PV2-001`, `IT-PV2-001`, `AT-PV2-001`
- Wave 2 (`PV2-101`): `IT-PV2-101-A` (Facebook Reels), `IT-PV2-101-B` (X), `AT-PV2-101`
- Wave 3 (`PV2-102`): `TS-PV2-102`, `IT-PV2-102`, `AT-PV2-102`
- Wave 4 (`PV2-002`): `TS-PV2-002`, `IT-PV2-002`, `AT-PV2-002`
- Wave 5 (`PV2-201`): `IT-PV2-201`, `RT-PV2-201`, `AT-PV2-201`
- Wave 6 (`PV2-202`): `TS-PV2-202`, `IT-PV2-202`, `AT-PV2-202`

## Compatibility and migration rules
1. Existing v1/v2 public payloads remain readable.
2. New schemas/types are additive-first where possible.
3. Any breaking interface change requires explicit migration notes and versioned contract updates before merge.
4. Migrations are forward-only and must have rollback/repair guidance in operations runbook.
