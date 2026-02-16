# Product Requirements Document (PRD)

## Product name
**Visual Album Studio (VAS)**

## Summary
VAS is a local-first desktop editor for creating looping, music-synced videos (10 seconds to 2+ hours) with a deterministic, resumable export pipeline. The product optionally supports YouTube publishing later, while treating copyright/Content ID and monetization policy risks as first-class design constraints.

## Goals

### Primary goals
- Enable creators to generate high-quality visual album videos locally with:
  - Real-time preview
  - Deterministic offline rendering
  - Reliable long-duration exports with cancel/resume
- Produce a complete **production bundle** suitable for manual upload or automated publishing:
  - `video.mp4`
  - `thumbnail.png`
  - `metadata.json`
  - `provenance.json`
  - `build_manifest.json`

### Secondary goals
- Expand visual variety (particles, landscapes, photo animation) without sacrificing export determinism.
- Support multi-track soundscapes with deterministic offline bounce.
- Support automation (batch/remix) with guardrails that reduce “inauthentic content” risk.
- Add optional YouTube publishing with quota-aware, audit-ready behavior.
- Close the loop with local analytics and revenue tracking using official APIs only.

## Non-goals (explicit)
- No cloud rendering, cloud project storage, or background SaaS dependency.
- No scraping of YouTube Studio or any non-official YouTube endpoints.
- No “one-click monetization guarantee.” The product mitigates risk but does not promise outcomes.

## Success metrics (authoritative)
- **Export reliability:** 50 consecutive renders without manual intervention; deterministic rerender hash match for at least 10 test projects.
- **Content safety:** every exported bundle includes machine-readable license provenance metadata for audio assets; no “unknown source” audio allowed in production exports.
- **YouTube (later):** N successful resumable uploads with correct scheduled publish times and thumbnails, staying within daily quota.

## Target users
- **Beginner creator:** wants a guided path to create a single video reliably.
- **Power workflow creator:** wants presets, batch generation, and consistent series branding across channels.
- **Operations-minded creator:** cares about provenance, audit trails, and repeatability.

## Key user journeys

### Journey A — Beginner (Phase 1)
1. Create project.
2. Import audio and album art.
3. See BPM/beat grid (analysis).
4. Choose Motion Poster preset.
5. Fill required audio provenance fields (source, license, attribution/proof).
6. Export production bundle.
7. Manually upload to YouTube using generated metadata and thumbnail.

Success: user gets a high-quality MP4 + thumbnail + metadata without needing network connectivity.

### Journey B — Power creator (Phase 4+)
1. Build a set of templates/presets for a channel.
2. Use Remix rules to create controlled variations (visual grading, typography variants, loop length variants).
3. Run an overnight batch of 100 renders.
4. Review “variant distance” report to ensure meaningful differences.
5. Export bundles for scheduled publishing.

Success: high-volume production with guardrails and crash-safe automation.

### Journey C — Publishing operator (Phase 5)
1. Connect a YouTube channel using system browser OAuth.
2. Select a channel profile template.
3. Upload a set of bundles using resumable upload.
4. Apply thumbnail and metadata.
5. Schedule publish and add to playlists.
6. Monitor quota budget and retry failed uploads.

Success: automated publishing that respects quota and audit constraints.

### Journey D — Analytics + revenue (Phase 6)
1. Sync Analytics/Reporting data via official APIs.
2. View dashboards from local DB instantly.
3. Import revenue via API where available, otherwise manual CSV import.
4. Track niches/keywords with a quota-aware notebook.

Success: local dashboards, no scraping, privacy-safe logs.

## Constraints (hard)
- **Local-first:** core workflows must work offline.
- **Reliability:** export pipeline must be crash-safe, cancelable, and resumable.
- **Determinism:** offline renders use fixed FPS stepping and seeded RNG; determinism is validated via checkpoint frame hashes.
- **Content safety:** provenance is required for production exports; originality guardrails for automation.
- **Security:** OAuth tokens never stored in plaintext; OS secure storage only.
- **Repo hygiene:** no generated artifacts committed; predictable output directories; strict `.gitignore`.

## Must / Should / Could (product-level)

### Must
- Phase 1 end-to-end production bundle workflow.
- Deterministic offline rendering with segment-based resume.
- License provenance enforcement for audio assets.
- Stable mapping/preset system with parameter registry.
- Crash-safe job queue.

### Should
- Multiple distinctive visual modes (Phase 2).
- Mixer and deterministic bounce (Phase 3).
- Batch/remix with meaningful variation guardrails (Phase 4).
- Quota-aware YouTube publishing (Phase 5).
- Disk usage management and pruning.

### Could
- Optional ML photo animation tier (Phase 2).
- Playlists automation (Phase 5).
- Revenue tracking and niche tools (Phase 6).
- Backup/restore and portability enhancements (Phase 6).

## Stop/Go gates (phase boundaries)

### Phase 1 gate (GO/NO-GO)
**GO** only when:
- 10s, 10min, 2h exports pass at 1080p30.
- Audio/video sync drift is < 1 frame at end.
- Cancel/resume works at segment boundaries.
- Determinism checkpoint hashes match for golden projects.

**STOP** if:
- Determinism or segment-based resume cannot be achieved with pinned toolchain.

### Later phase gates
Each later phase requires:
- Phase-specific acceptance tests pass (AT-002..AT-006).
- No regression in Phase 1 reliability/determinism suite.

## Glossary (project-wide)
- **Bundle:** The exported folder containing MP4 + thumbnail + metadata + provenance + build manifest.
- **Determinism:** For a given snapshot + seed + pinned toolchain, checkpoint frame hashes match exactly on the same machine/toolchain.
- **Segment:** A contiguous range of frames rendered and encoded as an intermediate artifact, used for resume and crash isolation.
- **Template:** Rules for generating metadata and default visual settings (per project or per channel).
- **Preset:** A concrete set of parameter values for a visual mode, referenced by stable IDs.
- **Mapping:** Rules that convert audio features + time → parameter values.
