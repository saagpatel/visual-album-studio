# Requirements V2 (RQ-V2-###)

This document defines V2 requirements for full post-v1 scope.

Stability rules:
- IDs are stable and append-only.
- Every requirement must map to traceability and tests.
- Every requirement must preserve v1 safety constraints unless explicitly superseded via ADR.

## Priorities
- Must: required for V2 completion
- Should: expected for target release trains
- Could: optional for post-v2 or scoped experiments

## Train 0 — Governance and Foundations

### RQ-V2-001 — V2 spec pack must be canonical and complete
Priority: Must
- V2 must define blueprint, requirements, traceability, and acceptance contracts before Train 1 feature work.

### RQ-V2-002 — Governance gates must be enforceable in CI
Priority: Must
- PR checks must include code scanning, dependency review, and policy checks for V2 artifact presence.

### RQ-V2-003 — ADR-backed architecture decisions for cloud sync and conflict handling
Priority: Must
- Cloud sync architecture and conflict-resolution model must be documented as accepted ADRs.

### RQ-V2-004 — UI quality baseline must be codified for V2
Priority: Must
- Accessibility, visual state coverage, and UX quality gates must be documented and testable.

### RQ-V2-005 — Provenance and release integrity controls must be defined
Priority: Must
- Release flow must define signed artifacts, provenance attestations, and verification steps.

### RQ-V2-006 — Cloud region and residency baseline must be explicit
Priority: Must
- V2 cloud baseline must declare initial Supabase region and residency constraints before Train 4 implementation.

## Train 1 — 4K and Packaging

### RQ-V2-101 — 4K export lane must be deterministic within defined boundary
Priority: Must
- 4K deterministic fixtures and reruns must pass within documented tolerance boundary.

### RQ-V2-102 — 4K long-run reliability must match v1 operational quality
Priority: Must
- 4K 2h export interruption/resume must pass with no corruption.

### RQ-V2-103 — Packaging pipeline must produce signed release artifacts
Priority: Must
- Artifacts must be signed and verifiable before channel promotion.

### RQ-V2-104 — Release channels must support canary/beta/stable progression
Priority: Must
- Promotion path must enforce gate pass and provenance verification.

### RQ-V2-105 — Release manifest v2 must include provenance metadata
Priority: Must
- Manifest must include build context, signature metadata, and schema version.

## Train 2 — Rendering and ML

### RQ-V2-201 — Next-generation rendering modes must integrate with existing mapping/presets
Priority: Must
- New visual modes must use stable parameter IDs and mapping contracts.

### RQ-V2-202 — New modes must preserve preview/export parity semantics
Priority: Must
- Same time-value input must produce parity-acceptable output across preview and offline render.

### RQ-V2-203 — ML model registry must enforce checksum/provenance policy
Priority: Must
- Downloaded models require checksums, source metadata, and license records.

### RQ-V2-204 — ML features must degrade safely when models unavailable
Priority: Must
- User-facing flows remain functional with clear fallback behavior.

### RQ-V2-205 — Model evaluation harness must score quality/perf/safety
Priority: Should
- Candidate models are compared using repeatable fixture-driven metrics.

## Train 3 — Distribution and Analytics Connectors

### RQ-V2-301 — Multi-provider distribution adapter must be provider-agnostic
Priority: Must
- Publish requests must route through normalized provider contracts.

### RQ-V2-302 — TikTok publishing lane must be production-ready
Priority: Must
- Upload, metadata, scheduling, and failure taxonomy support is required.

### RQ-V2-303 — Instagram publishing lane must be production-ready
Priority: Must
- Upload, metadata, scheduling, and failure taxonomy support is required.

### RQ-V2-304 — Quota/policy-aware scheduling must be provider-specific
Priority: Must
- Provider lane must enforce policy and quota controls before dispatch.

### RQ-V2-305 — Connector expansion must preserve privacy and redaction guarantees
Priority: Must
- Sensitive data must not leak in logs, diagnostics, or storage.

## Train 4 — Collaboration and Cloud

### RQ-V2-401 — Cloud sync must preserve local-first behavior
Priority: Must
- Local workflows must remain available offline and recover on reconnect.

### RQ-V2-402 — Collaboration GA must support role-based access controls
Priority: Must
- RBAC must enforce project/team permissions for collaboration actions.

### RQ-V2-403 — Conflict resolution must be deterministic and auditable
Priority: Must
- Conflict events must produce reproducible outcomes and audit records.

### RQ-V2-404 — Cloud storage references must remain schema-versioned and recoverable
Priority: Must
- Object references and sync envelopes must be versioned and migration-safe.

### RQ-V2-405 — Cloud outage handling must fail safe
Priority: Must
- App degrades to local-only mode with no data loss.

## Train 5 — Hardening and Closeout

### RQ-V2-501 — All V2 acceptance gates must pass on one canonical SHA
Priority: Must
- No train-specific pass is sufficient without full-candidate full-suite pass.

### RQ-V2-502 — Carry-forward v1 strict gates must pass on same canonical SHA
Priority: Must
- v1 reliability/security guarantees remain unchanged.

### RQ-V2-503 — Accessibility gates must pass across critical V2 workflows
Priority: Must
- Keyboard and focus behavior must be validated for top workflows.

### RQ-V2-504 — Supply-chain and provenance checks must be green
Priority: Must
- Release artifacts must be attested/signed and verification must pass.

### RQ-V2-505 — V2 closeout report must include evidence index and residual risks
Priority: Must
- Final declaration requires evidence references and risk ownership.

## Non-negotiable defaults
- Local-first remains the default operating model.
- Supabase + Postgres is the V2 cloud baseline.
- No permanent waivers are allowed for final V2 GA declaration.
