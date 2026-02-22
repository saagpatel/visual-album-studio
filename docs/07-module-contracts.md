# Module Contracts (A–T)

This document defines **stable internal APIs** for modules A–T. These contracts exist to prevent rewrites later and enforce clean separation (UI vs Core vs Adapters).

## Cross-cutting contract conventions

### Stable IDs
- `AssetId`, `ProjectId`, `TemplateId`, `PresetId`, `MappingId`, `JobId`, `ExportId`, `ChannelId`, `OauthProfileId` are **opaque strings** (UUID/ULID).
- IDs must be stable across exports and stored in SQLite.

### Error model
All Core services return either success or `VasError`.

```text
VasError
- code: string (E_*)
- message: string (human readable)
- details: dict (structured debug info; safe to log)
- recoverable: bool
- hint: string (actionable remediation)
```

Rules:
- Never include secrets in `details`.
- Adapters translate external failures into `VasError` with preserved stderr/status codes.

### Jobs model (for long tasks)
Any operation that can exceed ~100ms must be a Job (persisted).

```text
Job
- id: JobId
- type: enum (ANALYZE_AUDIO, RENDER_EXPORT, ENCODE_SEGMENT, CONCAT, THUMBNAIL, UPLOAD_YT, SYNC_ANALYTICS, ...)
- status: QUEUED | RUNNING | PAUSED | CANCELED | FAILED | SUCCEEDED
- progress: JobProgress (json)
- payload: dict (json; immutable once running)
- result: dict (json)
- error: VasError? (json)
```

### Events
Services emit events to drive UI updates.

```text
Event
- type: string
- at: timestamp
- data: dict
```

Examples: `job.progress`, `asset.imported`, `analysis.ready`, `export.completed`.

### Determinism conventions
- Render determinism depends on:
  - pinned Godot version
  - render graph hash
  - fixed FPS stepping
  - seed-driven RNG only
  - stable mapping parameter registry
- Encode determinism is not guaranteed across hardware encoders. Checkpoint frame hashing validates determinism.

---

## Module A — Audio import + analysis

### Responsibilities
- Decode imported audio into canonical WAV cache (48kHz stereo PCM).
- Produce analysis features (Phase 1: BPM + beat grid; Phase 3: extended features).
- Maintain analysis versioning and cache invalidation.

### Inputs
- Audio file path(s) from filesystem.

### Outputs
- Canonical WAV path in managed library.
- `AnalysisResult` (tempo + beats + feature summaries).

### Core API (AnalysisService)
- `import_audio(path: String) -> AssetId | VasError`
- `request_analysis(audio_asset_id: AssetId, profile_id: String) -> JobId | VasError`
- `get_analysis(audio_asset_id: AssetId, analysis_version: String) -> AnalysisResult?`
- `invalidate_analysis(audio_asset_id: AssetId, reason: String) -> void`

### Events
- `asset.imported` (kind=audio)
- `analysis.progress`
- `analysis.ready`
- `analysis.failed`

### Errors
- `E_AUDIO_UNSUPPORTED_FORMAT`
- `E_FFMPEG_FAILED`
- `E_WORKER_UNAVAILABLE`
- `E_ANALYSIS_TIMEOUT`

### Persistence expectations
- Writes:
  - `assets` (canonical wav relpath, sha256)
  - `analysis_cache` + `analysis_artifacts` (keyed by hash + analysis_version)
- Reads:
  - `analysis_profiles`

### Determinism
- Analysis is deterministic for the same input WAV + pinned worker versions + parameters.
- `analysis_version` must include: librosa version, hop length, sample rate, algorithm settings.

---

## Module B — Soundscape mixer

### Responsibilities
- Multi-track soundscape timeline (volume/pan/offset/loop/fades).
- Deterministic offline bounce to a single WAV using FFmpeg filtergraphs.
- Loop-perfect output where configured.

### Inputs
- Project mixer state (tracks + automation).
- Canonical audio assets.

### Outputs
- Bounced WAV artifact with hash.

### Core API (MixerService)
- `add_track(project_id, audio_asset_id) -> TrackId`
- `set_track_params(project_id, track_id, params) -> void`
- `request_bounce(project_id, bounce_profile_id) -> JobId`
- `get_last_bounce(project_id) -> BounceResult?`

### Events
- `mixer.track_added`
- `mixer.changed`
- `bounce.progress`
- `bounce.completed`

### Errors
- `E_MIXER_INVALID_STATE`
- `E_FFMPEG_FAILED`
- `E_LOOP_BOUNDARY_INVALID`

### Persistence expectations
- Writes:
  - `project_mixer_state`
  - `audio_bounces`
