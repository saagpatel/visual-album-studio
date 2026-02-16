# Phase 5 — Optional YouTube Publishing + Multi-channel

## Objectives
- Provide an optional YouTube publishing pipeline that is:
  - reliable (resumable upload)
  - secure (keychain token storage)
  - quota-aware (budgeting and throttling)
  - audit-ready (handles unverified project restrictions)
- Prevent wrong-channel operational mistakes via explicit bindings.

## Included modules / features
- **L** YouTube integration
- **M** Multi-channel management
- **K** Templates extended for publish profiles
- **I** Uploader job type (network jobs separate from render jobs)

## Deliverables (testable)

### D1 — OAuth installed-app login (RQ-022)
- System browser + loopback redirect.
- PKCE.
- Secure storage:
  - refresh token stored in OS keychain via Rust keyring helper.
  - no plaintext tokens in SQLite or logs.

### D2 — Resumable upload pipeline (RQ-023)
- Use resumable upload protocol.
- Persist session URL + bytes uploaded.
- Resume after interruption or restart.

### D3 — Apply metadata + thumbnail (RQ-024, RQ-025)
- Upload video and apply:
  - title/description/tags/category/privacy
- Upload thumbnail.png with YouTube constraints (<=2MB).
- Provide automatic thumbnail compliance fix if needed.

### D4 — Scheduling + playlists (RQ-026, RQ-027)
- Scheduling via publishAt constraints:
  - private only
  - never published before
- Playlist creation and insertion (optional / could).

### D5 — Multi-channel safety (RQ-028)
- Profiles per channel with explicit binding.
- Prominent channel identity display.
- Confirmation required when switching active channel.

### D6 — Quota budgeting + audit readiness (RQ-051, RQ-052)
- Quota estimation and daily budget enforcement.
- Audit readiness checklist.
- Manual publish fallback remains first-class:
  - bundles are upload-ready without APIs.

## Acceptance criteria (measurable)

### A1 — Upload reliability
- 20 successful uploads in a row using resumable upload.
- Mid-upload network interruption resumes successfully without restarting from 0.

### A2 — Scheduling correctness
- Scheduled publish time applied correctly for at least 10 videos:
  - verify publishAt and privacy transitions

### A3 — Security
- Tokens stored only in keychain.
- Logs/diagnostics contain no tokens or auth codes.

### A4 — Multi-channel safety
- Cannot upload to wrong channel accidentally:
  - upload requires explicit selection/binding to channel profile
  - switching channels requires confirmation

### A5 — Quota-aware behavior
- Planned operations show estimated quota.
- System pauses/throttles when budget exceeded.

## Verification plan

### Automated
- Unit:
  - TS-009 (keyring wrapper)
  - TS-010 (quota calculator)
- Integration:
  - IT-004 (keyring end-to-end)
  - IT-006 (resumable upload mock server)
- Acceptance:
  - **AT-005**

### Manual checks
- OAuth revoke/unlink flow.
- Unverified-project restriction scenario:
  - verify app can still operate in “private-only” mode and manual fallback works.

## Dependencies / prerequisites
- Phase 1–4 bundles stable with provenance/build manifest.
- Job queue supports network job types without interfering with render jobs.

## Risks + mitigation tasks
- Audit restrictions block public uploads:
  - keep publish optional
  - always support manual workflows
- Quota limits:
  - budgeting UI + scheduling
  - reduce high-cost calls

## Explicit out-of-scope (deferred)
- O/P/Q analytics/research/revenue (Phase 6)
- S/T UX platform + productization (Phase 7)
