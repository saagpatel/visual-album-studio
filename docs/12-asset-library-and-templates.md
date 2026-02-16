# Asset Library and Templates

This document specifies asset ingestion/management (J) and template/preset management (K), including bundle output schemas.

## Asset library (J)

### Goals
- Deterministic asset IDs and managed storage for reliability.
- Strong license provenance tracking, especially for audio.
- Usage tracking across projects and exports.
- Integrity verification and relink support.

### Managed library model
On import:
1. Compute SHA-256 of the source file.
2. Determine `kind` (audio/image/video/font/other) and metadata (duration, dimensions).
3. Copy into managed library using hash-addressed paths.
4. Store asset record in SQLite.

**Managed path convention (authoritative):**
```text
library/
  audio/<sha256[0:2]>/<sha256>.wav          # canonical decode
  audio_src/<sha256[0:2]>/<sha256>.<ext>    # optional preserved original
  images/<sha256[0:2]>/<sha256>.<ext>
  fonts/<sha256[0:2]>/<sha256>.<ext>
  models/<model_id>/...                      # Phase 2 optional
```

Rules:
- Canonical WAV is always stored as `.wav` (48kHz stereo PCM s16le).
- Original source may be preserved separately (optional but recommended).
- Dedupe is based on `(sha256, kind)`.

### Tagging and usage tracking
- Users can apply tags to assets (genre, mood, pack name, etc.).
- Usage is tracked:
  - asset ↔ project
  - asset ↔ export

### License provenance (non-negotiable)
Audio assets must include provenance before “production export”:
- `source_type`: original | licensed_pack | youtube_audio_library | creative_commons | commissioned | unknown
- `license_name` and/or `license_url`
- `attribution_text` when required
- `proof_relpath` when applicable (license certificate, receipt, etc.)

Production export gating (RQ-044):
- If `source_type == unknown`, production export is blocked.
- Draft export remains available for internal review.

## Templates & presets (K)

### Goals
- Generate metadata consistently.
- Support per-channel defaults for later publishing.
- Avoid “template spam” by encouraging variation and governance.

### Template types
1. **Metadata template** (Phase 1)
   - Generates `metadata.json` for a bundle.
2. **Publish profile template** (Phase 5)
   - Binds metadata + default privacy + scheduling rules to a channel.
3. **Visual defaults template** (Phase 4+)
   - Defines default preset selection and controlled variation envelopes.

### Variable system (authoritative)
Templates may reference variables using `{var_name}` syntax.

Variable sources:
- Project fields: `{project.title}`, `{project.artist}`, `{project.series}`
- Audio analysis: `{audio.bpm}`, `{audio.duration_sec}`
- Export context: `{export.fps}`, `{export.width}`, `{export.height}`, `{export.duration_hms}`
- Date/time: `{now.iso_date}`

Rules:
- Variables resolve deterministically during export planning.
- Missing variables resolve to empty string and generate a warning.

### Template JSON structure (v1)
Stored in `templates.template_json`.

```json
{
  "schema_version": 1,
  "name": "Default Template",
  "metadata": {
    "title": "{project.title} — Visual Album",
    "description": "Track: {project.title}\nBPM: {audio.bpm}\n\n{provenance.attribution_block}",
    "tags": ["visual album", "{project.genre}"],
    "categoryId": "10",
    "privacyStatus": "private",
    "publishAt": null,
    "chapters": []
  },
  "visual_defaults": {
    "mode_id": "motion_poster",
    "preset_id": "preset_default",
    "seed_strategy": "project_seed"
  }
}
```

## Output bundle specification (Phase 1 gate)

### Bundle directory layout (authoritative)
```text
<exports>/<export_id>/
  video.mp4
  thumbnail.png
  metadata.json
  provenance.json
  build_manifest.json
```

### metadata.json schema (v1)
```json
{
  "schema_version": 1,
  "title": "string (required)",
  "description": "string (required)",
  "tags": ["string", "..."],
  "categoryId": "string (YouTube category id; default '10' Music)",
  "privacyStatus": "private|unlisted|public",
  "publishAt": "ISO-8601 timestamp or null",
  "playlistIds": ["string", "..."],
  "chapters": [
    { "time_sec": 0, "title": "Intro" }
  ]
}
```

### provenance.json schema (v1)
```json
{
  "schema_version": 1,
  "audio": {
    "asset_id": "AssetId",
    "sha256": "string",
    "source_type": "original|licensed_pack|youtube_audio_library|creative_commons|commissioned|unknown",
    "license_name": "string|null",
    "license_url": "string|null",
    "attribution_text": "string|null",
    "proof": [
      { "type": "url|file", "value": "string" }
    ],
    "notes": "string|null"
  },
  "originality_ledger": {
    "template_id": "TemplateId",
    "preset_id": "PresetId",
    "mapping_id": "MappingId",
    "seed": 12345,
    "notable_changes": [
      { "param_id": "mp.color.accent", "from": "#ff00ff", "to": "#00ffff" }
    ],
    "user_notes": "string|null"
  },
  "attribution_block": "string (copy/paste ready)"
}
```

### build_manifest.json schema (v1)
```json
{
  "schema_version": 1,
  "toolchain": {
    "godot_version": "string",
    "render_graph_hash": "string",
    "ffmpeg_version": "string",
    "ffmpeg_license_mode": "lgpl|gpl_pack",
    "analysis_worker_version": "string"
  },
  "snapshot": {
    "export_id": "ExportId",
    "project_id": "ProjectId",
    "inputs": {
      "audio_asset_id": "AssetId",
      "audio_sha256": "string",
      "album_art_asset_id": "AssetId",
      "album_art_sha256": "string",
      "fonts": []
    },
    "preset_id": "PresetId",
    "mapping_id": "MappingId",
    "template_id": "TemplateId",
    "seed": 12345,
    "fps": 30,
    "width": 1920,
    "height": 1080,
    "duration_frames": 1800,
    "segment_plan": {
      "segment_frames": 1800,
      "segments": [
        { "index": 0, "start_frame": 0, "frame_count": 1800 }
      ]
    }
  },
  "outputs": {
    "video": { "container": "mp4", "codec": "h264", "encoder": "h264_videotoolbox", "settings": {} },
    "audio": { "codec": "aac", "bitrate": 192000 },
    "thumbnail": { "width": 1280, "height": 720, "time_sec": 0.0 }
  }
}
```

## Verification
- Schema validation tests (TS-005) validate JSON outputs.
- Provenance validator (TS-006) enforces production gating rules.
- Phase 1 acceptance (AT-001) checks bundle completeness and correct naming.