- Reads:
  - `assets`, `analysis_cache` (optional for beat-aligned loops)

### Determinism
- Bounce is deterministic for the same inputs + automation + pinned FFmpeg build.
- Filtergraph is generated from stable ordering rules (track sort order stable).

---

## Module C — Visual engine foundation

### Responsibilities
- Host the deterministic render graph used by preview and offline render.
- Provide shared timing model and seeded RNG.
- Provide a parameter application pipeline for visual modes.

### Inputs
- `RenderContext` (time, fps, seed, analysis features, resolved template vars).
- Parameter values from MappingService.

### Outputs
- GPU-rendered frames for preview.
- Offscreen rendered frames for offline (via MovieWriter).

### Core API (RenderService)
- `load_mode(mode_id: String) -> void`
- `set_render_context(ctx: RenderContext) -> void`
- `render_frame(time_sec: float) -> FrameResult` (offline/headless)
- `capture_checkpoint(frame_index: int) -> Hash`

### Events
- `render.mode_loaded`
- `render.progress` (offline)
- `render.checkpoint`

### Errors
- `E_MODE_NOT_FOUND`
- `E_RENDER_GRAPH_INVALID`
- `E_GPU_UNAVAILABLE` (fallback behavior must be explicit)

### Persistence expectations
- Reads:
  - `parameter_registry`, `presets`, `templates`, `analysis_cache`
- Writes:
  - render graph hash recorded in `build_manifest`

### Determinism
- Must not depend on wall-clock time.
- All randomness derived from `seed` and stable per-frame determinism rules.

---

## Module D — Beat-synced particles

### Responsibilities
- Provide particle-based visual mode(s) with beat/onset-driven modulation.
- Register parameters in the global parameter registry.
- Support preview/offline parity.

### Inputs/Outputs
- Same as Module C; parameter set is mode-specific.

### Core API
- Implemented as a visual mode package under `app/src/modes/particles/`
- Must expose:
  - `register_parameters()`
  - `apply_parameters(values)`
  - `render()`

### Errors
- `E_PARTICLE_SHADER_COMPILE`
- `E_PARTICLE_PARAM_INVALID`

### Persistence
- Presets stored in `presets` referencing the mode + parameter overrides.

---

## Module E — Photo animator

### Responsibilities
- Animate photos with Tier 0 (no ML) and optional Tier 1 (local ML).
- Manage optional model downloads and acceleration where available.

### Inputs
- Image assets + optional masks + user keyframes.
- Optional ML model artifacts.

### Outputs
- Animated frames.

### Core API
- Tier 0:
  - `create_depth_mask(image_asset_id) -> MaskAssetId`
  - `set_parallax_params(project_id, params)`
- Tier 1 (optional):
  - `request_depth_estimate(image_asset_id) -> JobId`
  - `request_segmentation(image_asset_id) -> JobId`

### Errors
- `E_MODEL_NOT_INSTALLED`
- `E_MODEL_LICENSE_UNKNOWN` (blocks production use)
- `E_ML_INFERENCE_FAILED`

### Persistence
- `photo_layers`, `photo_masks`, `model_registry`, caches as artifacts.

---

## Module F — Audio-to-3D landscape

### Responsibilities
- Terrain/landscape shader pipeline with audio-reactive displacement and grading.
- Register parameters; ensure offline parity.

### Core API
- Visual mode package under `app/src/modes/landscape/` with standard mode interfaces.

### Errors
- `E_SHADER_INVALID`
- `E_MESH_GENERATION_FAILED`

---

## Module G — Motion poster mode

### Responsibilities
- Motion Poster v1: album art + typography + subtle motion.
- Provide 6+ distinct presets and parameterized beat-reactive behavior.
- Serve as Phase 1 “production-grade” visual mode.

### Inputs
- Album art asset; project metadata (title/artist); mapping params.

### Outputs
- Frames.

### Contract requirements
- Must expose parameter registry with stable IDs for:
  - layout, typography, palette, motion, beat response, noise/grain.
- Presets must be meaningfully distinct (not just minor numeric deltas).

---

## Module H — Mapping + presets

### Responsibilities
- Provide mapping DSL and evaluator converting audio features + time → parameter values.
- Maintain stable parameter registry and schema migrations.

### Inputs
- Analysis features (beats, bpm, spectral summaries)
- RenderContext (time, seed)
- Mapping definition (DSL) + preset overrides

### Outputs
- Deterministic parameter value map: `{param_id: value}` per frame/time.

### Core API (MappingService)
- `register_parameters(mode_id, params[]) -> void`
- `validate_mapping(mapping_dsl: String) -> ValidationResult`
- `evaluate(mapping_id, ctx: RenderContext) -> ParamValueMap`
- `create_preset(mode_id, name, seed, mapping_id, overrides) -> PresetId`
- `migrate_preset(preset_id, target_schema_version) -> PresetId`

