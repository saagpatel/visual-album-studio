# System Architecture

This document describes the full-system architecture of Visual Album Studio (VAS), including module boundaries, data flow, and reliability/security constraints.

## Architecture goals
- Local-first: core workflows do not require network.
- Deterministic offline rendering and resumable export.
- Clean separation of concerns (UI vs Core vs Adapters).
- Content safety and provenance as first-class data.
- Secure token storage (OS keychain) for YouTube.

## Component diagram (logical)

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Godot App (UI + Preview)                             │
│                                                                              │
│  UI Layer (scenes)                  Core Services (domain logic)             │
│  - Asset Browser                    - AssetService (J)                       │
│  - Project Editor                   - ProjectService                         │
│  - Presets/Templates UI             - MappingService (H)                      │
│  - Export Queue UI                  - RenderService (C/I)                    │
│  - (Phase 3) Mixer UI               - ExportService (I)                      │
│  - (Phase 5) Publish UI             - PublishService (L/M)                   │
│  - (Phase 6) Analytics UI           - AnalyticsService (P/Q/O)               │
│                                                                              │
│  Visual Modes (render graph)         JobQueueService (persistent)            │
│  - Motion Poster (G)                 - Jobs + progress + cancel/resume        │
│  - Particles (D)                     - Crash recovery                         │
│  - Landscape (F)                                                             │
│  - Photo Animator (E)                                                        │
│                                                                              │
│  Adapters (side effects)                                                   │
│  - SQLiteAdapter (godot-sqlite)                                             │
│  - FileSystemAdapter                                                        │
│  - FFmpegAdapter (process + -progress parse)                                │
│  - PythonWorkerAdapter (IPC)                                                │
│  - KeyringAdapter (Rust helper)                                             │
│  - (Phase 5+) YouTubeApiAdapter (HTTP)                                      │
└──────────────────────────────────────────────────────────────────────────────┘

External local processes:
  ┌───────────────────────────────┐        ┌─────────────────────────────────┐
  │ Python Analysis Worker (A)     │        │ FFmpeg Sidecar (I/B)            │
  │ librosa + numpy/scipy          │        │ encode/mux/concat/thumbnail     │
  │ IPC: JSON lines + file paths   │        │ progress: -progress pipe:1      │
  └───────────────────────────────┘        └─────────────────────────────────┘

Optional network boundary (Phase 5+):
  ┌───────────────────────────────┐
  │ YouTube APIs (Data/Analytics)  │
  │ OAuth installed app flow       │
  └───────────────────────────────┘
```

## Data flow (end-to-end)

### Import → analyze (Phase 1)
1. UI requests import of an audio file.
2. AssetService:
   - computes SHA-256
   - stores a managed copy in the library (hash-addressed)
   - decodes to canonical WAV (via FFmpegAdapter)
   - writes asset record to SQLite
3. AnalysisService enqueues an AnalysisJob:
   - PythonWorkerAdapter runs librosa analysis over canonical WAV
   - results are cached in SQLite keyed by (audio_sha256, analysis_version)
4. UI subscribes to job progress and shows BPM/beat grid.

### Preview (Phase 1+)
1. UI plays audio (preview clock).
2. MappingService computes parameter values at time `t` based on cached audio features.
3. Visual mode scene reads parameter values and renders frame on GPU.

### Offline export (Phase 1 gate)
1. ExportService creates a RenderJob snapshot and a segment plan.
2. For each segment:
   - Renderer runs deterministic fixed-FPS stepping (time = frame_index / fps).
   - Godot MovieWriter writes PNG frames (and optional WAV) for the segment.
   - FFmpegAdapter encodes segment video and muxes audio.
   - Segment frames are deleted per cleanup policy.
3. After all segments:
   - FFmpegAdapter concatenates segments using concat demuxer.
   - Thumbnail is generated deterministically.
   - Bundle files are written atomically into the bundle directory.

### Optional publish (Phase 5)
1. User connects YouTube via system browser OAuth loopback redirect.
2. Tokens stored in OS secure storage (KeyringAdapter).
3. PublishService enqueues UploadJob:
   - uses resumable upload protocol
   - applies metadata and thumbnail
   - schedules publish where configured
   - quota-aware behavior and retry/backoff

## Preview vs offline parity (non-negotiable)
- **Single render graph**: same mapping functions, same parameter registry, same scene graph logic.
- **Seeded RNG**:
  - All randomness must be derived from a recorded seed.
  - Never use wall-clock time as a source of randomness in render logic.
- **Timebase**:
  - Preview: audio-clocked time `t`.
  - Offline: frame-stepped time `t = frame_index / fps` with fixed delta.

Determinism boundaries (explicit):
- **Guaranteed deterministic**: checkpoint frame hashes from Godot render output on the same machine + pinned toolchain.
- **Not guaranteed deterministic**: MP4 byte-identical output across machines/hardware encoders.

## Persistence model
- SQLite is the single persistent store for:
  - assets, projects, presets/templates, analysis summaries, jobs, exports
  - channel profiles and analytics snapshots (Phase 5/6)
- Secrets (OAuth tokens) are stored only in OS secure storage; DB stores only references.

## Error taxonomy (codes + recovery)

### Category: User/data errors (non-retryable until fixed)
- `E_ASSET_MISSING` — file missing or moved
- `E_LICENSE_INCOMPLETE` — production export blocked by missing provenance fields
- `E_TEMPLATE_INVALID` — template fails validation

Recovery: prompt user with actionable UI to fix; job remains blocked.

### Category: Tool/process errors (retryable depending on cause)
- `E_FFMPEG_NOT_FOUND` — FFmpeg missing
- `E_FFMPEG_FAILED` — non-zero exit code; capture stderr and command
- `E_RENDERER_CRASHED` — headless render process crashed
- `E_DISK_FULL` — insufficient disk for segment

Recovery:
- Provide retry after remediation.
- Resume from last completed segment when safe.
- Never finalize partial bundles.

### Category: Transient network errors (Phase 5+)
- `E_NET_TIMEOUT`, `E_NET_DNS`, `E_HTTP_5XX`
- `E_YT_QUOTA_EXCEEDED`
- `E_OAUTH_REVOKED`

Recovery:
- Exponential backoff for transient errors.
- Quota-aware scheduling and pause.
- Re-auth flow for revoked tokens.

### Category: Determinism violations (stop-the-line for Phase 1)
- `E_DETERMINISM_MISMATCH` — checkpoint hash mismatch on rerun

Recovery:
- Fail AT-001/AT-002.
- Capture the earliest divergence checkpoint and environment info in diagnostics.
