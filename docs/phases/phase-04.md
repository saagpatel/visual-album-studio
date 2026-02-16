# Phase 4 — Automation: Batch + Remix + Guardrails

## Objectives
- Enable production automation (overnight batches) while **actively preventing** monetization-risk “mass-produced” output.
- Introduce controlled remixing via declarative rules and enforce variant distance guardrails.

## Included modules / features
- **N** Batch generator
- **R** Remix engine (variant graph)
- **K** Templates v2 (publish-ready + governed)
- **I** Queue upgrades (priorities, scheduling windows, failure recovery)

## Deliverables (testable)

### D1 — Batch planner + executor (RQ-019)
- Plan N exports with:
  - concurrency controls
  - overnight scheduling window
  - retry limits + backoff
  - disk-space guard
- Persistent batch state with resume after restart.

### D2 — Remix engine (RQ-020)
Supported variation types:
- visual grading variants (preset families)
- thumbnail variants (safe text layout rules)
- length variants (10s/30s/10m/2h) driven by loop rules
- audio swaps (requires Phase 3 mixer/bounce)
- controlled seed/palette/typography variations

### D3 — Guardrails: minimum meaningful difference (RQ-021)
- Variant distance metric and thresholds:
  - min changed parameters count
  - at least one structural change
  - minimum distance score
- Near-duplicate detection and rejection/flagging.

### D4 — Provenance and reviewer reporting (RQ-045)
- Per-export originality ledger includes:
  - variant graph ID/spec ID
  - distance score
  - changed params summary
- Batch report artifact:
  - summary stats
  - flagged near-duplicates

### D5 — Queue reliability upgrades
- Segment-level resume remains standard.
- Circuit breaker for repeated failures.
- Cleanup policy enforced for batch runs.

## Acceptance criteria (measurable)

### A1 — Overnight batch reliability
- Batch of 100 renders completes with:
  - <2% failure rate
  - failures recoverable via retry
  - no orphan temp files beyond configured threshold

### A2 — Guardrails compliance
- Every batch item passes variant distance checks:
  - differs by at least X parameters (default 5)
  - includes at least one structural change
  - distance score >= threshold

### A3 — Provenance/report artifacts
- Every bundle includes originality ledger updates for remix context.
- Batch produces a reviewer report artifact.

## Verification plan

### Automated
- Unit:
  - TS-007 (variant distance) extended
  - TS-004 job state regression
- Integration:
  - IT-003 segment resume under batch load
- Acceptance:
  - **AT-004** synthetic batch stress suite

### Manual checks
- Reviewer rubric aligned to YouTube guidance:
  - spot-check 20 variants for meaningful differences
  - confirm the report highlights near duplicates

## Dependencies / prerequisites
- Phase 2 preset registry + migrations stable.
- Phase 3 mixer + deterministic bounce (for audio swaps and loop rules).

## Risks + mitigation tasks
- Combinatorial explosion:
  - cap variant graph breadth by default
  - require meaningful variation constraints
- Monetization risk via template-like outputs:
  - enforce guardrails
  - provide creator rubric and warnings
- Machine sleep / interruptions:
  - detect and pause/resume safely
  - robust job persistence

## Explicit out-of-scope (deferred)
- L/M YouTube publishing (Phase 5)
- O/P/Q analytics/research/revenue (Phase 6)
