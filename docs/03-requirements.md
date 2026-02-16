# Requirements (RQ-###)

This document defines the complete set of product and non-functional requirements for Visual Album Studio.

- Requirement IDs **RQ-###** are stable and must not be renumbered.
- Tests are referenced by:
  - **TS-###** (unit)
  - **IT-###** (integration)
  - **AT-###** (phase acceptance gates)

See `docs/18-traceability-matrix.md` for the authoritative mapping.

## Priorities
- **Must:** required for correctness, safety, or Phase gating.
- **Should:** high-value; planned in the defined phase but may be reduced in scope if risk threatens gates.
- **Could:** valuable but optional; implemented only if it does not threaten Must/Should gates.

## Requirements list
### RQ-001 — Local-first desktop editor; offline capable by default

**Priority:** Must  
**Modules:** C (Visual engine foundation), J (Asset library manager)  
**Phase(s):** Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, Phase 6  
**Verification:** AT-001, TS-004

**Description**  
The application operates as a local-first desktop editor. Core creation (import, edit, preview, export) must work with no network connectivity. Network is used only for optional YouTube/analytics features in later phases.

**Rationale**  
Local-first is a hard constraint in the Decision Pack and enables reliability, privacy, and predictable workflows.

**Acceptance criteria**  
- With network disabled, user can create a project, import assets, preview, and export a production bundle (Phase 1).
- All network calls are isolated to YouTube/Analytics modules and can be disabled globally.

### RQ-002 — Import audio files and normalize into a canonical WAV cache

**Priority:** Must  
**Modules:** A (Audio import + analysis), J (Asset library manager)  
**Phase(s):** Phase 1  
**Verification:** TS-001, IT-001, AT-001

**Description**  
Users can import common audio formats; the app decodes/resamples into a canonical WAV cache used for analysis and export.

**Rationale**  
Deterministic downstream processing requires a canonical audio representation.

**Acceptance criteria**  
- Import supports at least: WAV, MP3, FLAC, M4A/AAC, AIFF (via FFmpeg).
- Canonical WAV parameters are fixed and documented (48kHz, stereo, PCM s16le).
- Re-importing the same file results in the same SHA-256 and reuses the cached WAV.

### RQ-003 — Compute BPM + beat grid + persistent analysis cache

**Priority:** Must  
**Modules:** A (Audio import + analysis), J (Asset library manager)  
**Phase(s):** Phase 1, Phase 3  
**Verification:** IT-001, TS-008, AT-001

**Description**  
Compute tempo (BPM) and beat grid for imported audio and persist results keyed by (audio_hash, analysis_version).

**Rationale**  
Beat-synced visuals and determinism depend on stable analysis results and caching.

**Acceptance criteria**  
- Analysis returns BPM and an ordered list of beat timestamps (seconds) spanning the track.
- Analysis results are cached in SQLite keyed by (audio_sha256, analysis_version).
- Changing analysis_version forces cache recompute and preserves prior cached versions.

### RQ-004 — One production-grade visual mode in Phase 1

**Priority:** Must  
**Modules:** C (Visual engine foundation), G (Motion poster mode)  
**Phase(s):** Phase 1  
**Verification:** AT-001, TS-003

**Description**  
Provide at least one visually distinctive, production-usable visual mode in Phase 1 (Motion Poster v1).

**Rationale**  
Phase 1 must ship an end-to-end bundle with a strong visual path to reduce template spam risk.

**Acceptance criteria**  
- Motion Poster mode supports album art + typography + subtle motion.
- At least 6 presets exist that look meaningfully different.
- All parameters used in the mode are addressable via the mapping/preset system.

### RQ-005 — Map audio features → visual parameters with stable parameter IDs

**Priority:** Must  
**Modules:** H (Mapping + presets), A (Audio import + analysis), C (Visual engine foundation)  
**Phase(s):** Phase 1, Phase 2, Phase 3, Phase 4  
**Verification:** TS-002, TS-003, AT-001, AT-002

**Description**  
Provide a mapping system that converts audio features (BPM/beat phase/etc.) into visual parameter values using stable, versioned parameter IDs.

**Rationale**  
Stable parameter IDs and mapping governance prevent brittle per-mode code and enable remixing/batching later.

**Acceptance criteria**  
- Each exposed visual parameter has a stable ID and type (float/int/bool/color/etc.).
- Mappings reference parameters by stable IDs (not by scene node paths).
- Given the same inputs (analysis, time, seed), mapping outputs are deterministic.

### RQ-006 — Real-time preview consistent with offline render

