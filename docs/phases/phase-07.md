# Phase 7 — UX Excellence, Productization, and Post-v1 Velocity (Draft)

> Status: **Draft proposal only**.  
> Governance: This phase is **post-v1** and **non-authoritative** until explicitly added to `docs/01-pinned-decisions.md` and `docs/20-phase-blueprint.md` as a gated phase.

## Objectives
- Raise overall user experience quality from "powerful but technical" to "confident, fast, and approachable."
- Reduce time-to-value for first-time users while improving throughput for expert users.
- Improve operational polish for real-world usage:
  - packaging and update path readiness
  - failure recovery UX
  - support diagnostics and runbooks
- Preserve all hard constraints from Phases 1-6:
  - deterministic export behavior
  - segment-based resume
  - local-first architecture boundaries
  - secure token handling and redaction

## Phase outcome targets (measurable)
- First successful export by a new user in <= 10 minutes from install.
- Median clicks for common workflows reduced by >= 30%:
  - import audio + image + preset + export
  - duplicate template and retarget project metadata
- Keyboard-only completion for top 15 workflows.
- Zero regressions in `AT-001..AT-006`.
- New `AT-007` passes with UX + reliability acceptance scenarios.

## Scope definition

### Must-have
- UX foundations (design tokens, reusable components, interaction states).
- First-run onboarding and guided setup checks.
- Workflow acceleration for import, preset selection, and export setup.
- Export command center UX with better diagnostics and guided recovery.
- Accessibility baseline:
  - keyboard navigation
  - focus indicators
  - color contrast compliance
  - reduced-motion support
- Packaging + update-ready operational spec and implementation stubs.
- User-facing diagnostics export and troubleshooting runbooks.

### Should-have
- In-app command palette and global quick actions.
- Workspace layouts with "Creator" and "Operations" presets.
- Undo/redo expansion for project-wide operations.
- "Safe mode" startup for corrupted project/session recovery.

### Could-have
- In-app contextual tips system with progressive disclosure.
- Productivity telemetry (local-only, opt-in) for workflow friction analysis.
- AI-assisted copy suggestions for title/description templates (offline defaults first).

## Non-goals
- New rendering modes or novel visual engines (covered by prior phases).
- New external publishing providers beyond YouTube.
- Cloud sync or collaborative multi-user editing.
- Replacing core stack decisions (Godot/Python worker/Rust keyring).

## Included modules / feature areas
- **C** Visual engine foundation (editor UX shell improvements)
- **H/K** Mapping + templates UX and validation flows
- **I** Export pipeline operations UX and diagnostics
- **J** Asset management UX and integrity workflows
- **L/M** Publish UX hardening (safety and clarity improvements)
- **P/Q** Analytics/revenue dashboard UX polish
- **Proposed S (new)** UX platform module (design system + interaction framework)
- **Proposed T (new)** Productization module (packaging/update hooks + health reporting)

## Deliverables (testable)

### D1 — UX design system baseline
- Define and implement canonical UI tokens:
  - spacing scale, typography scale, color roles, semantic states
- Create reusable component primitives:
  - buttons, form fields, dropdowns, tabs, panels, notifications, progress rows, modal sheets
- Standardize interaction states:
  - loading, disabled, warning, error, success, recoverable-failure
- Add snapshot fixtures for core component states.

Definition of done:
- 100% of high-frequency screens use shared components and tokens.
- No legacy ad-hoc component copies on primary workflows.

### D2 — First-run onboarding and setup assistant
- Implement startup flow:
  - environment checks (FFmpeg availability, writable output dir, disk space sanity)
  - quick-start project generation with sample media references
  - explicit explanation of draft vs production export provenance behavior
- Implement "Readiness Panel":
  - green/yellow/red state with actionable fixes
  - one-click fix where safe

Definition of done:
- New user can reach first preview in <= 3 minutes.
- Readiness panel catches and explains common setup blockers.

### D3 — Workflow acceleration: import -> preset -> export
- Create a single guided workflow sidebar:
  - Step 1 import assets
  - Step 2 choose mode/preset
  - Step 3 validate metadata/provenance
  - Step 4 queue export
- Add quick actions:
  - "Use last export settings"
  - "Duplicate preset and retarget"
  - "Re-run last successful export"
- Add inline validation and "fix now" links for schema/provenance issues.

Definition of done:
- Common workflow is executable from one screen without deep navigation.
- Validation messages include direct remediation actions.

### D4 — Export Command Center UX
- Build a dedicated operations panel for all jobs:
  - queued/running/completed/failed filters
  - segment-level progress and ETA confidence
  - explicit cancel/resume controls
  - failure reason taxonomy surfaced in user language
