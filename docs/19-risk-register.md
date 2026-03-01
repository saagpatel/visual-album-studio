# Risk Register (RSK-###)

This register tracks the main project risks across product, engineering, and policy.

Scales:
- **Severity:** High / Medium / Low
- **Likelihood:** High / Medium / Low

## Risks

| Risk ID | Description | Severity | Likelihood | Mitigation | Detection/Monitoring | Owner (Module/Phase) |
|---|---|---|---|---|---|---|
| RSK-001 | Export pipeline fails to be deterministic at frame checkpoints (Phase 1 go/no-go). | High | Medium | Fixed-FPS stepping; seeded RNG only; checkpoint hashing harness; pin Godot/FFmpeg versions. | AT-001 determinism failures pinpoint first divergent checkpoint; diagnostics bundle. | I/C/H (Phase 1) |
| RSK-002 | Long-duration export crashes or cannot resume reliably; leaves corrupted artifacts. | High | Medium | Segment rendering + encode; atomic finalization; persistent job state; cleanup policy. | Kill/crash/resume tests; IT-003; monitor orphan temp files. | I (Phase 1) |
| RSK-003 | Disk blow-up from PNG sequences during long renders. | High | High | Segment rendering + immediate encode; delete frames after encode; disk guardrails; prune UI. | Disk usage dashboard; export logs track peak usage; RQ-053. | I/J (Phase 1) |
| RSK-004 | FFmpeg licensing becomes incompatible with distribution due to GPL components. | High | Medium | Default LGPL-safe build; optional GPL encoder pack opt-in; record license mode in manifest. | Startup license mode checks; build_manifest inspection. | I (Phase 1/3) |
| RSK-005 | Audio provenance requirements cause user friction; users cannot export. | Medium | Medium | Provide draft export mode; clear UI explaining required fields; templates for common sources. | Track blocked export reasons; UX validation. | J/K (Phase 1) |
| RSK-006 | Content ID claims or reused/inauthentic content policies reduce monetization viability. | High | High | Enforce provenance; originality ledger; multiple distinct modes; batch guardrails with reviewer report. | Phase 4 reviewer report; export ledger presence; creator education UI. | J/K/N/R (Phase 1/4) |
| RSK-007 | Motion Poster presets end up too similar ("template spam"). | High | Medium | Require 6+ distinct presets; define structural variation axes; include seed-driven controlled variation. | Manual rubric review; Phase 1 preset diversity checklist. | G/H/K (Phase 1) |
| RSK-008 | GPU/driver differences cause visual mismatches and user mistrust of preview/export parity. | Medium | Medium | Single render graph; avoid nondeterministic GPU features; define determinism boundary clearly. | AT-002 parity suite across modes; regression screenshots. | C (Phase 1/2) |
| RSK-009 | Python worker packaging/venv issues break analysis on user machines. | Medium | Medium | Ship pinned dependencies; bootstrap script; worker health checks; graceful fallback messaging. | IT-001; startup self-test; worker version in manifest. | A (Phase 1) |
| RSK-010 | FFmpeg process management bugs (progress parsing, cancel) cause stuck jobs. | High | Medium | -progress parsing spec; robust process kill; job state machine tests. | IT-002; TS-004 job transitions. | I (Phase 1) |
| RSK-011 | YouTube OAuth fails due to disallowed embedded user agents. | High | Low | System browser + loopback redirect only; never embed webviews. | AT-005 auth flow validation; error code detection. | L (Phase 5) |
| RSK-012 | YouTube uploads restricted to private due to unverified API project/audit constraints. | High | Medium | Treat publishing as optional; support manual upload fallback; audit readiness checklist. | Publish job warns and continues in private mode; UI state. | L/K (Phase 5) |
| RSK-013 | YouTube quota exhaustion blocks publishing workflows. | Medium | High | Quota budgeting UI; throttle/schedule; avoid high-cost calls; caching. | TS-010 quota calculator; publish job logs quota usage. | L/M/N (Phase 5) |
| RSK-014 | Resumable upload implementation is unreliable; uploads restart from 0 after interruption. | High | Medium | Implement resumable protocol properly; persist session URL and byte offset; retry/backoff. | IT-006 mock server; AT-005 interruption test. | L (Phase 5) |
| RSK-015 | Multi-channel confusion leads to wrong-channel uploads. | High | Medium | Explicit channel binding + confirmation; show channel ID/title prominently; require publish profile selection. | AT-005 wrong-channel guard test; UI audit. | M/L (Phase 5) |
| RSK-016 | ML model licensing/distribution issues (Phase 2) create legal risk. | High | Medium | Models optional download; record provenance; do not bundle by default; block production use if license unknown. | Model registry validation; provenance file includes model license. | E/J (Phase 2) |
| RSK-017 | Performance issues for long renders (2h) make product impractical. | High | Medium | Optimize render graph; segment parallelism (where safe); provide quality tiers; monitor render FPS. | Export logs include throughput metrics; profiling runbooks. | C/I (Phase 1/2) |
| RSK-018 | Analytics/revenue availability differs by account; users see empty dashboards. | Medium | High | Graceful degradation; clear “not available” explanations; manual import fallback. | AT-006 “unavailable” paths; UX validation. | P/Q (Phase 6) |
| RSK-019 | Privacy leak via logs/diagnostics (tokens or PII). | High | Low | Redaction enforced by tests; diagnostics export excludes secrets; secure storage only. | Automated log scanning in tests; AT-005 privacy checks. | L/I (Phase 5) |
| RSK-020 | Schema migrations corrupt user data. | High | Low | Forward-only migrations with transactions; backups; migration tests; refuse newer DB. | TS-008 migration runner tests; backup before migration (optional). | J (All phases) |
| RSK-021 | UX refactors regress reliability workflows and hide recoverability controls. | High | Medium | Keep ExportService semantics unchanged; enforce AT-001..AT-006 regression gates during Phase 7 work. | AT-001..AT-007 on every merge candidate; UX smoke runbook for fail/recover paths. | S/I (Phase 7) |
| RSK-022 | Accessibility regressions create keyboard traps and unusable critical paths. | High | Medium | Keyboard/focus contract tests; reduced-motion support; contrast baselines in component tokens. | TS-014, IT-012, AT-007 accessibility checks. | S/C (Phase 7) |
| RSK-023 | Diagnostics bundles leak sensitive information through new support UX. | High | Low | Redaction pipeline as hard gate; schema validation; no environment dumps with secrets. | TS-015 and AT-007 diagnostics redaction assertions. | T/S/I/L/P (Phase 7) |
| RSK-024 | Packaging/update architecture introduces non-deterministic release artifacts. | Medium | Medium | Deterministic manifest generation; pinned toolchain metadata; dry-run packaging gate before release usage. | TS-016 and AT-007 packaging dry-run validation. | T/I/J (Phase 7) |