**Priority:** Must  
**Modules:** C (Visual engine foundation), H (Mapping + presets)  
**Phase(s):** Phase 1, Phase 2  
**Verification:** AT-001, AT-002, IT-003

**Description**  
The real-time preview must match offline render in look and timing semantics (within defined determinism boundaries).

**Rationale**  
Preview/export parity is a core architectural decision (single deterministic render graph).

**Acceptance criteria**  
- Preview and offline use the same render graph and mapping functions.
- Offline uses fixed FPS stepping; preview uses audio-clocked playhead but produces the same look for the same time value.
- Golden projects show no visually significant differences between preview capture and offline render (Phase 1+).

### RQ-007 — Offline render supports 10s–2h+ reliably

**Priority:** Must  
**Modules:** I (Render/export pipeline), C (Visual engine foundation)  
**Phase(s):** Phase 1, Phase 2, Phase 3, Phase 4  
**Verification:** AT-001, IT-003

**Description**  
Offline rendering must support durations from 10 seconds to 2+ hours with segmentation, progress reporting, and crash resilience.

**Rationale**  
Export reliability for long durations is a highest priority non-functional requirement.

**Acceptance criteria**  
- Exports complete successfully for 10s, 10min, and 2h at 1080p30 using the reference test projects.
- Render pipeline uses segmentation; resume can restart from last completed segment.
- Progress is reported continuously with ETA and segment-level status.

### RQ-008 — Export bundle: MP4 + thumbnail + metadata JSON

**Priority:** Must  
**Modules:** I (Render/export pipeline), K (Templates & presets (metadata + render))  
**Phase(s):** Phase 1, Phase 2, Phase 3, Phase 4, Phase 5  
**Verification:** TS-005, AT-001

**Description**  
Export produces a production bundle folder containing: video.mp4, thumbnail.png, metadata.json, provenance.json, build_manifest.json.

**Rationale**  
Offline-first workflow requires complete outputs that can be uploaded manually or via Phase 5 automation.

**Acceptance criteria**  
- Bundle folder contains the five required files with exact names.
- metadata.json conforms to the documented schema and includes YouTube-ready fields.
- build_manifest.json includes pinned toolchain versions and preset/mapping identifiers.

### RQ-009 — Crash-safe render queue with progress + cancel

**Priority:** Must  
**Modules:** I (Render/export pipeline)  
**Phase(s):** Phase 1, Phase 2, Phase 3, Phase 4  
**Verification:** TS-004, IT-002, AT-001

**Description**  
Provide a persistent render queue supporting progress reporting, cancellation, and crash recovery.

**Rationale**  
Long renders must be controllable and resilient to failures.

**Acceptance criteria**  
- Cancel mid-export leaves no corrupted final output artifacts.
- On app restart after crash, in-progress jobs are recovered into a resumable state.
- Queue persists in SQLite and supports at least queued/running/paused/canceled/failed/succeeded states.

### RQ-010 — Segment-based resume for long renders

**Priority:** Must  
**Modules:** I (Render/export pipeline)  
**Phase(s):** Phase 1, Phase 2, Phase 3, Phase 4  
**Verification:** IT-003, AT-001

**Description**  
Long renders are segmented and resumable at segment boundaries; completed segments are reused on resume.

**Rationale**  
Segmentation reduces failure blast radius and enables practical resume semantics.

**Acceptance criteria**  
- Resuming a canceled/failed 2h export reuses already completed segment encodes.
- Segment boundaries align to whole-frame durations (integer frames) to prevent A/V drift.
- Segment list + concat operation is deterministic and produces a playable final MP4.

### RQ-011 — Asset metadata supports license provenance and attribution notes

**Priority:** Must  
**Modules:** J (Asset library manager)  
**Phase(s):** Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, Phase 6  
**Verification:** TS-006, AT-001

**Description**  
Assets, especially audio, must support license provenance metadata and attribution text required for safe publishing.

**Rationale**  
Copyright/Content ID and monetization policies require provenance as a design constraint.

**Acceptance criteria**  
- Audio assets require source_type and license notes before 'production export' is allowed.
- provenance.json includes an attribution block when required (e.g., Creative Commons).
- Assets can store proof references (license certificate, receipt, URL) as file paths.

### RQ-012 — Templates: per-channel default title/description/tags schemas

**Priority:** Must  
**Modules:** K (Templates & presets (metadata + render))  
**Phase(s):** Phase 1, Phase 4, Phase 5  
**Verification:** IT-005, AT-001, AT-004

**Description**  
Provide templates for metadata and visual presets, including per-channel defaults used for exports and later publishing.

**Rationale**  
Templates keep output consistent and reduce repetitive manual work, while being governed to avoid spam risk.

