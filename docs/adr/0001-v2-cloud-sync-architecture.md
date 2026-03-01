# 0001. V2 Cloud Sync Architecture (Supabase + Local-First)

## Status
Accepted

## Context
V2 requires collaboration and cloud storage/render capabilities while preserving local-first reliability and offline workflows.

## Decision
Use Supabase as the V2 cloud baseline:
- Auth for identity and RBAC primitives
- Postgres for metadata/state
- Storage for artifact/object references
- Realtime channels for collaboration signal updates

Adopt a local-first sync model:
- Local project state remains usable offline.
- Sync uses versioned envelopes and replay-safe journals.
- Cloud failure degrades to local-only mode with deferred sync.

## Consequences
Benefits:
- Faster path to cloud GA with managed primitives.
- Reduced control-plane implementation overhead.
- Strong SQL portability for long-term data strategy.

Tradeoffs:
- Managed-service dependency for cloud lane.
- Requires strict sync conflict and retry semantics.
- Requires ops controls for residency, backup, and key rotation.

## Alternatives Considered
- AWS managed stack: powerful but higher setup and operations complexity.
- GCP managed stack: strong ecosystem fit but higher lock-in and migration complexity.
- Fully self-hosted stack: maximum control but slower and riskier for V2 timeline.