## Recent updates (2026-03-01)
- Post-V2 Wave 1 (`PV2-001`) closure update:
  - adaptive model-selection drift guard added (missing/checksum mismatch detection).
  - evaluation auto-ingestion now records hardware benchmark telemetry for selection.
  - Wave 1 gates passed: `acceptance_pv2_001`, strict verify, strict capstone (`live_closeout=pass`).
- Post-V2 Wave 0 control-plane kickoff:
  - Post-V2 governance and verification docs published:
    - `docs/36-postv2-phase-blueprint.md`
    - `docs/37-postv2-requirements-traceability.md`
    - `docs/38-postv2-test-verification.md`
  - Post-V2 tracking issues opened: `#19`, `#20`, `#21`, `#22`, `#23`, `#24`.
  - Risk ownership remains single-owner; bus-factor is accepted with ongoing ownership-map cadence.
- V2 GA closeout declaration:
  - release closeout SHA `db9602048675a476ee70302a1509b685b3f3a857` with tags `v2.4.0` and `v2-closeout-2026-03-01` published.
  - post-closeout docs stamp SHA `7d5c1d3e50fe96fe850cf7359f78f3892680388f` revalidated with strict capstone pass.
  - release-blocking milestone issues `#10/#11/#12` closed with evidence-linked comments.
