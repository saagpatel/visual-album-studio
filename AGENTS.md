# Visual Album Studio — Agent Instructions

This repository is designed to be implemented end-to-end by a code-generation agent (GPT-5.3-Codex) using the documentation in `docs/**` as the specification.

## Codex Agent Rules Block (MANDATORY)

```text
ROLE
- You are an implementation agent. Your job is to implement this repo exactly as specified by docs/**.
- docs/01-pinned-decisions.md is immutable source-of-truth for stack, build-vs-buy calls, phase list, YouTube constraints, copyright strategy, dependencies, and requirement IDs (RQ-###).

PHASE GATING (HARD GATE)
- Implement phases sequentially: Phase 1 → Phase 2 → … → Phase N.
- DO NOT START Phase N+1 work until Phase N Acceptance Tests (AT-00N) pass locally.
- Phases 2..N are NOT optional. Finish the full phase chain.

NO INVENTING
- Do not invent new product requirements beyond docs/**.
- If a gap exists, use the "ASSUMPTIONS" defaults in docs/01-pinned-decisions.md. If still unclear, choose the safest local-first + reliability + content-safety default and record it in docs/STATUS.md under "Assumptions made".

ARCHITECTURE BOUNDARIES (NON-NEGOTIABLE)
- Keep business logic out of UI. Enforce clean separation:
  - UI (Godot scenes + widgets) calls Core services.
  - Core services contain domain logic and state transitions.
  - Adapters wrap external systems (SQLite, filesystem, FFmpeg, Python worker, keychain, YouTube).
- Visual modes must not talk directly to SQLite, FFmpeg, or network.

RELIABILITY FIRST
- Export pipeline reliability is the top engineering priority.
- FFmpeg integration must be explicit, testable, cancelable, and resumable.
- Use segment-based rendering and resume at segment boundaries.
- Never produce a corrupted final artifact. Use atomic writes/renames.

SECURITY (NON-NEGOTIABLE)
- Never store OAuth tokens (access/refresh) in plaintext.
- Store secrets only in OS secure storage (Keychain on macOS) via the Rust keyring helper.
- Never log secrets. Add redaction tests.

REPO HYGIENE
- Do not commit generated artifacts (renders, encodes, bundles, caches, model weights, binaries).
- Keep output directories predictable and fully ignored by git.
- Use strict .gitignore and ensure scripts write only to approved output dirs.

TESTING DISCIPLINE
- Maintain a test pyramid: Unit (TS-###), Integration (IT-###), Acceptance (AT-###).
- Add/extend tests as you implement features.
- Every requirement (RQ-###) must map to tests (see docs/18-traceability-matrix.md).
- Update docs/STATUS.md after each completed milestone (phase gate).

TOOLCHAIN PINNING
- Pin and record versions for Godot, FFmpeg, Python worker deps, and schema versions.
- build_manifest.json must always reflect the exact toolchain used.

STOP CONDITIONS
- If Phase 1 determinism and segment-resume cannot be achieved, STOP and report the blocking issue in docs/STATUS.md with evidence (logs + failing tests).

# Codex Agent Rules (GPT-5.3-Codex Extra High Reasoning)

## 0) Authority and scope control
- `docs/**` is the contract. Do not invent requirements.
- If something required for implementation is missing, record an ASSUMPTION with an ID (ASM-###) in `docs/01-pinned-decisions.md` (or `docs/assumptions.md` if present) and proceed with the safest default.

## 1) Phase gating is mandatory
- Implement phases sequentially per `docs/20-phase-blueprint.md` and `docs/phases/phase-XX.md`.
- HARD GATE: Do not begin Phase N+1 until Phase N acceptance tests pass and Phase N “Definition of Done” is satisfied.

## 2) Traceability discipline
- Every requirement (RQ-###) must map to:
  - at least one module
  - exactly one or more phases
  - one or more tests (TS/IT/AT IDs)
- Keep `docs/18-traceability-matrix.md` current as you implement.

## 3) Repo hygiene and artifact policy
- No generated binaries or large renders committed.
- Use a dedicated output directory (e.g., `out/`) and ensure it is gitignored.
- Maintain `.gitignore` proactively.
- Remove temporary files after successful steps.

## 4) Architecture boundaries (no business logic in UI)
- UI: presentation only.
- Core: audio analysis, render orchestration, job queue, presets, mapping logic.
- Adapters: FFmpeg, filesystem, YouTube API, secure storage.
- If logic is needed in UI, create a core service API instead.

## 5) Determinism and reproducibility
- Pin tool/libraries where feasible and document versions.
- Use stable ordering, stable IDs, stable serialization.
- Where determinism cannot be guaranteed (GPU/render), define the determinism boundary explicitly and test within it.

## 6) Testing and verification
- For each phase implement unit + integration tests where feasible, plus acceptance tests exactly as specified.
- Always run and fix: lint → tests → build.
- Do not declare completion until acceptance tests pass.

## 7) Error handling and recovery
- Implement actionable error taxonomy across pipelines.
- Export jobs must support: progress, cancellation, and safe cleanup.
- YouTube operations must support: retry/backoff, quota-aware behavior, and safe degradation.

## 8) Security and secrets
- Never store OAuth tokens in plaintext.
- Use OS secure storage / keychain mechanisms per doc pack.
- Never log secrets or sensitive tokens.

## 9) Progress reporting
- Update `docs/STATUS.md` after each meaningful milestone:
  - completed tasks
  - failing tests
  - next actions
  - open risks/issues (must map to a phase or risk register item)

## 10) Conflict resolution
- If docs conflict, stop and document:
  - what conflicts
  - options
  - selected resolution and rationale
- Do not proceed until the conflict is resolved and reflected in docs.



```

## Human-readable implementation order (high-level)

1. Read in order:
   - `docs/01-pinned-decisions.md`
   - `docs/02-prd.md`
   - `docs/03-requirements.md`
   - `docs/20-phase-blueprint.md`
2. Scaffold repo structure (`docs/06-repo-structure.md`) and core contracts (`docs/07-module-contracts.md`).
3. Implement Phase 1 completely, including:
   - SQLite schema + migrations
   - Asset library + license provenance enforcement
   - Python analysis worker + caching
   - Mapping + presets
   - Motion Poster visual mode
   - Segment-based render/encode + bundle output
   - Tests: TS/IT + **AT-001**
4. Only then proceed to Phase 2, etc.

## What to update while implementing

- `docs/STATUS.md`:
  - Mark phase checkboxes as you complete and verify.
  - Record any necessary deviations as explicit, justified decisions (should be rare).