**Acceptance criteria**  
- Template defines title/description/tags patterns using variables.
- Template can be selected per project and per channel profile (Phase 5).
- Template changes do not retroactively modify prior export bundles.

### RQ-013 — Beat-synced particle mode

**Priority:** Should  
**Modules:** D (Beat-synced particles), C (Visual engine foundation), H (Mapping + presets)  
**Phase(s):** Phase 2  
**Verification:** AT-002

**Description**  
Provide a beat-synced particle visual mode with parameters addressable via mapping system.

**Rationale**  
Adds visual diversity and reduces reliance on a single template-like mode.

**Acceptance criteria**  
- Particle mode exports with preview/offline parity.
- At least 3 presets demonstrate materially different looks.

### RQ-014 — Photo animator supports non-ML tier (manual depth/parallax)

**Priority:** Should  
**Modules:** E (Photo animator), C (Visual engine foundation)  
**Phase(s):** Phase 2  
**Verification:** AT-002

**Description**  
Photo animator must support a non-ML Tier 0 mode (Ken Burns + procedural parallax with manual depth mask tooling).

**Rationale**  
Keeps feature accessible without large models and avoids licensing/distribution complexity.

**Acceptance criteria**  
- Tier 0 works without downloading any ML model weights.
- User can define/adjust depth mask or parallax layers and preview offline parity holds.

### RQ-015 — Photo animator supports optional local ML tier (depth/segment)

**Priority:** Could  
**Modules:** E (Photo animator)  
**Phase(s):** Phase 2  
**Verification:** AT-002, IT-001

**Description**  
Provide optional local ML Tier 1 for depth estimation and segmentation, executed locally with CPU fallback.

**Rationale**  
Improves quality for users who opt-in, while remaining optional to control size/licensing risk.

**Acceptance criteria**  
- Tier 1 is gated behind explicit user download/enablement.
- If acceleration (CoreML EP) is unavailable, CPU fallback works with a warning.
- Model versions and licenses are recorded in provenance/build manifest.

### RQ-016 — Landscape mode with audio-reactive geometry

**Priority:** Should  
**Modules:** F (Audio-to-3D landscape), C (Visual engine foundation), H (Mapping + presets)  
**Phase(s):** Phase 2  
**Verification:** AT-002

**Description**  
Provide a landscape/terrain mode with audio-reactive displacement and grading presets.

**Rationale**  
Adds a distinctive 3D visual path and reduces template spam risk.

**Acceptance criteria**  
- Landscape mode exports deterministically with fixed FPS stepping.
- At least 3 grading presets exist and are mapping-addressable.

### RQ-017 — Mixer supports multi-track soundscape projects

**Priority:** Should  
**Modules:** B (Soundscape mixer)  
**Phase(s):** Phase 3  
**Verification:** AT-003

**Description**  
Provide a mixer for multi-track audio arrangements (volume, pan, start offset, looping region, fades).

**Rationale**  
Multi-track soundscapes enable richer, more original audio outputs.

**Acceptance criteria**  
- User can add at least 20 tracks and adjust volume/pan/offset and loop regions.
- Mixer state is persisted and reflected in offline bounce.

### RQ-018 — Offline bounce to WAV is deterministic and loop-safe

**Priority:** Must  
**Modules:** B (Soundscape mixer), I (Render/export pipeline)  
**Phase(s):** Phase 3  
**Verification:** AT-003, IT-002

**Description**  
Mixer must be able to bounce a project to a single WAV deterministically and produce seamless loops where configured.

**Rationale**  
Export pipeline depends on a single authoritative audio track and reliable looping.

**Acceptance criteria**  
- Given same inputs + automation, bounced WAV hash is identical across runs on the same toolchain.
- Loop boundaries produce no audible click; waveform diff at boundary is below threshold.

### RQ-019 — Batch generation can generate N variations overnight

**Priority:** Should  
**Modules:** N (Batch generator), I (Render/export pipeline), K (Templates & presets (metadata + render))  
**Phase(s):** Phase 4  
**Verification:** AT-004

**Description**  
Provide batch generation that can plan and execute many renders unattended (overnight), with recoverable failures.

**Rationale**  
Supports scalable production workflows while keeping guardrails.

**Acceptance criteria**  
- Batch planner can schedule 100 jobs with priority and time windows.
- Batch execution persists state and resumes after restart.

### RQ-020 — Remix engine can swap audio, vary length, grade visuals

**Priority:** Should  
**Modules:** R (Remix engine), A (Audio import + analysis), B (Soundscape mixer), C (Visual engine foundation), H (Mapping + presets), I (Render/export pipeline)  
**Phase(s):** Phase 4  
**Verification:** AT-004, TS-007

