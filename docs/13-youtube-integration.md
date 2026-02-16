# YouTube Integration (Phase 5)

YouTube integration is **optional** and strictly deferred to Phase 5. The product must remain fully usable offline without YouTube access.

This document specifies auth, upload, quota behavior, and failure modes.

## Non-negotiable constraints
- OAuth must use installed-app flow via **system browser** + **loopback redirect**.
- Avoid embedded webviews and embedded user agents.
- Use the **resumable upload protocol** for reliability.
- Be quota-aware and audit-ready.
- Uploads from unverified API projects may be restricted to **private** until an audit is passed.

## Auth flow

### OAuth approach (installed app)
- Use OAuth 2.0 for native apps with:
  - PKCE
  - loopback redirect URI: `http://127.0.0.1:<port>/oauth/callback`
  - system browser launch

### Token lifecycle
- Store refresh tokens in OS secure storage:
  - macOS Keychain via Rust `keyring` helper
- Store in SQLite only:
  - `oauth_profiles.keyring_account` (identifier)
  - channel bindings and metadata

Required capabilities:
- Connect account (obtain refresh token)
- Refresh access token automatically
- Unlink account:
  - revoke token (if supported)
  - delete keychain entry
  - remove local bindings

### Multi-channel binding safety (RQ-028)
- Each publish profile is bound to:
  - OAuth profile
  - channel ID
  - template ID
- Upload UI must show channel title + channel ID explicitly.
- Switching active channel requires explicit confirmation.

## Upload pipeline

### Inputs
- A completed export bundle:
  - `video.mp4`
  - `thumbnail.png`
  - `metadata.json`
  - `provenance.json`

### Upload job stages
1. Validate bundle integrity and metadata schema.
2. Ensure quota budget sufficient (estimated).
3. Start resumable upload session.
4. Upload bytes in chunks, persisting session URL and progress.
5. Apply metadata (title/description/tags/category/privacy).
6. Upload thumbnail (if enabled).
7. Scheduling:
   - apply `publishAt` when allowed by YouTube constraints
8. Playlist operations (optional):
   - create playlist
   - add video to playlist

### Resumable upload requirements
- Persist:
  - session URL
  - bytes_uploaded
  - file hash + size
- Resume rules:
  - after crash/restart, job can resume using stored session URL
  - if server invalidates session, restart upload and record reason

### Retry/backoff
- Transient errors (5xx, timeouts) use exponential backoff with jitter.
- Permanent errors (4xx) fail fast with actionable remediation.

## Quota-aware behavior

### Quota estimation
Before executing a publish batch, estimate quota costs:
- `videos.insert` cost ~100 units per upload
- `thumbnails.set` cost ~50 units
- playlist operations ~50 units
- search/list operations can be expensive (~100 units)

### Budgeting rules (RQ-051)
- Maintain a daily quota budget model:
  - warn before exceeding
  - throttle/pause when exceeded
- Provide a “quota simulation” view for planned operations.

## Scheduling rules (YouTube constraints)
- Scheduling requires:
  - privacy status initially private
  - video has never been published
- The publish profile determines:
  - `privacyStatus` default
  - `publishAt` timestamp (optional)

If constraints not met:
- The app must refuse scheduling and explain why.

## Chapters support
- Bundles may include chapter markers in metadata.json.
- Phase 5 upload applies chapters via description formatting (if supported by YouTube rules) or via metadata update APIs where applicable.

## Safe degradation & manual fallback
If YouTube APIs fail, quota exhausted, or unverified project restrictions apply:
- The bundle remains usable:
  - user can upload manually via YouTube Studio
  - metadata.json and provenance attribution block are copy/paste-ready
- Provide an in-app “Manual Publish Checklist”:
  - upload video.mp4
  - set title/description/tags from metadata.json
  - apply thumbnail.png
  - paste attribution block if required
  - set privacy/schedule

## Verification (Phase 5)
- Acceptance test AT-005 validates:
  - OAuth via system browser + loopback
  - secure token storage (no plaintext)
  - 20 resumable uploads with interruption recovery
  - correct scheduling behavior for 10 videos
  - wrong-channel protection
  - quota estimation and throttling behavior (mock or controlled environment)
