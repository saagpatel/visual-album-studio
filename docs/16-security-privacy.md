# Security & Privacy

Security and privacy requirements are non-negotiable. The product is local-first and must not leak secrets or sensitive user data.

## Threat model (practical)

### Assets at risk
- OAuth refresh tokens (Phase 5+)
- User media assets (audio/images)
- Channel identifiers and analytics
- Export outputs and metadata
- Logs and diagnostic bundles

### Adversaries
- Local attacker with access to the user’s filesystem (malware, shared machine).
- Accidental leakage through logs/bug reports.
- Network attacker (MITM) during YouTube API calls (mitigated by TLS + official endpoints).

## Security principles
- **Least privilege:** request minimum OAuth scopes.
- **No plaintext secrets:** never store tokens in SQLite or files.
- **Explicit boundaries:** only YouTube/Analytics modules can talk to network.
- **Safe logging:** redact secrets and minimize PII.

## OAuth + secure storage (Phase 5+)

### Token storage
- Refresh tokens stored only in OS secure storage (Keychain on macOS) using Rust `keyring`.
- DB stores only a stable keyring account identifier.

### Token access patterns
- Tokens are fetched from keychain only when needed.
- Access tokens are short-lived and stored in memory only.
- Token rotation and revocation are supported:
  - unlink removes keychain entries and local bindings.

### Anti-footgun rules
- Never log:
  - authorization codes
  - access tokens
  - refresh tokens
  - HTTP Authorization headers
- Sanitization is enforced by tests (RQ-039).

## Logging hygiene

### Logging levels
- `info`: high-level progress (safe)
- `warn`: recoverable issues (safe)
- `error`: failures with redacted details

### Redaction rules
- Any string matching token patterns is replaced with `***REDACTED***`.
- HTTP logs:
  - log status code and endpoint path
  - do not log headers or full body by default

### Diagnostics export
- Includes:
  - sanitized logs
  - job summaries
  - toolchain versions
  - DB schema version
- Excludes by default:
  - tokens
  - raw assets
  - full analytics payloads (unless explicitly opted in)

## Privacy boundaries
- Offline-first means:
  - no telemetry by default
  - no automatic cloud sync
- Optional YouTube/analytics sync is user-initiated and clearly labeled.

## Data retention and user controls
- Users can:
  - relocate library and exports directories
  - prune caches (analysis artifacts, temp workspaces)
  - delete channel profiles and analytics snapshots
  - backup/restore DB and library (Phase 6)

## Verification checklist
- Unit tests:
  - no token fields in schema
  - redaction function behavior
- Integration tests:
  - keyring helper stores/retrieves/deletes secrets
- Acceptance tests:
  - Phase 5 ensures no tokens appear in logs or diagnostics export