**Description**  
Provide remix engine capable of controlled variations: audio swaps, length variants, grading variants, thumbnail variants.

**Rationale**  
Enables variation without ad-hoc scripting and supports batch workflows.

**Acceptance criteria**  
- Remix rules are declarative and stored with provenance.
- Length variants respect loop period rules; no arbitrary truncation without fade.

### RQ-021 — Batch guardrails prevent low-variation template spam

**Priority:** Must  
**Modules:** N (Batch generator), R (Remix engine), K (Templates & presets (metadata + render))  
**Phase(s):** Phase 4  
**Verification:** TS-007, AT-004

**Description**  
Batch/remix must include guardrails enforcing minimum meaningful difference (variant distance) between outputs.

**Rationale**  
YouTube monetization risk for inauthentic/mass-produced content must be treated as a constraint.

**Acceptance criteria**  
- Variant distance metric must pass configured thresholds before enqueueing.
- System can generate a reviewer report listing differences per variant.

### RQ-022 — OAuth installed-app authorization via system browser

**Priority:** Must  
**Modules:** L (YouTube integration)  
**Phase(s):** Phase 5  
**Verification:** AT-005, IT-004

**Description**  
YouTube authorization must use OAuth for installed apps via system browser + local loopback redirect (no embedded webviews).

**Rationale**  
Google disallows embedded user agents; using system browser avoids disallowed_useragent failures.

**Acceptance criteria**  
- Auth flow opens system browser and completes using a loopback redirect to localhost.
- PKCE is used; refresh token is stored in OS secure storage.

### RQ-023 — Resumable uploads for large files

**Priority:** Must  
**Modules:** L (YouTube integration)  
**Phase(s):** Phase 5  
**Verification:** AT-005, IT-006

**Description**  
Use the YouTube resumable upload protocol for reliable uploads of large MP4 files.

**Rationale**  
Large exports require resilient, restartable upload behavior.

**Acceptance criteria**  
- Upload supports pausing/resuming after network interruption without restarting from byte 0.
- Progress is reported in bytes uploaded and percent.

### RQ-024 — Upload video with metadata (title/desc/tags/category/privacy)

**Priority:** Must  
**Modules:** L (YouTube integration)  
**Phase(s):** Phase 5  
**Verification:** AT-005

**Description**  
Publish pipeline uploads a video with metadata from metadata.json (title, description, tags, category, privacy).

**Rationale**  
Ensures offline bundle metadata is actually applied during upload.

**Acceptance criteria**  
- videos.insert request includes metadata fields and results in correct video properties.
- If API call fails, error is reported with actionable remediation and job can retry.

### RQ-025 — Upload custom thumbnail

**Priority:** Should  
**Modules:** L (YouTube integration)  
**Phase(s):** Phase 5  
**Verification:** AT-005

**Description**  
Publish pipeline uploads the thumbnail.png as the YouTube custom thumbnail (within size constraints).

**Rationale**  
Thumbnails are a key growth lever; pipeline must support them.

**Acceptance criteria**  
- thumbnails.set succeeds for compliant thumbnail.png files.
- If thumbnail exceeds size, app offers automatic downscale/re-encode to comply.

### RQ-026 — Schedule publish time

**Priority:** Should  
**Modules:** L (YouTube integration)  
**Phase(s):** Phase 5  
**Verification:** AT-005, TS-004

**Description**  
Support scheduling publish time using publishAt (private only; never published before).

**Rationale**  
Scheduling is part of professional publishing workflows.

**Acceptance criteria**  
- Scheduled publish time is applied and verified via subsequent API readback.
- UI prevents invalid scheduling states (e.g., scheduling public videos).

### RQ-027 — Add to playlists / manage playlists

**Priority:** Could  
**Modules:** L (YouTube integration)  
**Phase(s):** Phase 5  
**Verification:** AT-005

**Description**  
Support creating playlists and adding uploaded videos to playlists.

**Rationale**  
Useful for series organization and discovery.

**Acceptance criteria**  
- User can create a playlist and add the uploaded video to it via API calls.

### RQ-028 — Multi-channel profiles with explicit channel binding

**Priority:** Must  
**Modules:** M (Multi-channel management), L (YouTube integration), K (Templates & presets (metadata + render))  
**Phase(s):** Phase 5  
**Verification:** AT-005

**Description**  
Support multiple channel profiles with explicit binding and safeguards to prevent uploads to the wrong channel.

**Rationale**  
Wrong-channel uploads are operationally costly and can damage channels.