- V2 M3 closure update:
  - Distribution/provider expansion controls delivered and verified (`AT-V2-301` pass).
  - Quota/policy and privacy-redaction checks now covered by `IT-V2-301..305` and unit contracts `TS-V2-301/302`.
- V2 M4 closure update:
  - Cloud/collaboration controls delivered and verified (`AT-V2-401` pass).
  - Threat model signoff published: `docs/35-v2-train4-threat-model.md`.
  - Residency baseline revalidated for Train 4 closeout in `docs/28-v2-cloud-region-and-residency.md`.
- V2 M5 closeout-prep update:
  - Final closeout suites added (`AT-V2-501`, `IT-V2-510`, `IT-V2-511`, `TS-V2-510`).
  - Full acceptance stack (`train1`..`train5`) + strict verify + strict capstone rerun passed with `result[live_closeout]=pass` and `capstone_finished=2026-03-01T15:54:52Z`.
- Closeout context constants:
  - `CLOSEOUT_DATE_UTC=2026-03-01`
  - `CLOSEOUT_EVIDENCE_SHA=f608c203520d00b8b0a33946a502ba8cfdfe8991`
  - `CLOSEOUT_TARGET_TAG=closeout-2026-03-01`
- Phase 0 closure:
  - hardening baseline synchronized to closeout evidence SHA `f608c203520d00b8b0a33946a502ba8cfdfe8991`, removing branch/docs truth drift for release tracking.
- RSK-009 mitigation strengthened:
  - `scripts/bootstrap.sh` now enforces checksum-field validity in `tools/ffmpeg/checksums.json` and verifies managed FFmpeg binary checksums when present.
- RSK-011/RSK-014 mitigation strengthened:
  - `app/src/adapters/youtube_api_adapter.gd` now uses a real runtime sidecar (`scripts/youtube_adapter.py`) with structured retryable error envelopes instead of mock-only adapter behavior.
- RSK-019 mitigation strengthened:
  - `scripts/test/security_audit.sh` supports strict mode and explicit owner+expiry waivers via `docs/security-waivers.json`.
- RSK-019 follow-up closure:
  - strict security audit now passes with `VAS_SECURITY_STRICT=1` and no active waivers; `docs/security-waivers.json` reset to an empty waiver list.
- RSK-011/RSK-014 operational closure update:
  - `scripts/test/live_validation.py` now resolves trusted CA bundles via `VAS_SSL_CA_BUNDLE`, `SSL_CERT_FILE`, and `certifi`, and `scripts/test/capstone_audit.sh` auto-loads `scripts/test/live.env` when available so live closeout can execute in the capstone path on credentialed environments.
- RSK-009/RSK-019 execution hardening update:
  - `scripts/test/unit.sh` now builds `native/vas_keyring/target/debug/vas_keyring` automatically when missing, removing repeated acceptance/capstone failures caused by absent helper binaries.
  - `scripts/test/security_audit.sh` now resolves `bandit` and `pip-audit` from `worker/.venv/bin` before strict-mode failure, reducing environment drift between local and CI gate behavior.
- RSK-019 secret-hygiene hardening update:
  - `scripts/test/repo_hygiene_audit.sh` now blocks tracked `.env` files (while allowing template files such as `.example`).
  - `scripts/test/security_audit.sh` now detects Google OAuth-style secret patterns in tracked files.
- RSK-019 keyring dependency closure update:
  - `native/vas_keyring` upgraded from `keyring 2.3.3` to `keyring 3.6.3` (with native platform features), and keyring CLI compatibility updated for `delete_credential`.
  - `cargo audit` now reports no advisory warnings for `native/vas_keyring/Cargo.lock`.
