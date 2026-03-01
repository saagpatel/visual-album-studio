# Residual Risk Revalidation Cadence

## Purpose
Define and operationalize recurring revalidation of accepted residual risks documented in `docs/19-risk-register.md` and `docs/22-project-closeout-report.md`.

## Cadence Model

### Weekly cadence (Monday 16:00 UTC)
- Focus risk: `RSK-013` (YouTube quota exhaustion and quota-aware behavior drift)
- Trigger: scheduled GitHub Actions workflow
- Output: one GitHub issue with weekly checklist

### Monthly cadence (day 1, 16:00 UTC)
- Focus risks:
  - `RSK-006` (content-policy/inauthentic-content risk)
  - `RSK-012` (unverified API project/audit restriction risk)
  - `RSK-018` (analytics/revenue availability variance risk)
  - `RSK-024` (packaging nondeterminism risk)
- Trigger: scheduled GitHub Actions workflow
- Output: one GitHub issue with monthly checklist

### Release-train cadence (manual)
- Focus risk: `RSK-024`
- Trigger: manual run (`workflow_dispatch`) of risk cadence workflow before release packaging/signing activities
- Output: issue/checklist with explicit release-train evidence links

## Automation
- Workflow: `.github/workflows/risk-revalidation-cadence.yml`
- Behavior:
  - Opens a dated cadence issue when no matching open issue exists.
  - Includes required checks for strict verification, capstone evidence, and waiver status.
- Ownership-map export automation:
  - Workflow: `.github/workflows/security-ownership-map-cadence.yml`
  - Script: `scripts/ops/export_security_ownership_map.sh`
  - Output artifacts:
    - `out/logs/security/security_ownership_map.md`
    - `out/logs/security/security_ownership_map.json`

## Required Evidence for Each Cadence Run
1. Latest strict verify result:
   - `env VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh`
2. Latest capstone/live-closeout status:
   - `out/logs/capstone_baseline/capstone_summary.txt`
3. Current waiver status:
   - `docs/security-waivers.json`

## Owner and Escalation
- Owners follow module ownership in `docs/19-risk-register.md`.
- Escalate immediately when:
  - required checks fail,
  - `live_closeout` regresses from `pass`, or
  - any temporary waiver is needed without a bounded owner+expiry.