**Acceptance criteria**  
- Each publish job is bound to a specific channel profile and requires explicit confirmation when switching.
- App displays channel identity (name + channelId) prominently before upload.

### RQ-029 — Local analytics dashboard with official APIs only

**Priority:** Should  
**Modules:** P (Analytics dashboard)  
**Phase(s):** Phase 6  
**Verification:** AT-006

**Description**  
Provide a local analytics dashboard that uses official YouTube Analytics/Reporting APIs only (no scraping).

**Rationale**  
Avoid policy risk and fragility; keep local-first storage for responsiveness.

**Acceptance criteria**  
- Dashboard loads from local SQLite without network and shows last-synced timestamps.
- No creator studio scraping code exists; only official API clients are used.

### RQ-030 — Bulk analytics ingestion for historical storage

**Priority:** Could  
**Modules:** P (Analytics dashboard)  
**Phase(s):** Phase 6  
**Verification:** AT-006, IT-007

**Description**  
Support bulk analytics ingestion via Reporting API CSV reports for historical storage.

**Rationale**  
Enables backfills and long-term analysis.

**Acceptance criteria**  
- System can import 90 days of data and store locally without corruption.
- Incremental sync updates only new periods and avoids duplicates.

### RQ-031 — Revenue tracking with graceful data-unavailable UX

**Priority:** Could  
**Modules:** Q (Revenue tracking)  
**Phase(s):** Phase 6  
**Verification:** AT-006

**Description**  
Provide revenue tracking where available and a clearly labeled manual import fallback when not available.

**Rationale**  
Revenue access is account-dependent; the system must degrade gracefully.

**Acceptance criteria**  
- If revenue metrics unavailable, UI shows 'Not available' with explanation and offers manual CSV import.
- Imported data is stored locally and can be edited/removed by the user.

### RQ-032 — Niche analyzer is quota-aware and supports manual workflows

**Priority:** Could  
**Modules:** O (Niche analyzer)  
**Phase(s):** Phase 6  
**Verification:** AT-006, TS-010

**Description**  
Provide niche analyzer tooling (keyword notebook, competitor notes) that is quota-aware and works even without API access.

**Rationale**  
Reduces quota burn and supports ethical, policy-safe research workflows.

**Acceptance criteria**  
- User can track keywords and notes without any API calls.
- If search/list APIs are used, quota cost is surfaced and operations are budgeted.

### RQ-033 — Export bundles record pinned toolchain versions and schema versions

**Priority:** Must  
**Modules:** I (Render/export pipeline), C (Visual engine foundation), A (Audio import + analysis), H (Mapping + presets), K (Templates & presets (metadata + render))  
**Phase(s):** Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, Phase 6  
**Verification:** TS-005, AT-001

**Description**  
Every export bundle must include build_manifest.json capturing exact versions/hashes for: Godot, render graph hash, FFmpeg (version + license mode), analysis worker/version, mapping/preset schema versions, and export preset IDs.

**Rationale**  
Prevents drift and supports deterministic rerenderability and auditability.

**Acceptance criteria**  
- build_manifest.json includes all required version fields and is generated for every export.
- build_manifest.json includes a reproducibility section: input asset hashes, preset IDs, seed, fps, resolution, segment plan.

### RQ-034 — Managed FFmpeg strategy with checksum verification and license mode tracking

**Priority:** Must  
**Modules:** I (Render/export pipeline)  
**Phase(s):** Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, Phase 6  
**Verification:** IT-002, TS-005, AT-001

**Description**  
The app uses a managed FFmpeg installation: a pinned version is downloaded/located, checksum-verified, and its license mode (LGPL/GPL) is recorded and surfaced to the user.

**Rationale**  
FFmpeg is the 'truth pipeline' for export; version and licensing must be explicit and reproducible.

**Acceptance criteria**  
- On startup, the app verifies FFmpeg presence and version meets pinned requirements (or user overrides with warning).
- If managed download is used, binary checksum is verified before execution.
- License mode is displayed in Settings and recorded in build_manifest.json.

### RQ-035 — Determinism harness with checkpoint frame hashing

**Priority:** Must  
**Modules:** C (Visual engine foundation), I (Render/export pipeline), H (Mapping + presets)  
**Phase(s):** Phase 1, Phase 2, Phase 3, Phase 4  
**Verification:** TS-005, AT-001, AT-002

**Description**  
Provide a determinism verification harness that records and compares checkpoint frame hashes for golden projects.

**Rationale**  
Determinism is a Phase 1 go/no-go criterion and must be continuously verified.

