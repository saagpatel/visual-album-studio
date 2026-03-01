# Post-v1 Backlog (Deferred Scope Register)

## Purpose
This backlog captures all explicitly deferred/out-of-scope items from the phase specifications so current project scope can be declared complete without ambiguity.

## Source of Deferred Items
- `docs/phases/phase-01.md` -> Explicit out-of-scope (deferred)
- `docs/phases/phase-02.md` -> Explicit out-of-scope (deferred)
- `docs/phases/phase-03.md` -> Explicit out-of-scope (deferred)
- `docs/phases/phase-04.md` -> Explicit out-of-scope (deferred)
- `docs/phases/phase-05.md` -> Explicit out-of-scope (deferred)
- `docs/phases/phase-06.md` -> Explicit out-of-scope
- `docs/phases/phase-07.md` -> Explicit out-of-scope

## Backlog Themes

### Rendering / ML Enhancements

| ID | Item | Reason Deferred | Priority | Suggested Phase/Quarter | Dependencies / Notes |
|---|---|---|---|---|---|
| PV1-001 | Next-generation rendering modes beyond current phase-7 scope | Explicitly out-of-scope in Phase 7 closeout to prevent scope expansion during completion | P2 | Post-v1 / Q2 planning | Requires reliability budget review so new render features do not regress AT-001 determinism and resume guarantees |
| PV1-002 | ML-heavy visual pipelines beyond optional Phase 2 photo animator tier | Explicitly out-of-scope in Phase 7; deferred to protect licensing/provenance and runtime stability controls | P2 | Post-v1 / Q2-Q3 | Requires updated model provenance policy, distribution review, and additional AT coverage |
| PV1-003 | 4K export profile hardening as default production lane | Locked assumption in pinned decisions defers 4K until stability is proven | P1 | Post-v1 / Q2 | Depends on export throughput profiling, determinism rerun scaling, and disk-usage envelope updates |

### Distribution / Platform Expansions

| ID | Item | Reason Deferred | Priority | Suggested Phase/Quarter | Dependencies / Notes |
|---|---|---|---|---|---|
| PV1-004 | Additional external distribution platforms beyond YouTube | Explicitly out-of-scope in Phase 7 to avoid diluting publish reliability/security work | P2 | Post-v1 / Q3 | Requires per-platform auth, quota/policy compliance modeling, and adapter contract extensions |
| PV1-005 | Production packaging/signing/release-channel expansion beyond dry-run architecture | Phase 7 intentionally delivered packaging readiness architecture and deterministic dry-run only | P1 | Post-v1 / Q2 | Requires signing/updates threat model, rollback playbook integration, and release governance checkpoints |
| PV1-006 | Broader analytics/revenue connector set beyond official current APIs | Deferred to preserve policy-safe, official-API-only boundary in v1 | P3 | Post-v1 / Q3-Q4 | Requires policy review, quota modeling, and updated privacy/redaction validation |

### Collaboration / Cloud Features

| ID | Item | Reason Deferred | Priority | Suggested Phase/Quarter | Dependencies / Notes |
|---|---|---|---|---|---|
| PV1-007 | Multi-user collaboration workflows | Explicitly out-of-scope in Phase 7 and non-goal for current local-first v1 architecture | P3 | Post-v1 / Q4 exploration | Requires architecture decision update (sync/conflict resolution/offline merge), security model expansion, and new module contracts |
| PV1-008 | Cloud project storage and cloud rendering workflows | Non-goal in PRD for current project scope | P3 | Post-v1 / Q4+ | Requires cost model, privacy controls, and deterministic pipeline parity strategy across environments |

## Operational Notes
- Deferred items are tracked as backlog candidates, not in-scope deliverables for current completion criteria.
- Any promoted item must be re-scoped through `docs/01-pinned-decisions.md`, `docs/20-phase-blueprint.md`, and traceability updates before implementation.
