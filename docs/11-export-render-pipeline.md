# Export & Render Pipeline (Reliability-Critical)

This is the most reliability-critical subsystem. It must be **explicit, testable, cancelable, resumable**, and deterministic at the frame level.

## Goals (Phase 1 gate)
- Export “production bundle” locally:
  - `video.mp4`
  - `thumbnail.png`
  - `metadata.json`
  - `provenance.json`
  - `build_manifest.json`
- Support 10s → 2h+ with:
  - segmentation
  - progress reporting
  - cancel
  - resume from last completed segment
  - crash-safe recovery
- Determinism:
  - checkpoint frame hashes stable for golden projects (same inputs + seed + toolchain).

## High-level pipeline stages

```text
(1) Validate inputs (assets + licenses + templates)  [fast]
(2) Plan export (snapshot + segments)                [fast]
(3) For each segment:
      (3a) Offline render segment frames (PNG)
      (3b) Encode segment MP4 (FFmpeg)
      (3c) Cleanup segment frames (policy)
(4) Concat segments → final video.mp4 (FFmpeg)
(5) Generate thumbnail.png (FFmpeg or Godot capture)
(6) Write metadata.json + provenance.json + build_manifest.json
(7) Atomic finalize bundle directory
```

All stages are modeled as persisted jobs (RQ-036) with sub-stage progress (RQ-046).

## Workspace layout (per job)

All intermediate artifacts live in a per-job workspace.

```text
<tmp_root>/jobs/<job_id>/
  job_manifest.json              # planned stages + snapshot reference
  segments/
    000/
      frames/                    # PNG sequence (deleted after encode by default)
      segment.mp4                # encoded segment
      segment.manifest.json      # segment metadata + hashes
    001/...
  concat/
    concat_list.txt              # ffmpeg concat demuxer list
  final/
    video.mp4                    # written only after successful concat
    thumbnail.png
```

Final bundle is written under:
- repo/dev mode: `out/exports/<export_id>/`
- installed app: `<app_data>/exports/<export_id>/`

Finalization uses **atomic rename**:
- write to `bundle_tmp/` then rename to `bundle/` on success
- never leave a partially written `video.mp4` as the final artifact.

## Segmentation strategy (Phase 1 baseline)

### Segment size (locked default)
- Default segment duration: **60 seconds**
- Segment frames: `segment_frames = fps * 60`

Rationale:
- Provides practical resume granularity without excessive concat overhead.

### Segment plan algorithm
Given `total_frames` and `segment_frames`:
- Produce segments `i = 0..N-1` with:
  - `start_frame = i * segment_frames`
  - `frame_count = min(segment_frames, total_frames - start_frame)`

Segment boundaries must be whole frames; time = frame_index/fps.

### Resume semantics
- On resume:
  - For each segment:
    - if `segment.mp4` exists and hash matches recorded manifest: mark as encoded
    - else rerender/re-encode segment
- Final concat runs only when all segments encoded.

### Cancel semantics
- Cancel request is honored at safe points:
  - between segments
  - between render and encode for a segment
  - between FFmpeg operations
- On cancel:
  - Job status becomes `canceled`
  - Completed segment artifacts remain
  - No final bundle is finalized
- Resume from cancel uses the same resume semantics.

## Determinism strategy

### Deterministic render
- Offline render is fixed-FPS stepping:
  - `t = frame_index / fps`
- Seeded RNG only (recorded in snapshot).
- Mapping evaluation must be pure and deterministic.

### Determinism verification
- Golden projects define checkpoint frames (e.g., 0/900/1800).
- During export:
  - capture checkpoint frame(s) as raw PNG (or buffer)
  - compute SHA-256 of normalized pixel bytes
- AT-001 compares checkpoint hashes across runs.

### Nondeterminism boundaries (explicit)
- Encoder output (`video.mp4` bytes) may differ across:
  - FFmpeg builds
  - hardware encoders
  - platform differences
- Checkpoint frame hashes are the determinism truth.

## FFmpeg integration (explicit)

### Progress reporting (required)
Use machine-readable progress:

```bash
ffmpeg ... -progress pipe:1 -nostats -hide_banner
```

Parse lines of form:
- `out_time_ms=...`
- `frame=...`
- `progress=continue|end`

Unify into JobProgress:
- stage, percent, eta, frames_done, fps_est, bytes_written.

### Encoding (baseline)
Encode each segment into MP4.

Baseline requirements:
- H.264 video in MP4 container
- AAC audio
- pixel format yuv420p (YouTube-friendly)

Encoder selection policy (locked):
1. Prefer platform LGPL-safe encoders when available:
   - macOS: `h264_videotoolbox`
2. If unavailable, allow optional user-enabled **GPL encoder pack** (e.g., `libx264`) with explicit acknowledgement.
3. Record chosen encoder and FFmpeg license mode in build_manifest.json.

Reference command (conceptual):
```bash
ffmpeg -y -framerate <fps> -i frames_%06d.png   -i audio.wav   -c:v <encoder> <encoder_opts>   -pix_fmt yuv420p   -c:a aac -b:a 192k   -shortest   -movflags +faststart   segment.mp4   -progress pipe:1 -nostats -hide_banner
```

### Concat segments (resume-safe)
Use concat demuxer (not filter) for MP4 segments:

`concat_list.txt`:
```text
file 'segments/000/segment.mp4'
file 'segments/001/segment.mp4'
...
```

Command:
```bash
ffmpeg -y -f concat -safe 0 -i concat_list.txt -c copy video.mp4   -progress pipe:1 -nostats -hide_banner
```

### Thumbnail generation (YouTube-valid)
Default thumbnail:
- 1280x720 PNG
- <= 2 MB (auto shrink if larger)

Reference:
```bash
ffmpeg -y -ss <time_sec> -i video.mp4 -vframes 1 -vf "scale=1280:720" thumbnail.png
```

If size > 2MB:
- re-encode with higher compression or palette reduction while preserving PNG requirement.

## Build manifest + provenance

### build_manifest.json (required fields)
- toolchain:
  - godot_version
  - render_graph_hash
  - ffmpeg_version
  - ffmpeg_license_mode (lgpl|gpl_pack)
  - analysis_worker_version
- snapshot:
  - project_id, export_id
  - input asset hashes (audio/image/fonts)
  - template_id, preset_id, mapping_id, schema versions
  - seed, fps, resolution, duration_frames
  - segment_plan (segment_frames, count, list)
- outputs:
  - video codec/encoder + settings
  - audio codec + settings
  - thumbnail time/frame index

### provenance.json (required fields)
- audio asset provenance:
  - source_type, license, attribution text, proof reference(s)
- originality ledger summary:
  - preset/template used
  - notable parameter deltas
  - seed
  - user-provided notes

## Cleanup policy (Phase 1 baseline)
- Default: delete segment frame PNGs after the segment MP4 is successfully encoded and hashed.
- Retain:
  - segment MP4s until final concat succeeds
  - job_manifest.json and logs for diagnostics
- Prune:
  - old tmp workspaces by age/LRU (configurable)

## Verification (Phase 1 acceptance)
AT-001 must validate:
- 10s, 10min, 2h exports at 1080p30 produce bundles.
- A/V sync drift < 1 frame at end (beat marker overlay method).
- Cancel mid-export:
  - does not leave corrupted `video.mp4`
  - resume reuses completed segments
- Determinism:
  - checkpoint frame hashes match across reruns on the same machine/toolchain.