**Acceptance criteria**  
- Golden projects define checkpoint frames (e.g., 0/900/1800) and expected hashes for a pinned environment.
- Running determinism test twice on the same machine yields identical checkpoint hashes.
- If determinism breaks, the test output pinpoints the first divergent checkpoint.

### RQ-036 — Job queue persistence, crash recovery, and resume semantics

**Priority:** Must  
**Modules:** I (Render/export pipeline), A (Audio import + analysis), L (YouTube integration), P (Analytics dashboard), N (Batch generator), R (Remix engine)  
**Phase(s):** Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, Phase 6  
**Verification:** TS-004, AT-001

**Description**  
All long-running operations (analysis, render, encode, concat, upload, analytics sync) are modeled as jobs persisted in SQLite with crash recovery and resume semantics.

**Rationale**  
Long tasks are the norm; reliability requires a persistent job system.

**Acceptance criteria**  
- Jobs survive app restarts; completed work is reused where safe (e.g., segment encodes, upload sessions).
- Each job has a deterministic state machine; invalid transitions are rejected.

### RQ-037 — Workspace isolation and cleanup policy for renders/exports

**Priority:** Must  
**Modules:** I (Render/export pipeline), J (Asset library manager)  
**Phase(s):** Phase 1, Phase 2, Phase 3, Phase 4  
**Verification:** IT-003, AT-001

**Description**  
Export pipeline uses per-job workspace directories; temporary artifacts are cleaned deterministically and never corrupt final outputs.

**Rationale**  
Prevents disk blow-ups and ensures cancel/resume safety.

**Acceptance criteria**  
- Workspaces live under a predictable tmp directory and are keyed by job_id.
- Final artifacts are written via atomic rename only after successful completion.
- Cleanup rules are configurable; default retains last N bundles and prunes temp frames immediately after segment encode.

### RQ-038 — Secure storage adapter using OS keychain/secure storage (no plaintext tokens)

**Priority:** Must  
**Modules:** L (YouTube integration), M (Multi-channel management)  
**Phase(s):** Phase 5, Phase 6  
**Verification:** IT-004, AT-005

**Description**  
OAuth refresh tokens and any long-lived secrets are stored only via OS secure storage (Keychain on macOS) using a Rust keyring helper. No plaintext tokens are stored in SQLite or on disk.

**Rationale**  
Security non-negotiable from Decision Pack.

**Acceptance criteria**  
- No token fields exist in SQLite schema; only references/identifiers.
- Keyring helper stores and retrieves secrets; secrets are never logged.
- Unlink action deletes secrets from secure storage and invalidates local references.

### RQ-039 — Privacy-first logging and diagnostics with redaction

**Priority:** Must  
**Modules:** C (Visual engine foundation), I (Render/export pipeline), L (YouTube integration), P (Analytics dashboard)  
**Phase(s):** Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, Phase 6  
**Verification:** TS-004, AT-001, AT-005

**Description**  
Logging must redact tokens/PII and provide a safe diagnostics export bundle without secrets.

**Rationale**  
Prevents accidental leakage and improves supportability.

**Acceptance criteria**  
- Logs never include OAuth tokens, authorization codes, or raw HTTP headers.
- Diagnostics export includes sanitized logs, job summaries, and environment versions, but excludes assets and secrets by default.

### RQ-040 — SQLite schema migrations with forward-only versioning

**Priority:** Must  
**Modules:** J (Asset library manager)  
**Phase(s):** Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, Phase 6  
**Verification:** TS-008, AT-001

**Description**  
The application maintains a migration system to evolve SQLite schema while preserving existing user data.

**Rationale**  
Local-first persistent state must be upgrade-safe across versions.

**Acceptance criteria**  
- On startup, migrations apply automatically and are recorded in schema_migrations table.
- Downgrades are not supported; app refuses to open DB from a newer schema version.

### RQ-041 — Immutable export snapshots for rerenderability

**Priority:** Must  
**Modules:** I (Render/export pipeline), J (Asset library manager), H (Mapping + presets), K (Templates & presets (metadata + render))  
**Phase(s):** Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, Phase 6  
**Verification:** IT-003, AT-001

**Description**  
Each export captures an immutable snapshot of all inputs needed to reproduce the output (asset hashes, template/preset IDs, mapping versions, seeds, durations, export preset).

**Rationale**  
Supports deterministic rerenderability and audit trails.

**Acceptance criteria**  
- build_manifest.json (or a referenced snapshot file) contains the complete snapshot.
- Rerender command can reproduce checkpoint frame hashes when run against the snapshot.

### RQ-042 — Template variable engine for metadata and on-canvas typography

