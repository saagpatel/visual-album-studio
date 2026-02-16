# Repository Structure

This document defines the intended repository layout, package boundaries, tooling, and artifact policy. The goal is predictable builds and zero repo bloat.

## Top-level layout (authoritative)

```text
/AGENTS.md
/docs/                          # This doc pack (authoritative spec)
/app/                           # Godot project root (project.godot lives here)
  /addons/                      # Third-party Godot addons (MIT-compatible)
  /src/
    /ui/                        # UI scenes/scripts (no business logic)
    /core/                      # Domain services + models (business logic)
    /adapters/                  # Side-effect wrappers (SQLite, FS, FFmpeg, IPC, keyring, YouTube)
    /modes/                     # Visual modes (G/D/E/F) + parameter bindings
    /shared/                    # Shared types/utilities (errors, IDs, serialization)
  /tests/                       # Godot-side tests + golden fixtures metadata
/worker/                        # Python analysis worker (librosa)
  /vas_audio_worker/
  /tests/
/native/                        # Rust helpers (secure storage; future native helpers)
  /vas_keyring/
/scripts/                       # Dev + CI scripts (bootstrap, lint, test, acceptance)
/tools/                         # Toolchain management (FFmpeg downloads, checksums, versions)
/out/                           # Generated outputs (gitignored; created by scripts)
```

## Package boundaries (enforced)

### UI layer (`app/src/ui`)
- Godot scenes, widgets, layout, user interaction.
- Calls into Core services via explicit interfaces.
- No direct DB/FFmpeg/network calls.

### Core services (`app/src/core`)
- Own the domain model and state transitions:
  - Asset import + provenance validation
  - Project state + snapshots
  - Mapping evaluation
  - Job queue orchestration
  - Export planning (segments, presets)
- Must be testable without rendering or external processes.

### Adapters (`app/src/adapters`)
- Wrap external side effects behind stable interfaces:
  - SQLiteAdapter (godot-sqlite)
  - FileSystemAdapter
  - FFmpegAdapter
  - PythonWorkerAdapter
  - KeyringAdapter (Rust helper)
  - YouTubeApiAdapter (Phase 5+)
- Adapters must be mockable for tests.

### Visual modes (`app/src/modes`)
- Implement render graph nodes and parameter application.
- Consume parameter values; must not own business logic.
- Must support fixed-FPS offline stepping.

## Tooling + version pinning strategy

Pinned versions are mandatory for export repeatability.
- `tools/versions.json` (created by implementation) stores pinned:
  - Godot version
  - FFmpeg version + checksums per platform
  - Python worker dependency lock hash
  - Schema version
- `scripts/bootstrap.*` validates versions and prepares local toolchain.

FFmpeg policy:
- Use a managed download in `tools/ffmpeg/<version>/<platform>/ffmpeg` (gitignored).
- Verify checksum before running.
- Record license mode (LGPL-safe vs GPL pack).

## Scripts (required entrypoints)

- `scripts/bootstrap.sh`
  - Validates/install toolchain (FFmpeg download, Python venv, Rust build)
- `scripts/dev/run_editor.sh`
  - Runs Godot editor with `--path app`
- `scripts/test/unit.sh`
  - Runs unit tests (Godot core tests + Python tests)
- `scripts/test/integration.sh`
  - Runs integration tests (IPC, FFmpeg progress, DB migration)
- `scripts/test/acceptance_phase_0X.sh`
  - Runs phase acceptance gate tests (AT-00X)

## Artifact policy (strict)

Nothing generated is allowed in git.

### Must be gitignored
- `out/**`
- `tools/ffmpeg/**`
- `worker/.venv/**`
- `app/.godot/**`
- `app/export_presets.cfg` (if generated)
- `**/*.import` (Godot import artifacts)
- `**/.DS_Store`

### Predictable output directories
- In repo/dev mode, all generated outputs go under `out/`:
  - `out/exports/`
  - `out/tmp/`
  - `out/logs/`
  - `out/cache/`
- In installed app mode, outputs go under OS user data dir (documented in `docs/00-readme.md`).

## Implementation order (recommended)

Phase 1:
1. Repo scaffolding + scripts + .gitignore
2. SQLite schema + migrations + DB adapter
3. Asset library (import/copy/hash/dedupe) + license provenance validation
4. Python worker IPC + analysis caching
5. Parameter registry + mapping DSL evaluator
6. Motion Poster mode + presets
7. Export pipeline (segment render → encode → concat → bundle)
8. Determinism + resume acceptance tests

Then proceed phase-by-phase.
