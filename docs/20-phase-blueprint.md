# Phase Blueprint (Master Plan)

This document is the master plan for phases, deliverables, and stop/go gates. Each phase has a dedicated detailed spec in `docs/phases/phase-XX.md`.

## Phase order (authoritative)
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6

## Post-v1 extension phases (non-authoritative drafts)
- The authoritative gated chain ends at Phase 6 unless `docs/01-pinned-decisions.md` is explicitly amended.
- Draft extension specs can be prepared for planning and estimation.
- Current draft extension:
  - **Phase 7 (draft):** UX excellence, productization, and post-v1 velocity
  - Spec: `docs/phases/phase-07.md`

## Stop/Go gates (hard)

### Global gate rule
- **Stop:** if a phase gate acceptance test (AT-00X) cannot be made to pass without violating pinned decisions (docs/01-pinned-decisions.md).
- **Go:** only when AT-00X passes and regression suite from prior phases still passes.

### Phase 1 (GO/NO-GO)
Stop if:
- determinism checkpoint hashes cannot be stabilized
- segment-based resume cannot be made reliable

Go when:
- AT-001 passes (including 10s/10min/2h bundles, cancel/resume, determinism checkpoints)

## Definition of Done (per phase)
A phase is done only when:
- All deliverables listed in the phase doc exist and are testable.
- Phase acceptance test AT-00X passes.
- No regressions in earlier phase acceptance tests.
- docs/STATUS.md is updated.

## Phase summaries

### Phase 1 — Local-only end-to-end production bundle
- Objective: ship a local-only workflow that produces production bundles reliably.
- Modules: A, C, G, H, I, J, K
- Gate: AT-001
- Spec: `docs/phases/phase-01.md`

### Phase 2 — Visual modes expansion + mapping/preset hardening
- Objective: expand visual modes (particles/landscape/photo) while preserving determinism and parity.
- Modules: D, E, F, H (v2), J/K governance improvements
- Gate: AT-002
- Spec: `docs/phases/phase-02.md`

### Phase 3 — Mixer + deterministic offline bounce
- Objective: ship multi-track mixer and deterministic loop-safe bounce.
- Modules: B + A enhancements + I audio integration + J license extensions
- Gate: AT-003
- Spec: `docs/phases/phase-03.md`

### Phase 4 — Automation: batch + remix + guardrails
- Objective: batch generation and remixing with anti-spam guardrails and reliability.
- Modules: N, R, K v2, I queue upgrades
- Gate: AT-004
- Spec: `docs/phases/phase-04.md`

### Phase 5 — Optional YouTube publishing + multi-channel
- Objective: publish bundles to YouTube reliably and safely; respect quota/audit constraints.
- Modules: L, M, K publish profiles, I network jobs
- Gate: AT-005
- Spec: `docs/phases/phase-05.md`

### Phase 6 — Analytics + niche + revenue
- Objective: local dashboards, quota-aware sync, revenue tracking, and niche notebook.
- Modules: O, P, Q, J extensions
- Gate: AT-006
- Spec: `docs/phases/phase-06.md`

## Cross-phase invariants (must never regress)
- Export pipeline remains segment-based and crash-safe.
- No plaintext tokens or secrets stored in DB or logs.
- Bundle schemas remain backward compatible via schema_version fields.
- Parameter IDs remain stable; migrations create new versions rather than mutating old ones.
