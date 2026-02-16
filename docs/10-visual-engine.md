# Visual Engine (Preview + Offline Render)

Godot is used for both the interactive editor UI and the real-time preview renderer. Offline rendering uses the same render graph with fixed-FPS stepping to preserve preview/export parity.

## Goals
- **Single render graph** used for preview and offline export.
- **Deterministic offline rendering** with fixed FPS stepping (MovieWriter).
- Visual diversity to reduce “template spam” risk.
- Stable parameter system via registry + presets + mapping engine.

## Preview vs Offline Rendering Architecture

### Preview
- Runs in the editor process.
- Timebase is audio-clocked: `t = audio_playhead_seconds`.
- Each frame:
  1. Gather `RenderContext` (t, bpm, beat_phase, seed, resolved template vars).
  2. Mapping engine produces `{param_id: value}`.
  3. Visual mode applies parameters and renders.

### Offline render
- Runs in a dedicated **render runner** (can be headless) to isolate crashes.
- Timebase is fixed:
  - `t = frame_index / fps`
  - `delta = 1/fps`
- Segment plan defines `(start_frame, frame_count)` per segment.
- Output:
  - frames: PNG sequence per segment
  - optional audio: WAV (Phase 1 can loop a single audio track; Phase 3 uses bounced WAV)

## Parameter System (H + C contract)

### Parameter registry
- Parameters are declared per mode with stable IDs:
  - Example: `mp.text.title_size`
- Parameter declaration includes:
  - type: float/int/bool/color/vec2/vec3/enum/string
  - default
  - semantic range (min/max)
  - description
  - schema version introduced

### Parameter application rules
- Mode owns how parameters affect the scene graph, but:
  - Mode must not read from DB or filesystem directly.
  - Mode must not generate randomness except via the seeded RNG provided in `RenderContext`.
- Parameter values are applied deterministically in a stable order:
  - sort by param_id lexicographically before applying
  - apply before render step

### Seeded RNG
- `RenderContext.seed` is the only randomness source.
- Per-frame random values must be derived from stable hashing:
  - `rng(seed, frame_index, param_id)` pattern
- Never use `Time.get_ticks_msec()`, `OS.get_unix_time()`, etc. in render logic.

## GPU and determinism considerations
- Determinism is validated via **checkpoint frame hashing** on the same machine and pinned toolchain.
- Minor cross-machine pixel differences are possible due to GPU/driver variation; this is explicitly outside the determinism guarantee.
- Avoid nondeterministic GPU features where possible:
  - no temporal reprojection
  - avoid stochastic sampling
  - avoid reading uninitialized buffers

## Visual modes specification (all modes)

### Mode G — Motion Poster (Phase 1)
**Purpose:** Album art + typography + subtle motion with beat-reactive parameters.

**Required assets:**
- Primary audio (required)
- Album art image (required)
- Optional: font asset (fallback to default bundled font)

**Core layout elements:**
- Background layer (solid/gradient + grain)
- Album art panel (transform + subtle parallax)
- Title text + artist text
- Optional progress/beat indicator (debug and optional export overlay for sync verification)

**Stable parameters (minimum)**
Typography:
- `mp.text.title` (string; resolved from template vars)
- `mp.text.artist` (string)
- `mp.text.title_size` (float; 12..180)
- `mp.text.artist_size` (float; 10..120)
- `mp.text.tracking` (float; -10..50)
- `mp.text.line_height` (float; 0.8..1.6)
- `mp.text.align` (enum; left|center|right)

Layout:
- `mp.layout.art_scale` (float; 0.2..1.5)
- `mp.layout.art_rotation_deg` (float; -15..15)
- `mp.layout.art_pos_x` (float; -1..1 normalized)
- `mp.layout.art_pos_y` (float; -1..1 normalized)
- `mp.layout.safe_margin` (float; 0..0.2 normalized)

