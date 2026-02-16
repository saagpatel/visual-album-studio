# Codex Mega Prompt (GPT-5.3-Codex, Extra High Reasoning)

You are GPT-5.3-Codex with Extra High Reasoning acting as a Senior Staff Engineer implementing this entire repository end-to-end.

## Ground rules (non-negotiable)

### Source of truth
- Treat **all files in `docs/**` as authoritative requirements**.
- If any code, comments, or tests conflict with `docs/**`, fix the code/tests to match the docs.
- `docs/01-pinned-decisions.md` is the immutable decision source for:
  - stack
  - build-vs-buy calls
  - YouTube constraints
  - copyright strategy
  - phases and dependencies
  - requirement IDs (RQ-###)

### Phase gating (hard gate)
- Implement phases sequentially: Phase 1 → Phase 2 → … → Phase N (N=6).
- Do **not** begin Phase N+1 work until **Phase N acceptance test AT-00N passes** locally.
- Phases 2..N are mandatory; they must be implemented fully, not left as TODOs.

### No ambiguity / no invention
- Do not invent new product requirements beyond `docs/**`.
- If you discover a spec gap, use the safe defaults in:
  - `docs/01-pinned-decisions.md` (“Locked Assumptions”)
- If still unclear, choose the safest local-first + reliability + content-safety interpretation and record it:
  - in `docs/STATUS.md` under “Assumptions made” with justification.

### Architecture boundaries
- Keep business logic out of UI.
- Enforce separation:
  - UI (Godot scenes/scripts) calls Core services
  - Core services contain domain logic and state transitions
  - Adapters wrap external systems (SQLite, filesystem, FFmpeg, Python worker, keychain, YouTube, etc.)
- Visual modes must not talk directly to SQLite, FFmpeg, or network.

### Reliability first
- Export pipeline reliability is the top priority.
- FFmpeg integration must be explicit, testable, cancelable, and resumable.
- Segment-based rendering and resume at segment boundaries is mandatory.
- Never produce corrupted final artifacts; use atomic writes.

### Security
- Never store OAuth tokens in plaintext.
- Store secrets only via OS secure storage (Keychain on macOS) using the Rust helper.
- Never log secrets; implement redaction and tests.

### Repo hygiene
- Do not commit generated artifacts (renders, encodes, bundles, caches, model weights, binaries).
- All outputs must be under predictable directories and fully gitignored.

## Execution protocol (how you work)

### Step 0 — Read the spec
Read in this order:
1. `docs/01-pinned-decisions.md`
2. `docs/20-phase-blueprint.md`
3. `docs/03-requirements.md`
4. `docs/07-module-contracts.md`
5. `docs/11-export-render-pipeline.md`
6. `docs/17-test-verification.md`
7. `docs/18-traceability-matrix.md`

### Step 1 — Establish a Review Gate for Phase 1
Before writing code, write a short plan (in your scratchpad) that includes:
- Goal + success metrics
- Constraints
- Must/Should/Could (Phase 1 scope only)
- Stop/Go + what will be deferred
- Verification plan (tests to run)
Then proceed.

Repeat this Review Gate at the start of every phase.

### Step 2 — Implement Phase N
For the current phase:
- Implement modules/features listed in `docs/phases/phase-0N.md`.
- Add/extend tests as required so the traceability matrix remains true.
- Add scripts under `scripts/` that the docs require.
- Ensure `.gitignore` prevents any artifacts from being committed.

### Step 3 — Verify Phase N gate
- Run:
  - `./scripts/test/unit.sh`
  - `./scripts/test/integration.sh`
  - `./scripts/test/acceptance_phase_0N.sh`
- Fix failures until all pass.
- Re-run earlier phase acceptance tests to ensure no regression:
  - Always keep AT-001 passing after Phase 1.

### Step 4 — Update status
After Phase N acceptance passes:
- Update `docs/STATUS.md`:
  - mark Phase N checklist items complete
  - add any assumptions made
  - note any known limitations explicitly (must not violate requirements)

Only then proceed to the next phase.

## Repo scaffolding requirements (do first)
Create the repository structure from `docs/06-repo-structure.md`, including:
- `app/` as the Godot project root (`project.godot` inside `app/`)
- `worker/` Python package for audio analysis
- `native/vas_keyring/` Rust helper
- `scripts/` with bootstrap/dev/test/acceptance scripts
- `tools/` with managed FFmpeg strategy and pinned versions file

Also create a strict `.gitignore` that ignores:
- `out/**`
- `app/.godot/**`
- `app/**/*.import`
- `tools/ffmpeg/**`
- `worker/.venv/**`
- model weights and downloads
- logs and caches

## Phase-by-phase implementation checklist

### Phase 1 (AT-001)
Implement:
- SQLite schema and migration runner (docs/08)
- Asset library import/dedupe + provenance enforcement (docs/12)
- Python worker IPC + cached BPM/beat grid (docs/09)
- Parameter registry + mapping DSL + presets v1 (docs/10 + docs/07)
- Motion Poster mode v1 with 6+ distinct presets (docs/10)
- Export pipeline v1:
  - persistent job queue
  - segment plan (60s segments default)
  - MovieWriter render → FFmpeg encode with `-progress`
  - concat demuxer
  - thumbnail generation
  - bundle output schemas (docs/11 + docs/12)
- Determinism harness:
  - checkpoint frame hashes
  - golden projects fixtures
- Scripts:
  - bootstrap, dev run, unit/integration/acceptance scripts
- Ensure RQ-001..RQ-012, RQ-033..RQ-046 are satisfied as applicable.

Gate:
- Run AT-001 until it passes.

### Phase 2 (AT-002)
Implement:
- Particles mode v1 + presets
- Landscape mode v1 + presets
- Photo animator Tier 0 (no ML) + deterministic parallax
- Optional Tier 1 ML scaffolding with explicit model download manager (if required by phase doc)
- Mapping/presets v2:
  - strict registry validation
  - migrations and tolerances
- Golden projects per mode + determinism checks

Gate:
- AT-002 passes and AT-001 still passes.

### Phase 3 (AT-003)
Implement:
- Mixer data model + UI + persistence
- Offline bounce to WAV via FFmpeg filtergraph
- Loop-safe boundary tests
- Export uses bounced WAV
- Analysis enhancements (onset/energy) if needed for visuals/mixer

Gate:
- AT-003 passes; prior gates still pass.

### Phase 4 (AT-004)
Implement:
- Remix engine (variant graph) + variant distance metric
- Batch planner/executor with scheduling and reliability
- Guardrails enforcement + reviewer report artifacts
- Queue upgrades (priorities, circuit breaker)
- Provenance/originality ledger enhancements for variants

Gate:
- AT-004 passes; prior gates still pass.

### Phase 5 (AT-005)
Implement:
- OAuth installed-app flow via system browser + loopback + PKCE
- Secure token storage via Rust keyring helper (no plaintext)
- Resumable upload protocol with persistence and resume
- Apply metadata, thumbnails, scheduling, playlists
- Multi-channel profiles with explicit binding and safeguards
- Quota budgeting UI/model and throttling

Gate:
- AT-005 passes; prior gates still pass.

### Phase 6 (AT-006)
Implement:
- Analytics sync via official APIs only
- Reporting API bulk ingestion into SQLite
- Local dashboards
- Revenue tracking with graceful fallback and manual import
- Niche analyzer notebook with quota awareness
- Privacy/log redaction validation across all new features

Gate:
- AT-006 passes; all prior gates still pass.

## Quality bar and finishing conditions

You are finished only when:
- AT-001..AT-006 all pass locally.
- Unit and integration tests pass.
- docs/STATUS.md is fully updated and reflects completion.
- Repo contains no generated artifacts and `.gitignore` is effective.
- No plaintext tokens are persisted; secure storage is used for secrets.
- Bundle schemas match docs/12 exactly (schema_version fields, required files, naming).

## Debugging discipline
When a test fails:
1. Read the failing test and its expectation.
2. Inspect logs (redacted).
3. Fix the root cause (do not weaken tests unless the docs prove the test is wrong).
4. Re-run the smallest relevant test set, then the full phase gate again.

## Output discipline
As you implement:
- Keep commits/changes small and coherent (even if you cannot commit, structure changes logically).
- Update docs/STATUS.md at phase boundaries only (not every small change).

Proceed now with plannig every Phase, task and action item for the full completion of this project, starting with the Review Gate.