- RSK-019 hardening continuation update:
  - `native/vas_keyring/src/main.rs` now supports `--from-stdin` for `set`, and `scripts/test/live_validation.py` / `IT-004` now use stdin secret handoff where supported.
  - `scripts/youtube_adapter.py` now supports optional `--token-stdin` mode for non-Godot subprocess callers (`IT-013` coverage).
  - `scripts/test/security_audit.sh` now enforces generated secret filename denylist checks (`scripts/test/live.env.generated`, `.env.generated`).
- Ownership map cadence update:
  - `scripts/ops/export_security_ownership_map.sh` exports security-critical ownership artifacts to `out/logs/security/*`.
  - `.github/workflows/security-ownership-map-cadence.yml` publishes recurring ownership-map artifacts on weekly cadence.
- Phase 4-6 capstone evidence update:
  - `env VAS_SECURITY_STRICT=1 ./scripts/test/capstone_audit.sh` passed end-to-end on `2026-03-01` with `result[acceptance_phase_04]=pass`, `result[acceptance_phase_05]=pass`, `result[acceptance_phase_06]=pass`, and `result[live_closeout]=pass`.
  - Latest live closeout now reports zero skips:
    - Phase 5: resumable upload interruption/resume passed using fixture evidence.
    - Phase 6: revenue API 403 handled as policy-compliant fallback pass with `AT-006` fallback verification.
- Final closeout acceptance update:
  - strict verification + strict capstone reruns passed on `f608c203520d00b8b0a33946a502ba8cfdfe8991`.
  - closeout capstone finished `2026-03-01T06:21:32Z` with `result[live_closeout]=pass`.
  - release checkpoint tag `closeout-2026-03-01` published on GitHub.
  - `docs/security-waivers.json` remains empty (no temporary waivers active).
  - residual risks are accepted with owners/modules and periodic review in `docs/22-project-closeout-report.md`.

## Operational Revalidation Cadence
- Recurring cadence is now scheduled and documented:
  - Workflow automation: `.github/workflows/risk-revalidation-cadence.yml`
  - Cadence policy: `docs/24-risk-revalidation-cadence.md`
- Cadence lanes:
  - Weekly (Monday 16:00 UTC): `RSK-013`
  - Monthly (day 1, 16:00 UTC): `RSK-006`, `RSK-012`, `RSK-018`, `RSK-024`
  - Release-train manual trigger: `RSK-024`

## V2 Program Risk Additions (Train 0 Baseline)

| Risk ID | Description | Severity | Likelihood | Mitigation | Detection/Monitoring | Owner (Module/Phase) |
|---|---|---|---|---|---|---|
| RSK-V2-001 | Cloud sync/collaboration complexity degrades local-first reliability guarantees. | High | Medium | Keep local-first as default, enforce offline-safe degradation, and gate cloud features behind deterministic sync contracts. | `AT-V2-401`, outage simulation scenarios, sync replay logs. | S/T + V2 Cloud (Train 4) |
| RSK-V2-002 | 4K default lane introduces determinism/performance regressions versus v1 baseline. | High | Medium | Add 4K determinism fixtures, long-run resume tests, and performance budget gates before default-lane promotion. | `AT-V2-101`, 4K benchmark trend reports, rerun hash drift alerts. | I/C/H (Train 1) |
| RSK-V2-003 | Multi-provider policy/quota drift causes publish instability or compliance regressions. | High | High | Provider-specific guardrails, quota-aware schedulers, and policy-change monitoring with adapter contract tests. | `AT-V2-301`, provider error taxonomy dashboards, revalidation cadence issues. | L/M + V2 Distribution (Train 3) |
| RSK-V2-004 | ML model provenance/licensing ambiguity introduces legal/security risk. | High | Medium | Enforce model checksum/provenance policy, license metadata requirements, and allowlist-only model registry. | `AT-V2-201`, model registry audits, security review checks. | E/J + V2 Model Registry (Train 2) |
| RSK-V2-005 | UI complexity from collaboration + multi-provider workflows harms usability/accessibility. | Medium | Medium | Tokenized UI system, mandatory state coverage, and blocking WCAG 2.2/accessibility gates for critical paths. | UI gate reports, `AT-V2-501` accessibility assertions, usability review findings. | S (Train 0-5) |
