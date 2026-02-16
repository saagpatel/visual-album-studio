# Phase 3 — Soundscape Mixer + Deterministic Offline Bounce

## Objectives
- Ship the soundscape mixer so creators can build more original audio arrangements.
- Produce a **single authoritative bounced WAV** for export, deterministically, with loop-perfect output.

## Included modules / features
- **B** Mixer (multi-track timeline + automation)
- **A** Analysis enhancements (onset/energy/spectral features)
- **I** Export pipeline audio integration improvements
- **J** License management extensions (audio provenance in multi-track projects)

## Deliverables (testable)

### D1 — Mixer UI + persistence (RQ-017)
Minimum capabilities:
- 20 tracks (stress case)
- per-track:
  - volume (dB)
  - pan
  - start offset
  - loop region
  - fade in/out
- project-level master gain + optional limiter preset (off by default)

### D2 — Offline bounce to WAV via FFmpeg filtergraph (RQ-018)
- Generate bounced WAV with:
  - deterministic ordering
  - stable filtergraph generation
  - recorded manifest (inputs, params, FFmpeg version)
- Bounced WAV stored as an asset with SHA-256.

### D3 — Loop-perfect output
- Seamless loop where configured:
  - no audible click
  - optional crossfade strategy when exact loops not possible

### D4 — Export pipeline uses bounced WAV as the single authoritative audio track
- Render segments use the bounced WAV (not raw source audio).
- A/V sync validated against beat markers.

## Acceptance criteria (measurable)

### A1 — Deterministic bounce
- Same inputs + automation → identical bounced WAV hash on the same machine/pinned FFmpeg build.

### A2 — Loop-safe boundary
- Loop boundary has no audible click.
- Sample-level boundary diff check passes under defined threshold.

### A3 — Loudness/clipping safety
- Default output does not clip.
- If limiter is enabled, limiter parameters are recorded in build_manifest/provenance.

### A4 — Export integration
- MP4 export uses the bounced WAV and remains in sync (drift < 1 frame at end) for golden projects.

## Verification plan

### Automated
- Unit:
  - TS-004 (job state), TS-005 (manifest), TS-006 (provenance) continue
- Integration:
  - IT-002 (FFmpeg) extended for filtergraph bounce
- Acceptance:
  - **AT-003**

### Manual checks
- Listen test on loop boundaries for representative tracks.
- Stress mix: 20-track project exported at 10min and validated.

## Dependencies / prerequisites
- Phase 1 export pipeline and segmentation framework.
- Phase 2 mapping/preset system (for beat-aligned loops, optional).

## Risks + mitigation tasks
- FFmpeg licensing complexity:
  - keep default LGPL-safe build baseline
  - optional GPL encoder pack remains opt-in
- Deterministic bounce across platforms:
  - define determinism boundary as “same machine + pinned FFmpeg build”
- User expectations of DAW-like features:
  - keep scope minimal; defer advanced automation lanes if needed

## Explicit out-of-scope (deferred)
- N/R automation (Phase 4)
- L/M YouTube (Phase 5)
- O/P/Q analytics/research/revenue (Phase 6)
