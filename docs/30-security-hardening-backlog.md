# Security Hardening Backlog (Cycle 2026-03-01)

## Scope
- Source findings: security audit + threat model + ownership map review completed on 2026-03-01.
- Program constraint: single-owner model retained (`saagar210`) per current operating decision.
- Canonical hardening evidence SHA: `234e2a619bf71208970e7f548397117e43773073` (merged to `main` during closeout).

## Ownership
- Security owner: `saagar210`
- Backup owner: none (accepted bus-factor=1 risk for current stage).

## Prioritized Remediation Sequence

| Priority | ID | Remediation | Status | Owner | Why First | Verification Gate |
|---|---|---|---|---|---|---|
| P0 | SEC-001 | Remove OAuth access token from subprocess CLI payload; use env handoff only by default | Complete | saagar210 | Directly reduces local secret exposure from process args | `IT-013`, strict `security_audit` |
| P0 | SEC-002 | Remove keyring secret from CLI arg; support `--from-env` and block insecure arg by default | Complete | saagar210 | Eliminates highest-risk local secret leak path for keyring set operations | `IT-004`, strict `security_audit` |
| P0 | SEC-003 | Stop printing raw OAuth secrets in refresh-token helper; write secure file mode `0600` and masked stdout | Complete | saagar210 | Prevents accidental secret leakage into terminals/log captures | helper smoke + strict `security_audit` |
| P0 | SEC-004 | Ignore generated secret file by git (`scripts/test/live.env.generated`) | Complete | saagar210 | Prevents accidental secret commit | strict `repo_hygiene_audit` |
| P1 | SEC-005 | Replace env token/secret handoff with fd/stdin handoff where platform allows | Complete | saagar210 | Further reduces same-host env inspection risk | `IT-004`, `IT-013`, strict verify |
| P1 | SEC-006 | Add explicit denylist check for generated secret filenames in `security_audit.sh` | Complete | saagar210 | Defense-in-depth against accidental secret file retention | strict `security_audit` |
| P2 | SEC-007 | Add recurring ownership-map export artifact for security-critical paths | Complete | saagar210 | Improves long-term maintainability visibility under single-owner model | `scripts/ops/export_security_ownership_map.sh`, scheduled workflow |

## Cycle Evidence
- Strict verify command:
  - `env VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh`
- Latest strict verify evidence on closeout SHA:
  - `head_sha=234e2a619bf71208970e7f548397117e43773073`
  - `security_audit_started=2026-03-01T13:33:48Z`
  - `out/logs/capstone_baseline/security_audit_report.txt`
- Latest strict capstone evidence on closeout SHA:
  - `result[live_closeout]=pass`
  - `capstone_finished=2026-03-01T13:38:47Z`
  - `out/logs/capstone_baseline/capstone_summary.txt`
- Ownership-map export evidence:
  - `out/logs/security/security_ownership_map.md`
  - `out/logs/security/security_ownership_map.json`
  - `.github/workflows/security-ownership-map-cadence.yml`
- Key updated files:
  - `app/src/adapters/youtube_api_adapter.gd`
  - `scripts/youtube_adapter.py`
  - `app/src/adapters/keyring_adapter.gd`
  - `native/vas_keyring/src/main.rs`
  - `scripts/test/get_refresh_token.py`
  - `scripts/test/security_audit.sh`
  - `scripts/ops/export_security_ownership_map.sh`
  - `.github/workflows/security-ownership-map-cadence.yml`
  - `scripts/test/live.env.example`
  - `.gitignore`

## Residual Risk Acceptance
- Single security owner (`bus-factor=1`) is explicitly accepted for this cycle.
- Residual local-host inspection risk remains only for Godot `OS.execute` runtime paths that do not support stdin piping; non-Godot subprocess paths now prefer stdin handoff.
