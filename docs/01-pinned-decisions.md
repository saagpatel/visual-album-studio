# Pinned Decisions (Immutable)

This document freezes the decisions from the **Deep Research Decision Pack**. These decisions are treated as **non-negotiable** for implementation.

If another doc conflicts with this one, this doc wins.

## 1. Core Stack (authoritative)

- **UI + Real-time Preview Renderer:** **Godot Engine** (MIT)
  - Godot is used for the interactive editor UI and the live preview renderer.
- **Deterministic Offline Rendering:** **Godot MovieWriter**
  - Offline export uses fixed-FPS simulation / perfect frame pacing.
  - Export frames to an **image sequence** (PNG) and then encode with FFmpeg.
  - Rationale: Godot’s built-in AVI output has a 4 GB limit; PNG sequence + WAV is the intended path for FFmpeg encoding.
- **Export/Encode/Mux “truth pipeline”:** **FFmpeg** (pinned version)
  - Responsible for encoding image sequences to MP4, audio muxing, segment concat for resume, and thumbnail generation.
  - Progress reporting must use `-progress` machine-readable output.
- **Persistent local storage:** **SQLite** (public domain)
  - Used for assets, projects, analyses, presets, jobs, exports, channels, analytics snapshots, revenue records, etc.
- **Audio analysis worker:** **Python worker process (librosa)**
  - Separate local worker process for tempo/beat/features.
  - Cache analysis results keyed by `(audio_hash, analysis_version)`.

## 2. Architecture decisions (authoritative)

- **Single deterministic render graph** for preview ↔ offline parity:
  - Preview is audio-clocked but uses the same mapping functions and seeded RNG as export.
  - Offline uses `time = frame_index / fps` stepping.
- **Long-duration reliability** (10 seconds → 2+ hours) requires:
  - Render segmentation
  - Progress reporting
  - Cancel and resume at segment boundaries
  - Crash-safe cleanup
  - Version-pinned toolchain to prevent drift
- **Local-first boundary:**
  - Default workflows are offline.
  - Network is used only for YouTube APIs and analytics later.

## 3. Security model (authoritative)

- YouTube OAuth tokens (access/refresh) **must not be stored in plaintext**.
- Tokens must be stored using **OS secure storage (Keychain on macOS)**.
- Implementation approach: **small Rust helper using `keyring` crate** + cross-platform keyring storage.

## 4. YouTube integration constraints (authoritative)

- OAuth for installed apps:
  - **System browser** + **local loopback redirect**.
  - Avoid embedded webviews (embedded user agents can be disallowed).
- Upload reliability:
  - Use the **resumable upload protocol** for large files.
- Quotas and audits:
  - Operations must be quota-aware.
  - Default daily quota is limited; additional quota may require compliance audit.
- Critical compliance constraint:
  - Uploads from **unverified API projects** (created after July 28, 2020) may be restricted to **private** until the project passes an audit.

## 5. Copyright & monetization risk strategy (authoritative)

This is treated as a product constraint.

- **Content ID reality:** uploads are scanned automatically; matches can lead to blocking/monetization/tracking.
- **Monetization risk (reused/inauthentic content):**
  - Channels can lose monetization eligibility for repetitive or mass-produced content even without copyright strikes.
- Product-level mitigations:
  - Enforce **asset provenance** for audio.
  - Include `provenance.json` with license notes and attribution blocks.
  - Avoid “template spam” by designing visually distinct modes and enforcing batch variation guardrails (Phase 4).
  - Provide an "originality ledger" per export.

## 6. Build vs Buy decisions (Modules A–T)

These are the authoritative implementation choices and deferrals.

### Core media engine and export
- **A Audio import + analysis:** Integrate (librosa; cache in SQLite)
- **B Soundscape mixer:** Build + Integrate (FFmpeg filtergraph; optional miniaudio for preview)
- **C Visual engine:** Integrate (Godot + MovieWriter)
- **D Beat-synced particles:** Build (Godot particle systems + shaders)
- **E Photo animator:** Defer to Phase 2 (OpenCV + optional ML models via ONNX Runtime)
- **F Audio-to-3D landscape:** Defer to Phase 2 (Godot mesh + shader displacement)
- **G Motion poster:** Integrate + Build (Godot 2D/3D typography + shaders)
- **H Mapping + presets:** Build (custom DSL + schema; store in SQLite)
- **I Render/export pipeline:** Integrate (Godot MovieWriter + FFmpeg encode/mux/concat/progress)

### Asset, templates, and ops
- **J Asset library manager:** Build + Integrate (SQLite + Godot-SQLite plugin)
- **K Templates & presets:** Build (template schema + variable system; stored in SQLite)
- **L YouTube integration:** Defer to Phase 5
- **M Multi-channel management:** Defer to Phase 5
- **N Batch generator:** Defer to Phase 4
- **O Niche analyzer:** Defer to Phase 6
- **P Analytics dashboard:** Defer to Phase 6
- **Q Revenue tracking:** Defer to Phase 6
- **R Remix engine:** Defer to Phase 4
- **S UX platform:** Defer to Phase 7 (design tokens, component system, accessibility, workflow shell)
- **T Productization:** Defer to Phase 7 (packaging hooks, diagnostics UX, update-channel architecture stubs)

## 7. Phase list (authoritative)

1. Phase 1 — Local-only end-to-end production bundle
2. Phase 2 — Visual modes expansion + mapping/preset hardening
3. Phase 3 — Soundscape mixer + deterministic offline bounce
4. Phase 4 — Automation: batch + remix + guardrails
5. Phase 5 — Optional YouTube publishing + multi-channel
6. Phase 6 — Analytics + niche + revenue
7. Phase 7 — UX excellence + productization

Stop/Go rule:
- **STOP** if Phase 1 export pipeline cannot be made deterministic and resumable at segment boundaries.
- **GO** only when Phase 1 acceptance criteria are met.

## 8. Dependency DAG summary (authoritative)

Module DAG (high-level):
- A → H
- B → I
- C → (D, E, F, G)
- (D, E, F, G) → H
- (C, H, A, B) → I
- J → (A, B, C, H, I, K, L, P, Q, R)
- K → (I, L, N, R, M)
- I → (N, R, L)
- L → (M, P)
- P → Q
- C → S
- (H, I, J, K, L, M, P, Q) → S
- (I, J, L, P, S) → T

Phase DAG:
- Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7

## 9. Locked Assumptions (chosen safe defaults)

The Decision Pack listed open questions. This plan resolves them now.

- **Distribution intent:** assume potential distribution later.
  - Avoid AGPL/GPL dependencies by default.
  - If GPL encoders are used, they must be opt-in and explicitly recorded (see FFmpeg policy below).
- **Baseline export standard:** 1080p @ 30 fps is the baseline.
  - 4K is deferred until stability is proven (post Phase 2).
- **ML model bundling:** ML models are never shipped by default.
  - Users explicitly download optional models; provenance and checksums are recorded.
- **YouTube scope:** optional and deferred to Phase 5.
  - Phases 1–4 remain fully useful offline.
- **FFmpeg delivery:** managed FFmpeg installation downloaded/verified by scripts.
  - Binaries are not committed to git. Checksums are verified.

## 10. FFmpeg licensing policy (locked)

- Maintain two FFmpeg modes:
  - **Default (LGPL-safe) encoder set** using platform encoders where available (e.g., `h264_videotoolbox` on macOS).
  - **Optional GPL encoder pack** (e.g., `libx264`) only if needed and explicitly enabled by the user.
- The selected license mode must be surfaced in Settings and recorded in every bundle `build_manifest.json`.