- Add crash recovery affordance:
  - detect recoverable jobs at startup
  - offer one-click resume or cleanup options

Definition of done:
- Export failures are diagnosable in <= 2 interactions.
- Resume path is obvious and consistent for interrupted jobs.

### D5 — Asset library and provenance UX upgrades
- Add asset health badges:
  - integrity ok
  - missing source
  - relink required
  - provenance incomplete
- Add guided relink wizard with candidate path suggestions.
- Improve provenance editor:
  - field-level guidance
  - required-fields checklist for production exports

Definition of done:
- User can resolve missing asset links without manual DB edits.
- Provenance completion rate for production exports improves materially.

### D6 — Preset/template management UX
- Add preset browser with filter/sort/search by mode and tag.
- Add side-by-side preset diff:
  - parameter deltas
  - compatibility warnings
- Add explicit migration path UI for preset schema versions.

Definition of done:
- Preset migration failures present clear one-step remediation paths.
- Preset selection latency remains acceptable on large libraries.

### D7 — Accessibility and inclusivity baseline
- Keyboard navigation map for all core screens.
- WCAG-style contrast checks for text and critical status indicators.
- Focus ring visibility and logical tab order enforcement.
- Reduced motion mode support for animated UI transitions.
- Screen-reader-friendly labels for core controls where supported.

Definition of done:
- Accessibility checklist passes for all Phase 1-6 critical workflows.
- No blocking keyboard traps in modal/dialog interactions.

### D8 — Command palette and productivity UX
- Add global command palette (`Cmd/Ctrl+K`) with fuzzy search.
- Include top operational commands:
  - new project
  - import assets
  - run export
  - resume failed job
  - open diagnostics
- Add recent actions and user-pinned actions.

Definition of done:
- Top 15 workflows are invokable via command palette.
- Keyboard-only power path is documented and tested.

### D9 — Diagnostics, runbooks, and supportability
- Add diagnostics bundle export:
  - redacted logs
  - build/toolchain summary
  - queue and migration state summary
  - recent failure signatures
- Add "Troubleshoot" panel linking to local runbooks:
  - disk-full
  - interrupted export
  - keyring unavailable
  - API quota/auth failures

Definition of done:
- Support package generation is one click and secrets are redacted.
- Runbooks are accessible from failure notifications.

### D10 — Packaging and update readiness
- Define and implement packaging hooks for macOS release flow:
  - app bundle assembly scripts
  - signing/notarization placeholders and validation checks
  - release artifact manifest format
- Add update-channel architecture stubs:
  - stable/beta/dev channels
  - rollback metadata

Definition of done:
- Packaging dry-run succeeds and emits deterministic manifest.
- Update architecture can be enabled later without refactoring core services.

### D11 — UX performance and responsiveness
- Measure and optimize editor responsiveness:
  - target < 100ms interaction response for common UI actions
  - asynchronous loading for heavy lists and project metadata
- Add cold-start and project-open timing instrumentation.

Definition of done:
- Measured p95 latency for key UI interactions meets target thresholds.
- No UI thread stalls caused by blocking I/O in core workflows.

### D12 — Documentation and enablement updates
- Create end-user guides:
  - first export walkthrough
  - reliability checklist
  - troubleshooting quick reference
- Update developer docs:
  - UX architecture conventions
  - component contribution guidelines

Definition of done:
- A junior engineer can implement new UI screens using documented patterns only.

## Proposed requirement set for Phase 7 (draft IDs)

> Note: these IDs are proposed for post-v1 planning and are not yet part of `docs/03-requirements.md`.

- **RQ-056** UX design system and component standardization.
- **RQ-057** First-run onboarding and readiness checks.
- **RQ-058** Guided workflow for import/preset/export.
- **RQ-059** Export command center with recoverability UX.
- **RQ-060** Asset/provenance health and relink wizard UX.
- **RQ-061** Preset browser/diff/migration UX.
- **RQ-062** Accessibility baseline (keyboard/contrast/reduced motion).
- **RQ-063** Command palette and productivity shortcuts.
- **RQ-064** Diagnostics export and in-app troubleshooting runbooks.
- **RQ-065** Packaging/update readiness architecture.
- **RQ-066** UI responsiveness and performance instrumentation.

## Acceptance criteria (measurable)

### A1 — Onboarding effectiveness
- 5/5 fresh-machine runs complete first successful export within <= 10 minutes.
- Setup readiness panel identifies missing dependencies with actionable steps.

