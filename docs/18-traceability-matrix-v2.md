# Traceability Matrix V2 (RQ-V2 -> Scope -> Tests)

Legend:
- Scope areas: Train 0..5
- Test IDs:
  - `TS-V2-*` Unit
  - `IT-V2-*` Integration
  - `AT-V2-*` Acceptance
  - `RT-V2-*` Resilience/Chaos

| RQ ID | Scope Area | Train | Test IDs |
|---|---|---|---|
| RQ-V2-001 | V2 canonical spec pack | Train 0 | AT-V2-000 |
| RQ-V2-002 | Governance CI gates | Train 0 | IT-V2-001, AT-V2-000 |
| RQ-V2-003 | ADR-backed cloud/conflict decisions | Train 0 | AT-V2-000 |
| RQ-V2-004 | UI quality baseline contracts | Train 0 | TS-V2-010, AT-V2-000 |
| RQ-V2-005 | Provenance/release integrity definition | Train 0 | IT-V2-002, AT-V2-000 |
| RQ-V2-101 | 4K determinism lane | Train 1 | TS-V2-101, AT-V2-101 |
| RQ-V2-102 | 4K long-run resume reliability | Train 1 | IT-V2-101, RT-V2-101, AT-V2-101 |
| RQ-V2-103 | Signed artifact production | Train 1 | IT-V2-102, AT-V2-101 |
| RQ-V2-104 | Channel promotion controls | Train 1 | IT-V2-103, AT-V2-101 |
| RQ-V2-105 | Release manifest v2 provenance fields | Train 1 | TS-V2-102, IT-V2-102 |
| RQ-V2-201 | New modes on mapping/preset contracts | Train 2 | TS-V2-201, AT-V2-201 |
| RQ-V2-202 | Preview/export parity for new modes | Train 2 | IT-V2-201, AT-V2-201 |
| RQ-V2-203 | ML model checksum/provenance policy | Train 2 | TS-V2-202, IT-V2-202 |
| RQ-V2-204 | ML fallback behavior | Train 2 | IT-V2-203, AT-V2-201 |
| RQ-V2-205 | Model evaluation harness | Train 2 | TS-V2-203, IT-V2-204 |
| RQ-V2-301 | Provider-agnostic distribution adapter | Train 3 | TS-V2-301, IT-V2-301 |
| RQ-V2-302 | TikTok lane | Train 3 | IT-V2-302, AT-V2-301 |
| RQ-V2-303 | Instagram lane | Train 3 | IT-V2-303, AT-V2-301 |
| RQ-V2-304 | Provider-specific quota/policy controls | Train 3 | TS-V2-302, IT-V2-304, RT-V2-301 |
| RQ-V2-305 | Privacy-safe connector expansion | Train 3 | IT-V2-305, AT-V2-301 |
| RQ-V2-401 | Local-first preserving cloud sync | Train 4 | IT-V2-401, AT-V2-401 |
| RQ-V2-402 | Collaboration RBAC | Train 4 | TS-V2-401, IT-V2-402, AT-V2-401 |
| RQ-V2-403 | Deterministic/auditable conflict resolution | Train 4 | TS-V2-402, IT-V2-403, RT-V2-401 |
| RQ-V2-404 | Versioned cloud references | Train 4 | TS-V2-403, IT-V2-404 |
| RQ-V2-405 | Cloud outage fail-safe local mode | Train 4 | RT-V2-402, AT-V2-401 |
| RQ-V2-501 | Canonical SHA full-suite green | Train 5 | AT-V2-501 |
| RQ-V2-502 | Carry-forward v1 strict gates green | Train 5 | AT-V2-501 |
| RQ-V2-503 | Accessibility for critical V2 workflows | Train 5 | TS-V2-510, IT-V2-510, AT-V2-501 |
| RQ-V2-504 | Supply-chain/provenance checks green | Train 5 | IT-V2-511, AT-V2-501 |
| RQ-V2-505 | V2 closeout evidence report | Train 5 | AT-V2-501 |

## Train gate summaries
- `AT-V2-000`: Train 0 spec/governance readiness.
- `AT-V2-101`: Train 1 4K + signing.
- `AT-V2-201`: Train 2 rendering/ML.
- `AT-V2-301`: Train 3 provider/connectors.
- `AT-V2-401`: Train 4 collaboration/cloud.
- `AT-V2-501`: Train 5 final full-candidate validation.