Color:
- `mp.color.bg_primary` (color)
- `mp.color.bg_secondary` (color)
- `mp.color.text_primary` (color)
- `mp.color.accent` (color)
- `mp.color.grade_amount` (float; 0..1)

Motion:
- `mp.motion.float_amp` (float; 0..80 px)
- `mp.motion.float_speed` (float; 0..4)
- `mp.motion.zoom_amp` (float; 0..0.2)
- `mp.motion.rotation_wobble_deg` (float; 0..5)
- `mp.motion.noise_amount` (float; 0..1)

Beat response:
- `mp.beat.pulse_amount` (float; 0..1)
- `mp.beat.pulse_decay` (float; 0..1)
- `mp.beat.glow_amount` (float; 0..1)
- `mp.beat.shake_amount` (float; 0..20 px)

Debug/verification:
- `mp.debug.beat_overlay_enabled` (bool)
- `mp.debug.beat_overlay_opacity` (float; 0..1)

**Preset requirements (Phase 1)**
- At least 6 presets with:
  - distinct palettes and layout composition
  - distinct motion character (e.g., float vs punchy pulse vs slow zoom)
  - distinct typography choices

### Mode D — Beat-synced particles (Phase 2)
**Purpose:** Particle fields that react to beats/onsets.

Assets:
- Optional texture atlas for particles
- Optional LUT/grading preset (stored as parameters or asset reference)

Parameters (minimum):
- `pt.emission.rate` (float; 0..5000)
- `pt.emission.burst_on_beat` (bool)
- `pt.emission.burst_count` (int; 0..5000)
- `pt.physics.gravity` (vec3)
- `pt.physics.turbulence` (float; 0..10)
- `pt.color.palette_a` (color)
- `pt.color.palette_b` (color)
- `pt.color.beat_flash_amount` (float; 0..1)
- `pt.camera.zoom` (float; 0.5..3)
- `pt.camera.rotation_speed` (float; -2..2)
- `pt.post.bloom_amount` (float; 0..1)

### Mode F — Audio-to-3D landscape (Phase 2)
**Purpose:** 3D terrain/displacement driven by audio features.

Parameters (minimum):
- `ls.terrain.scale` (float; 0.1..10)
- `ls.terrain.displacement_amount` (float; 0..5)
- `ls.terrain.displacement_source` (enum; rms|onset|beat_phase)
- `ls.camera.path` (enum; orbit|flyover|static)
- `ls.camera.speed` (float; 0..5)
- `ls.color.grade_preset` (enum)
- `ls.color.saturation` (float; 0..2)
- `ls.color.contrast` (float; 0..2)
- `ls.atmos.fog_density` (float; 0..1)
- `ls.lighting.key_intensity` (float; 0..10)
- `ls.lighting.rim_intensity` (float; 0..10)

### Mode E — Photo animator (Phase 2)
**Purpose:** Animate still images.

Tier 0 (no ML):
- Ken Burns (pan/zoom) with optional procedural parallax using a user-defined depth mask/layers.

Tier 1 (optional local ML):
- Depth estimation (MiDaS/ZoeDepth) + segmentation (SAM) via ONNX Runtime, with CoreML EP on macOS where available.

Parameters (minimum):
- `ph.kb.start_zoom` (float; 0.8..2.0)
- `ph.kb.end_zoom` (float; 0.8..2.0)
- `ph.kb.pan_x` (float; -1..1)
- `ph.kb.pan_y` (float; -1..1)
- `ph.parallax.amount` (float; 0..1)
- `ph.parallax.layer_count` (int; 1..8)
- `ph.depth.mask_asset_id` (string; AssetId)
- `ph.ml.enabled` (bool)
- `ph.ml.depth_model_id` (string; model_registry.id)
- `ph.ml.segmentation_model_id` (string)

## Verification requirements by mode
- Every mode must pass preview/offline parity on golden projects.
- Every mode must declare all parameters in the registry; no hidden parameters.
- Determinism tests (checkpoint hashing) must be run for each mode’s golden projects.