### Errors
- `E_MAPPING_PARSE_ERROR`
- `E_PARAM_UNKNOWN`
- `E_SCHEMA_VERSION_UNSUPPORTED`

### Persistence
- `parameter_registry`, `mappings`, `presets`, `preset_versions`

### Determinism
- DSL evaluator must be pure and deterministic.
- Any RNG functions must use seed + stable hashing (no global RNG).

---

## Module I — Render/export pipeline

### Responsibilities
- Persistent job queue for render/encode/concat/thumbnail/bundle.
- Segment-based export with cancel/resume and crash-safe cleanup.
- FFmpeg invocation with progress parsing.

### Inputs
- Export snapshot (project + assets + presets + durations)
- Segment plan
- Pinned toolchain references (Godot/FFmpeg)

### Outputs
- Production bundle folder with required artifacts.

### Core API (ExportService)
- `plan_export(project_id, export_preset_id) -> ExportPlan`
- `enqueue_export(plan: ExportPlan) -> JobId`
- `request_cancel(job_id) -> void`
- `request_resume(job_id) -> JobId`
- `get_bundle(export_id) -> BundleInfo`

### Errors
- `E_FFMPEG_NOT_FOUND`
- `E_RENDERER_FAILED`
- `E_DISK_FULL`
- `E_BUNDLE_WRITE_FAILED`
- `E_DETERMINISM_MISMATCH` (test-only; gate)

### Persistence
- `jobs`, `render_jobs`, `render_segments`, `exports`, `export_artifacts`

### Determinism
- Segment boundaries are whole frames.
- Checkpoint frame hashes recorded for determinism verification.

---

## Module J — Asset library manager

### Responsibilities
- Import/copy assets into a managed library (hash-addressed).
- Track metadata, tags, usage, and license provenance.
- Provide integrity checks and relink workflows.

### Inputs
- Files selected by user.

### Outputs
- Asset records with stable IDs and managed file paths.

### Core API (AssetService)
- `import_asset(path, kind) -> AssetId`
- `get_asset(asset_id) -> Asset`
- `set_license(asset_id, license_fields) -> void`
- `validate_production_allowed(asset_id) -> ValidationResult`
- `verify_integrity(asset_id) -> IntegrityResult`
- `relink_asset(asset_id, new_path) -> void`

### Errors
- `E_ASSET_NOT_FOUND`
- `E_ASSET_HASH_MISMATCH`
- `E_LICENSE_INCOMPLETE`

### Persistence
- `assets`, `asset_license`, `asset_tags`, `asset_usage`

---

## Module K — Templates & presets (metadata + render)

### Responsibilities
- Metadata templates (title/description/tags/category/privacy/schedule placeholders).
- Variable system used by both metadata generation and on-canvas text.
- Governed template usage to reduce spam risk.

### Core API (TemplateService)
- `create_template(name, template_json) -> TemplateId`
- `render_metadata(template_id, project_id, export_plan) -> MetadataJson`
- `validate_template(template_json) -> ValidationResult`

### Persistence
- `templates`, `template_versions`, `template_bindings`

---

## Module L — YouTube integration (Phase 5)

### Responsibilities
- OAuth installed-app flow via system browser + loopback redirect.
- Resumable upload protocol implementation.
- Apply metadata, thumbnails, scheduling, playlists.
- Quota-aware behavior and audit readiness.

### Core API (PublishService)
- `connect_channel() -> OauthProfileId`
- `list_channels(oauth_profile_id) -> [Channel]`
- `enqueue_upload(export_id, channel_id, publish_profile_id) -> JobId`
- `pause_upload(job_id) -> void`
- `resume_upload(job_id) -> void`
- `unlink_channel(channel_id) -> void`
- Runtime adapter contract for upload execution:
  - `start_upload_session(file_path, metadata, selected_channel_id, profile_channel_id) -> UploadEnvelope`
  - `resume_upload_step(session_url, file_path, bytes_uploaded, chunk_size) -> UploadEnvelope`
  - `finalize_upload(video_id, metadata, thumbnail_path) -> UploadEnvelope`

`UploadEnvelope` shape:
- `ok: bool`
- `error_code: string`
- `http_status: int`
- `retryable: bool`
- `data: dict`

### Errors
- `E_OAUTH_FAILED`
- `E_OAUTH_DISALLOWED_USERAGENT`
- `E_YT_QUOTA_EXCEEDED`
- `E_YT_UPLOAD_FAILED`

