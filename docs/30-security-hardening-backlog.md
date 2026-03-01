# Security Hardening Backlog (Cycle 2026-03-01)

## Scope
- Source findings: security audit + threat model + ownership map review completed on 2026-03-01.
- Program constraint: single-owner model retained (`saagar210`) per current operating decision.
- Canonical branch/SHA at cycle close: `main` / `38dac43e96b0e6d7b97dfb7eaabd96e774d03a70`.

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
| P1 | SEC-005 | Replace env token/secret handoff with fd/stdin handoff where platform allows | Planned | saagar210 | Further reduces same-host env inspection risk | New integration test + strict verify |
| P1 | SEC-006 | Add explicit denylist check for generated secret filenames in `security_audit.sh` | Planned | saagar210 | Defense-in-depth against accidental secret file retention | strict `security_audit` |
| P2 | SEC-007 | Add recurring ownership-map export artifact for security-critical paths | Planned | saagar210 | Improves long-term maintainability visibility under single-owner model | scheduled report validation |

## Cycle Evidence
- Strict verify command:
  - `env VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh`
- Latest strict verify evidence on closeout SHA:
  - `head_sha=38dac43e96b0e6d7b97dfb7eaabd96e774d03a70`
  - `security_audit_started=2026-03-01T13:19:17Z`
  - `out/logs/capstone_baseline/security_audit_report.txt`
- Key updated files:
  - `app/src/adapters/youtube_api_adapter.gd`
  - `scripts/youtube_adapter.py`
  - `app/src/adapters/keyring_adapter.gd`
  - `native/vas_keyring/src/main.rs`
  - `scripts/test/get_refresh_token.py`
  - `scripts/test/live.env.example`
  - `.gitignore`

## Residual Risk Acceptance
- Single security owner (`bus-factor=1`) is explicitly accepted for this cycle.
- Residual local-host inspection risk remains for env-based handoff and is tracked as `SEC-005`.
