# Post-V2 Backlog

## Source of deferred items
This backlog captures work intentionally deferred beyond V2 GA after delivery of `PV1-001..PV1-008`. Source set:
- `docs/23-post-v1-backlog.md`
- `docs/20-phase-blueprint-v2.md`
- Train 3/4 execution notes and closeout follow-ups

## Rendering and ML enhancements
| Item | Description | Reason deferred | Priority | Suggested phase/quarter | Dependency notes |
|---|---|---|---|---|---|
| PV2-001 | Adaptive model auto-selection by hardware profile | Requires expanded benchmark matrix and wider hardware telemetry | P1 | Post-V2 Q2 | Needs model-eval harness expansion |
| PV2-002 | Cross-project style transfer preset exchange | UX governance and safety policy not finalized in V2 | P2 | Post-V2 Q3 | Depends on collaboration permissions extensions |

## Distribution and platform expansions
| Item | Description | Reason deferred | Priority | Suggested phase/quarter | Dependency notes |
|---|---|---|---|---|---|
| PV2-101 | Additional platform adapters beyond TikTok/Instagram/YouTube | V2 focused on first two provider expansions | P1 | Post-V2 Q2 | Reuse `DistributionAdapter` contract |
| PV2-102 | Provider-specific scheduling optimization engine | Initial quota/policy controls meet V2 scope | P2 | Post-V2 Q3 | Requires production telemetry sample size |

## Collaboration and cloud features
| Item | Description | Reason deferred | Priority | Suggested phase/quarter | Dependency notes |
|---|---|---|---|---|---|
| PV2-201 | Multi-region replication + residency mobility | Explicitly deferred by residency baseline | P1 | Post-V2 Q3 | Requires ADR + migration plan |
| PV2-202 | Team-level audit dashboards and anomaly detection | V2 shipped core conflict/audit records only | P2 | Post-V2 Q4 | Depends on cloud telemetry aggregation |
