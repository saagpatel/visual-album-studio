# Visual Album Studio — Agent Instructions

<!-- comm-contract:start -->
## Communication Contract (Global)
- Follow `/Users/d/.codex/policies/communication/BigPictureReportingV1.md` for all user-facing updates.
- Keep default updates beginner-friendly, big-picture, and low-noise.
- Keep technical details in internal artifacts unless explicitly requested by the user.
- Honor toggles literally: `simple mode`, `show receipts`, `tech mode`, `debug mode`.
<!-- comm-contract:end -->
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

## UI Hard Gates (when UI scope changes)
1) Reviewer emits `UIFindingV1[]` from `/Users/d/.codex/contracts/UIFindingV1.schema.json`.
2) Fixer applies UI findings in order: `P0 -> P1 -> P2 -> P3`.
3) Required states: loading, empty, error, success, disabled, focus-visible.
4) Required UI gates: static lint/type/style, visual regression, a11y regression, responsive checks, and Lighthouse CI.
5) UI done-state is blocked if any required gate is `fail` or `not-run`.

## Codex Reliability Contract

### Canonical Verification Commands (Source of Truth)
Source: `.codex/verify.commands` (derived from `docs/00-readme.md` and `scripts/test/*`)
- lint: `N/A (no canonical lint command currently documented)`
- format-check: `N/A (no canonical format-check command currently documented)`
- typecheck: `N/A (no standalone typecheck command currently documented)`
- unit-test: `./scripts/test/unit.sh`
- integration-test: `./scripts/test/integration.sh`; `./scripts/test/security_audit.sh`; `./scripts/test/repo_hygiene_audit.sh`
- build: `N/A (build gate currently enforced through phase acceptance scripts)`

### Definition of Done
- All commands in `.codex/verify.commands` pass via `.codex/scripts/run_verify_commands.sh`.
- No open `critical` or `high` `ReviewFindingV1` findings.
- Diff scope matches approved task scope.
- Security checks (secrets, dependency, and SAST) are clean or explicitly waived with owner + expiry.

### Private Repo Guardrail
- GitHub branch protection is currently unavailable for this private repo plan.
- Install and keep the local guard active via `.codex/scripts/install-prepush-guard.sh`.
- Pushes to `main` must pass `.codex/scripts/run_verify_commands.sh` unless explicitly bypassed with `CODEX_BYPASS_PREPUSH=1` and documented rationale.

### Agent Contract
- Reviewer agent: read-only and emits only `ReviewFindingV1` findings.
- Fixer agent: applies accepted findings in severity order and reports exact file patches + verification.
- Final verifier: re-runs `.codex/scripts/run_verify_commands.sh` and summarizes `GateReportV1`.

## Definition of Done: Tests + Docs (Blocking)

- Any production code change must include meaningful test updates in the same PR.
- Meaningful tests must include at least:
  - one primary behavior assertion
  - two non-happy-path assertions (edge, boundary, invalid input, or failure mode)
- Trivial assertions are forbidden (`expect(true).toBe(true)`, snapshot-only without semantic assertions, render-only smoke tests without behavior checks).
- Mock only external boundaries (network, clock, randomness, third-party SDKs). Do not mock the unit under test.
- UI changes must cover state matrix: loading, empty, error, success, disabled, focus-visible.
- API/command surface changes must update generated contract artifacts and request/response examples.
- Architecture-impacting changes must include an ADR in `/docs/adr/`.
- Required checks are blocking when `fail` or `not-run`: lint, typecheck, tests, coverage, diff coverage, docs check.
- Reviewer -> fixer -> reviewer loop is required before merge.
