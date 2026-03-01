# Next-Cycle Requirements Traceability Matrix

Legend:
- Test IDs:
  - `TS-NC-*` unit
  - `IT-NC-*` integration
  - `AT-NC-*` acceptance
- Status: `not-started`, `in-progress`, `pass`, `fail`

| RQ ID | Item | Requirement statement | Primary modules/interfaces | Planned tests | Status |
|---|---|---|---|---|---|
| RQ-NC-001 | NC-001 | Automated DR rehearsal runner must execute deterministic failover drill and produce replay-safe report artifacts. | DR runner + replication services | TS-NC-001, IT-NC-001, AT-NC-001 | not-started |
| RQ-NC-002 | NC-002 | Auto-triage enrichment must attach historical context and recommended remediations to anomaly signals. | `AuditDashboardServiceV1` extensions | TS-NC-002, IT-NC-002, AT-NC-002 | not-started |
| RQ-NC-003 | NC-003 | Provider policy watcher must ingest policy snapshots, detect diffs, persist changelog events, and emit remediation recommendations. | `ProviderPolicyWatcherV1` | TS-NC-003, IT-NC-003, AT-NC-003 | pass |
| RQ-NC-101 | NC-101 | Preset trust UI must expose signature/provenance state across loading/error/success and keyboard-only flows. | UX surfaces + preset exchange integration | TS-NC-101, IT-NC-101, AT-NC-101 | not-started |
| RQ-NC-102 | NC-102 | Scheduler simulation dashboard must provide side-by-side provider timeline previews with policy/quota overlays. | Scheduling UI + `DistributionSchedulingServiceV1` | TS-NC-102, IT-NC-102, AT-NC-102 | not-started |
| RQ-NC-103 | NC-103 | Collaboration timeline visualizer must render replay/conflict events with deterministic ordering and accessible controls. | Collaboration timeline UX + conflict/replay logs | TS-NC-103, IT-NC-103, AT-NC-103 | not-started |
| RQ-NC-201 | NC-201 | New provider lanes must be gated by feature flags and policy readiness checks by default. | `DistributionServiceV2` feature-flag surface | TS-NC-201, IT-NC-201, AT-NC-201 | not-started |
| RQ-NC-202 | NC-202 | Residency templates must offer compliance-profile defaults without breaking existing residency routing. | Residency policy template service | TS-NC-202, IT-NC-202, AT-NC-202 | not-started |
| RQ-NC-203 | NC-203 | Audit dashboard exports must generate shareable support bundles with sensitive data redaction. | Audit export service + diagnostics bundle integration | TS-NC-203, IT-NC-203, AT-NC-203 | not-started |
