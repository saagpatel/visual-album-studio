# 0002. V2 Conflict Resolution Model (Deterministic + Auditable)

## Status
Accepted

## Context
Cloud collaboration introduces concurrent edits and reconciliation complexity. V2 requires deterministic behavior, user clarity, and auditability.

## Decision
Use a deterministic hybrid model:
- Metadata scalar fields: last-write-wins with audit trail.
- Structured graph entities: operation log merge with stable ordering rules.
- Asset/provenance collisions: explicit user decision required.
- Preset/mapping schema collisions: schema-aware merge suggestions with compatibility warnings.

Every conflict event is persisted as a structured record with:
- conflict type
- entities impacted
- deterministic strategy applied
- user decisions and timestamps (when manual)

## Consequences
Benefits:
- Predictable outcomes and reproducible merges.
- Clear forensic trail for debugging and support.
- Maintains local-first continuity without silent data loss.

Tradeoffs:
- Additional implementation complexity in merge engine.
- More UX work for conflict explanation and remediation.
- Requires strong test coverage for edge-case interleavings.

## Alternatives Considered
- Pure last-write-wins: simple but unsafe for complex project graph edits.
- Manual-only merge: safe but too slow and high-friction for common edits.
- CRDT-everywhere: powerful but disproportionate complexity for V2 scope.