### A2 — Workflow efficiency
- Import-to-queued-export flow requires <= 50% of prior navigation transitions.
- User can complete the flow entirely from the guided workflow sidebar.

### A3 — Operational clarity
- Failed export jobs expose root-cause category and remediation in the UI.
- Resume/cancel flows are discoverable without documentation lookup.

### A4 — Accessibility
- Keyboard-only path works for all critical operations.
- Contrast checks pass for all text and status badges in core screens.

### A5 — Reliability non-regression
- `AT-001..AT-006` remain green.
- New UX features do not bypass provenance or security constraints.

### A6 — Packaging readiness
- Packaging dry-run produces deterministic manifest output.
- Release artifact checklist is generated without manual edits.

## Verification plan

### Automated (proposed)
- Unit:
  - **TS-011** design token validation and component state snapshots
  - **TS-012** workflow wizard state transitions
  - **TS-013** command palette indexing and command dispatch
  - **TS-014** accessibility focus-order and keyboard navigation assertions
  - **TS-015** diagnostics redaction and bundle schema checks
  - **TS-016** packaging manifest generation determinism
- Integration:
  - **IT-008** end-to-end onboarding flow on clean environment
  - **IT-009** export command center recoverable failure UX
  - **IT-010** provenance relink wizard with missing assets
  - **IT-011** preset migration UI with mixed schema versions
  - **IT-012** accessibility smoke path across critical screens
- Acceptance:
  - **AT-007** UX + productization gate

### Manual validation runbook
- Compare pre/post click-path and elapsed time for top workflows.
- Conduct keyboard-only completion run for project create/import/export.
- Simulate common failures and confirm remediation UX:
  - disk pressure
  - interrupted export
  - keyring unavailable
  - publish quota exceeded

## Proposed AT-007 scenarios
- New-user first export completion from clean setup.
- Recover from interrupted export via command center in <= 3 interactions.
- Resolve missing asset relink and provenance warnings end-to-end.
- Execute top workflows using command palette + keyboard only.
- Generate diagnostics bundle and verify redaction.
- Packaging dry-run completion with deterministic manifest.

## Sequenced implementation plan (junior-executable)

### Step 0 — Branch and baseline
1. Create branch `codex/phase-07-ux-productization`.
2. Capture baseline UX timings for top workflows.
3. Freeze screenshots of current core screens for regression comparison.

### Step 1 — Foundation
1. Implement design tokens and component primitives.
2. Refactor high-frequency screens to consume shared components.
3. Add snapshot/unit coverage for shared states.

### Step 2 — Guided workflows
1. Build onboarding assistant and readiness panel.
2. Implement import/preset/export guided sidebar.
3. Add inline remediation links for common validation failures.

### Step 3 — Operations and recovery UX
1. Build export command center with job taxonomy and segment-level detail.
2. Add startup recovery prompts for interrupted jobs.
3. Link failure states to troubleshooting runbooks.

### Step 4 — Library/preset usability and accessibility
1. Build asset health badges and relink wizard.
2. Build preset browser/diff/migration UX.
3. Implement keyboard/focus/contrast/reduced-motion improvements.

### Step 5 — Productization + diagnostics
1. Implement diagnostics export UX + redacted support package.
2. Add packaging/update readiness scripts and dry-run checks.
3. Implement command palette and shortcut map.

### Step 6 — Performance + hardening
1. Instrument UI latency and startup timings.
2. Optimize blocking paths and list rendering.
3. Execute full regression + AT-007 + documentation updates.

## Dependencies and prerequisites
- Phase 1-6 completed and green.
- Stable component ownership and UI architecture boundaries.
- Existing acceptance and integration test harnesses available in CI/local.

## Risks and mitigation
- Risk: UX refactor introduces behavior regressions.
  - Mitigation: keep AT-001..AT-006 green on every merge.
- Risk: Accessibility work breaks visual consistency.
  - Mitigation: tokenized theming and contrast snapshot checks.
- Risk: Packaging complexity delays delivery.
  - Mitigation: phase packaging as dry-run first, release signing later.
- Risk: Scope expansion into new product features.
  - Mitigation: enforce non-goals and limit to UX/productization outcomes.

## Exit criteria
- `AT-007` passes.
- `AT-001..AT-006` pass without regressions.
- Proposed `RQ-056..RQ-066` mapped to modules and tests.
- Runbooks and user docs published and discoverable in-app.

## Explicit out-of-scope (for this draft phase)
- New rendering modes or ML-heavy visual pipelines.
- Additional external distribution platforms.
- Multi-user cloud collaboration.
