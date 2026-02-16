# Phase 1 — Local-only Production Bundle (GO/NO-GO)

## Objectives
- Deliver a **local-only end-to-end workflow** that produces a **production bundle** reliably.
- Prove the hardest engineering constraints early:
  - deterministic offline rendering (checkpoint hashes)
  - segment-based resume + crash-safe cleanup
  - provenance enforcement for audio assets

This phase is the **project go/no-go gate**.

## Included modules / features
- **A** Audio import + analysis (baseline: BPM + beat grid; cached)
- **C** Visual engine foundation (preview + offline parity)
- **G** Motion Poster mode v1 (production-grade)
- **H** Mapping + presets v1 (stable parameter IDs)
- **I** Render/export pipeline v1 (segment render → encode → bundle)
- **J** Asset library manager v1 (license provenance enforced)
- **K** Templates v1 (metadata + render preset defaults)

## Deliverables (testable)

### D1 — Audio import + canonical WAV cache (RQ-002)
- Import audio (MP3/WAV/FLAC/M4A/AIFF).
- Decode to canonical WAV:
  - 48kHz, stereo, PCM s16le.
- Dedupe based on SHA-256.

### D2 — Audio analysis worker + cache (RQ-003)
- Python worker process (librosa).
- Outputs:
  - BPM
  - beat timestamps
- Cached in SQLite keyed by `(audio_sha256, analysis_version)`.
- UI shows analysis status and results.

### D3 — Asset library v1 + provenance enforcement (RQ-011, RQ-044)
- Asset import for audio + images + fonts.
- License fields for audio are required for **production export**.
- Provide draft export mode if provenance incomplete.

### D4 — Mapping/presets v1 (RQ-005)
- Parameter registry for Motion Poster parameters with stable IDs.
- Mapping evaluator deterministic for `(analysis, t, seed)`.
- Preset schema v1 stored in SQLite.

### D5 — Motion Poster mode v1 (RQ-004)
- Album art + typography + subtle motion.
- Beat-reactive parameters via mapping.
- **At least 6 presets** that are visually distinct.

### D6 — Export pipeline v1 (RQ-007..RQ-010, RQ-008)
- Persistent job queue with:
  - progress
  - cancel
  - resume
  - crash recovery
- Segment-based export:
  - render segment frames via MovieWriter
  - encode segment MP4 via FFmpeg with `-progress`
  - concat via concat demuxer
- Bundle output:
  - `video.mp4`
  - `thumbnail.png` (YouTube-valid)
  - `metadata.json`
  - `provenance.json`
  - `build_manifest.json`

### D7 — Determinism harness + golden projects (RQ-035)
- Golden projects with checkpoint frame hashing at fixed frames.
- Tools/scripts to run determinism checks locally.

## Acceptance criteria (measurable)

### A1 — Export correctness
- Exports succeed at **1080p30** for:
  - 10 seconds
  - 10 minutes
  - 2 hours
- Produced bundle has the exact required files and names.

### A2 — Sync accuracy
- Audio/video sync drift **< 1 frame at end**.
- Validate using beat marker overlay in a test scene or equivalent method.

### A3 — Cancel/resume safety
- Cancel mid-export:
  - leaves no corrupted final `video.mp4`
  - leaves completed segments intact
- Resume:
  - restarts from the last completed segment
  - does not redo completed segment encodes

### A4 — Determinism
- Same inputs + preset seed → identical checkpoint frame hashes at defined checkpoints (e.g., 0/900/1800).
- Determinism verified on the same machine and pinned toolchain.

### A5 — Provenance enforcement
- Production export is blocked if audio provenance is incomplete or source_type is unknown.
- Draft export remains available.

## Verification plan

### Automated
- Unit:
  - TS-001, TS-002, TS-003, TS-004, TS-005, TS-006, TS-008
- Integration:
  - IT-001 (worker IPC + cache)
  - IT-002 (FFmpeg progress + cancel)
  - IT-003 (segment render/encode/concat + resume)
- Acceptance:
  - **AT-001** (must pass)

### Manual runbook checks
- Kill the app mid-segment and verify resume.
- Simulate disk-full (small disk quota) and ensure safe failure + cleanup.
- Validate bundle manual upload readiness (metadata/provenance copy/paste).

## Dependencies / prerequisites
- FFmpeg managed install strategy + license mode tracking (RQ-034).
- SQLite schema v1 locked and migration runner implemented (RQ-040).
- Toolchain version recording in build_manifest (RQ-033).

## Risks + mitigation tasks
- Disk blow-up from PNG frames:
  - implement segment cleanup immediately after encode
  - add disk guard to pause exports when low
- “Template spam” risk:
  - enforce preset diversity checklist
  - include seed-driven controlled variation within a preset family
- Determinism drift:
  - pin toolchain versions and record them
  - add regression suite for checkpoint hashes

## Explicit out-of-scope (deferred)
- D particles, E photo animator, F landscape (Phase 2)
- B mixer (Phase 3)
- N batch generator, R remix (Phase 4)
- L/M YouTube publishing (Phase 5)
- O/P/Q analytics/research/revenue (Phase 6)
