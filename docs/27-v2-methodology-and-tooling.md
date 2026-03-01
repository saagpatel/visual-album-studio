# V2 Methodology and Tooling Baseline

This document records the methods and tooling selected for V2 execution.

## Delivery methodology
- Quality-first staged train delivery.
- Hard gate rule: required checks cannot be skipped for GA.
- Continuous RCA + downstream revalidation for any gate failure.

## Security and supply chain
- SSDF-aligned secure software practices.
- SLSA-aligned provenance and signed release artifacts.
- Continuous code/dependency/secret scanning.

## Governance workflow
- Protected `main` with required status checks.
- CODEOWNERS ownership map for critical paths.
- Dependabot updates for Actions/Python/Cargo lanes.
- PR dependency review and code scanning workflows.
- If branch protection/rulesets are unavailable on the current repo tier, enforce strict local fallback:
  - install `.codex/scripts/install-prepush-guard.sh`
  - use `scripts/ops/configure_github_branch_protection.sh` for tier-aware best-effort remote setup

## Observability and operational quality
- DORA metrics tracked by train and release candidate.
- OpenTelemetry-aligned trace/log/metric contracts for new cloud/connectors.
- Risk revalidation cadence integrated with release readiness.

## UI/UX quality
- Platform-native interaction norms with tokenized design system.
- Blocking state matrix: loading, empty, error, success, disabled, focus-visible, keyboard-only.
- WCAG 2.2 + WAI-ARIA APG alignment for critical paths.

## Distribution/provider strategy
- Provider abstraction layer with normalized request/status contracts.
- Priority lanes: TikTok first, Instagram second.
- Provider-specific quota/policy guardrails before publish dispatch.

## Cloud baseline
- Supabase + Postgres + Storage + Realtime.
- Local-first workflow continuity is non-negotiable.
- Deterministic and auditable conflict handling model.
- Initial cloud region/residency baseline:
  - region: `us-west-1` (N. California)
  - residency: United States
  - source: `docs/28-v2-cloud-region-and-residency.md`

## Program horizon
- 12-14 months across Train 0..5.
- Train 0 completion is required before Train 1 feature implementation.