**Priority:** Should  
**Modules:** K (Templates & presets (metadata + render)), G (Motion poster mode), C (Visual engine foundation)  
**Phase(s):** Phase 1, Phase 4, Phase 5  
**Verification:** IT-005, AT-001

**Description**  
Templates support a variable system used for metadata.json generation and for optional on-canvas text fields (title/artist/etc.) in modes like Motion Poster.

**Rationale**  
Ensures consistency between metadata and visuals and enables multi-channel automation.

**Acceptance criteria**  
- Variables can reference project fields (title, artist), audio analysis (bpm), and export fields (duration).
- Rendering a template is deterministic and produces a resolved metadata.json.

### RQ-043 — Deterministic, YouTube-valid thumbnail generation

**Priority:** Should  
**Modules:** I (Render/export pipeline), C (Visual engine foundation)  
**Phase(s):** Phase 1, Phase 2, Phase 3, Phase 4, Phase 5  
**Verification:** TS-005, AT-001

**Description**  
Generate thumbnail.png locally in a YouTube-compliant format and size constraints, deterministically from the render context.

**Rationale**  
Thumbnails are required for publishing and must be reproducible.

**Acceptance criteria**  
- Default thumbnail is 1280x720 PNG and <= 2MB; if larger, it is re-encoded to comply.
- Thumbnail generation is deterministic for a given snapshot/seed and records the chosen frame/time in build_manifest.json.

### RQ-044 — Production export gating enforces audio license provenance completeness

**Priority:** Must  
**Modules:** J (Asset library manager), I (Render/export pipeline)  
**Phase(s):** Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, Phase 6  
**Verification:** TS-006, AT-001

**Description**  
The app must prevent 'production export' when audio assets have unknown source provenance; users can still do 'draft exports' for internal review.

**Rationale**  
Decision Pack success metrics require no unknown-source audio in production exports.

**Acceptance criteria**  
- Production export requires source_type, license_name or license_url, and attribution/proof where applicable.
- If requirements missing, UI explains what fields are required and links to the asset record.
- provenance.json includes structured provenance and a copy-paste attribution block.

### RQ-045 — Originality ledger per export (anti-template-spam support)

**Priority:** Should  
**Modules:** K (Templates & presets (metadata + render)), R (Remix engine), N (Batch generator), I (Render/export pipeline)  
**Phase(s):** Phase 1, Phase 4  
**Verification:** AT-001, AT-004

**Description**  
Each export bundle includes an originality ledger summarizing what makes this output distinct (assets, preset deltas, seed, manual edits).

**Rationale**  
Supports creator self-audits and helps mitigate inauthentic content risk.

**Acceptance criteria**  
- Ledger lists: base template/preset, changed parameters, seed, and unique assets used.
- Ledger is included in provenance.json or a referenced file and is human-readable.

### RQ-046 — Unified progress reporting using FFmpeg -progress and render progress events

**Priority:** Must  
**Modules:** I (Render/export pipeline)  
**Phase(s):** Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, Phase 6  
**Verification:** IT-002, AT-001

**Description**  
All pipeline stages report machine-readable progress, unified into a single job progress model in UI and logs.

**Rationale**  
Reliable UX and automation require consistent progress semantics.

**Acceptance criteria**  
- FFmpeg progress is parsed using -progress pipe:1 key=value output.
- Progress model supports: percent, ETA, current_stage, and stage-specific metrics (frames, bytes).

### RQ-047 — ML model download manager with provenance and version pinning

**Priority:** Could  
**Modules:** E (Photo animator), J (Asset library manager)  
**Phase(s):** Phase 2  
**Verification:** AT-002

**Description**  
Optional ML models (Phase 2) are not bundled by default; users explicitly download them. The app records model provenance (source URL, license, checksum, version).

**Rationale**  
Controls app size and licensing risk while enabling advanced features for opt-in users.

**Acceptance criteria**  
- Models are stored outside the core app bundle in a managed models directory.
- Downloads are checksum-verified and versioned; provenance is recorded in SQLite.

### RQ-048 — Multi-process architecture keeps editor responsive during heavy work

**Priority:** Must  
**Modules:** A (Audio import + analysis), I (Render/export pipeline), L (YouTube integration)  
**Phase(s):** Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, Phase 6  
**Verification:** IT-001, IT-003, AT-001

**Description**  
Audio analysis, offline rendering, encoding, and network uploads run in separate worker processes and communicate via explicit IPC contracts.

**Rationale**  
Responsiveness and reliability require isolating heavy/fragile operations.

**Acceptance criteria**  
- Starting an analysis or export job does not freeze the editor UI for more than 100ms.
- IPC messages are JSON (newline-delimited) and only exchange file paths and structured data (no raw media bytes).