### Persistence
- `oauth_profiles` (no secrets), `channels`, `youtube_uploads`, `jobs`

---

## Module M — Multi-channel management (Phase 5)

### Responsibilities
- Manage multiple OAuth profiles and channel bindings.
- Prevent wrong-channel uploads via explicit binding and confirmation.

### Core API
- `create_publish_profile(channel_id, template_id, defaults) -> PublishProfileId`
- `set_active_channel(channel_id) -> void` (requires confirmation)
- `validate_channel_binding(export_id, channel_id) -> ValidationResult`

### Persistence
- `channels`, `publish_profiles`, `template_bindings`

---

## Module N — Batch generator (Phase 4)

### Responsibilities
- Plan and execute batches of renders with priorities and schedules.
- Integrate with job queue and export pipeline.
- Enforce guardrails (variant distance checks).

### Core API
- `create_batch(plan) -> BatchId`
- `enqueue_batch(batch_id) -> JobId`
- `pause_batch(batch_id)`
- `resume_batch(batch_id)`

### Persistence
- `batch_plans`, `batch_items`, `jobs`

---

## Module O — Niche analyzer (Phase 6)

### Responsibilities
- Quota-aware niche research support (keyword notebook, competitor notes).
- Optional YouTube API search usage with explicit quota accounting.

### Core API
- `add_keyword(note)`
- `search_youtube(keyword) -> results` (optional; quota-budgeted)

### Persistence
- `niche_keywords`, `niche_notes`, `quota_budget`

---

## Module P — Analytics dashboard (Phase 6)

### Responsibilities
- Local dashboards powered by SQLite.
- Sync via official YouTube Analytics API and Reporting API.
- Incremental updates and backfills.

### Core API
- `sync_analytics(channel_id, date_range) -> JobId`
- `get_dashboard(channel_id, range) -> DashboardData`

### Persistence
- `analytics_snapshots`, `report_files`, `jobs`

---

## Module Q — Revenue tracking (Phase 6)

### Responsibilities
- Store revenue metrics where accessible.
- Provide manual import fallback with clear labeling.

### Core API
- `sync_revenue(channel_id) -> JobId`
- `import_revenue_csv(path) -> ImportResult`

### Persistence
- `revenue_records`, `imports`

---

## Module R — Remix engine (Phase 4)

### Responsibilities
- Define a declarative variant graph system for controlled variations.
- Generate remix plans for batch generator.
- Provide provenance tracking for every variant.

### Core API
- `create_variant_graph(graph_spec) -> VariantGraphId`
- `generate_variants(graph_id, count) -> [VariantSpec]`
- `compute_variant_distance(a, b) -> DistanceScore`

### Persistence
- `variant_graphs`, `variant_specs`, `variant_reports`

---

## Module S — UX platform (Phase 7)

### Responsibilities
- Provide shared UI design tokens and reusable component primitives.
- Standardize interaction states and validation surfaces across screens.
- Enforce accessibility baselines (keyboard focus, contrast, reduced motion).
- Provide command-palette command registry and dispatch contracts.

### Core API (UxPlatformService)
- `get_tokens() -> Dictionary`
- `resolve_component(component_id, variant, state) -> ComponentSpec`
- `validate_accessibility(screen_id) -> AccessibilityReport`
- `register_command(command_spec) -> void`
- `run_command(command_id, args) -> CommandResult`

### Errors
- `E_UX_TOKEN_MISSING`
- `E_COMMAND_NOT_FOUND`
- `E_ACCESSIBILITY_VIOLATION`

### Persistence
- `ui_preferences`
- `workspace_layouts`
- `command_history`

### Determinism / consistency
- UI state transitions for deterministic flows (wizard/queue actions) must be stable and testable.
- Command execution must be idempotent where specified.

---

## Module T — Productization (Phase 7)

### Responsibilities
- Provide packaging and release-manifest generation hooks.
- Manage diagnostics export and troubleshooting runbook integration.
- Define update-channel metadata stubs and rollback metadata contracts.

### Core API (ProductizationService)
- `run_packaging_dry_run(profile_id) -> PackageManifest`
- `export_diagnostics(scope) -> DiagnosticsBundleInfo`
- `get_release_channels() -> Array`
- `set_release_channel(channel_id) -> ValidationResult`
- `generate_support_report(context) -> SupportReport`

### Errors
- `E_PACKAGING_FAILED`
- `E_DIAGNOSTICS_EXPORT_FAILED`
- `E_CHANNEL_INVALID`

### Persistence
- `release_profiles`
- `diagnostics_exports`
- `support_reports`

### Security / privacy rules
- Diagnostics exports must pass redaction checks before writing.
- No secret-bearing process environment values may be included in support bundles.