### RQ-049 — Configuration, profiles, and data directory conventions are explicit and portable

**Priority:** Should  
**Modules:** J (Asset library manager), I (Render/export pipeline)  
**Phase(s):** Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, Phase 6  
**Verification:** TS-004, AT-001

**Description**  
Define explicit on-disk layout for app data (DB, library, tmp, exports, logs) and provide settings for relocating library/exports directories.

**Rationale**  
Reduces surprises, supports backups, and helps manage disk usage.

**Acceptance criteria**  
- App uses OS-appropriate user data directory by default and documents it.
- User can relocate asset library and exports directory via Settings; paths persist and are validated on startup.

### RQ-050 — Export presets are versioned; determinism boundaries are documented and enforced

**Priority:** Must  
**Modules:** I (Render/export pipeline), K (Templates & presets (metadata + render)), C (Visual engine foundation)  
**Phase(s):** Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, Phase 6  
**Verification:** TS-005, AT-001

**Description**  
Export presets (resolution, fps, encoder, bitrate/quality) are versioned and recorded. Determinism boundaries (GPU/encoder variability) are explicitly documented and surfaced.

**Rationale**  
Avoids 'works on my machine' drift and sets correct expectations about determinism scope.

**Acceptance criteria**  
- Preset schema includes a version field; changes create new preset versions rather than mutating old ones.
- UI surfaces when hardware encoders may make MP4 bytes non-deterministic, while checkpoint frame hashes remain deterministic.

### RQ-051 — Quota budgeting and quota-aware scheduling for YouTube operations

**Priority:** Should  
**Modules:** L (YouTube integration), N (Batch generator), M (Multi-channel management)  
**Phase(s):** Phase 5, Phase 6  
**Verification:** TS-010, AT-005

**Description**  
YouTube operations are quota-budgeted; the app estimates quota costs for planned operations and throttles/schedules to stay within daily limits.

**Rationale**  
Quota limits and compliance audits are operational constraints; ignoring them causes outages.

**Acceptance criteria**  
- Before executing a publish batch, the app shows estimated quota units and warns if over budget.
- Upload/publish operations can be scheduled or paused automatically when budget exhausted.

### RQ-052 — Audit readiness checklist and manual-publish fallback artifacts

**Priority:** Should  
**Modules:** L (YouTube integration), K (Templates & presets (metadata + render)), J (Asset library manager)  
**Phase(s):** Phase 5  
**Verification:** AT-005

**Description**  
The app provides an audit readiness checklist and supports a manual publish fallback using the exported bundle (metadata + provenance + thumbnail).

**Rationale**  
Uploads from unverified API projects may be restricted; the product must remain usable with manual workflows.

**Acceptance criteria**  
- Audit checklist is accessible in-app and exportable as a report.
- Manual publish mode generates copy/paste-ready description including attribution/provenance block.

### RQ-053 — Disk usage management and cache pruning

**Priority:** Should  
**Modules:** J (Asset library manager), I (Render/export pipeline), A (Audio import + analysis)  
**Phase(s):** Phase 1, Phase 2, Phase 3, Phase 4, Phase 6  
**Verification:** AT-001, AT-006

**Description**  
The app tracks disk usage for assets, analysis caches, render workspaces, and exports; users can prune safely.

**Rationale**  
Long renders and caches can consume significant disk; must be managed proactively.

**Acceptance criteria**  
- Settings page shows sizes per category and last-used times.
- Prune operations never delete referenced assets without confirmation; temp workspaces can be cleaned safely.

### RQ-054 — Backup/restore for local database and managed library

**Priority:** Could  
**Modules:** J (Asset library manager)  
**Phase(s):** Phase 6  
**Verification:** AT-006

**Description**  
Provide a supported backup/restore mechanism for the SQLite DB and managed asset library, preserving IDs and relationships.

**Rationale**  
Local-first tools need reliable backups for creator workflows.

**Acceptance criteria**  
- Backup creates a single archive containing DB + necessary library metadata (and optionally asset files).
- Restore can load backup into a clean environment and open projects successfully.

### RQ-055 — Asset integrity verification and relink workflow

**Priority:** Should  
**Modules:** J (Asset library manager)  
**Phase(s):** Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, Phase 6  
**Verification:** TS-001, AT-001

**Description**  
Provide tools to verify integrity of managed assets and relink or repair missing external paths where applicable.

**Rationale**  
Protects projects from broken links and silent corruption.

**Acceptance criteria**  
- Integrity check reports missing/changed files and can re-verify hashes.
- Relink workflow allows user to point to a new file and updates references safely.

