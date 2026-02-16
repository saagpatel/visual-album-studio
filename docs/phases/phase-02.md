# Phase 2 — Visual Modes Expansion + Preset Hardening

## Objectives
- Expand from the single Phase 1 mode into a **diverse core visual mode set** while preserving:
  - deterministic offline rendering
  - preview ↔ export parity
  - stable parameter IDs and preset migrations

## Included modules / features
- **D** Beat-synced particles mode v1
- **E** Photo animator v1
  - Tier 0 (no ML)
  - optional Tier 1 (local ML opt-in)
- **F** Audio-to-3D landscape mode v1
- **H** Mapping + presets v2 (strict registry, semantic ranges, migrations)
- **J/K** Asset + preset governance improvements (provenance extended to ML models)

## Deliverables (testable)

### D1 — Particles mode v1 (RQ-013)
- 2D and/or 3D particle variant(s).
- Beat-reactive modulation via mapping system.
- 3+ distinct presets.

### D2 — Landscape mode v1 (RQ-016)
- Terrain/landscape shader with audio-reactive displacement.
- Camera path variants (orbit/flyover/static).
- 3+ grading presets.

### D3 — Photo animator v1 (RQ-014, RQ-015)
Tier 0 (mandatory):
- Ken Burns pan/zoom with deterministic interpolation.
- Manual depth/parallax tooling (mask or layer system).
- No ML required.

Tier 1 (optional):
- Local inference for depth estimation and segmentation:
  - ONNX Runtime with CoreML EP on macOS if available.
  - CPU fallback must work with explicit performance warnings.
- ML model download manager:
  - explicit user download
  - checksum verification
  - provenance + license recorded
  - models stored outside app bundle

### D4 — Mapping/presets v2 hardening (RQ-005, TS-003)
- Strict parameter registry:
  - stable IDs, types, ranges, descriptions
- Preset migration framework:
  - old presets can be migrated to newer schema versions
  - backward compatibility rules documented
- Validation tooling:
  - reject mappings referencing unknown params
  - reject presets with out-of-range values

### D5 — Governance improvements (anti-template-spam prep)
- Preset catalog includes “structural families”:
  - layout families
  - palette families
  - camera families
- These families feed Phase 4 guardrails.

## Acceptance criteria (measurable)

### A1 — Preview/export parity for all modes
- For each mode (G/D/F/E Tier 0):
  - preview capture and offline export are visually consistent within defined tolerances.
- No “different look” surprises when rendering offline.

### A2 — Determinism
- Golden projects per mode:
  - checkpoint frame hashes match across reruns on same machine/toolchain.

### A3 — Photo animator requirements
- Tier 0 works fully without ML models.
- Tier 1 (if enabled):
  - explicit download required
  - CPU fallback works
  - model provenance recorded in build manifest and provenance

### A4 — Preset migrations
- Migrating a preset to a new schema version preserves output within defined tolerances for golden projects.
  - Tolerance rules must be explicit (e.g., allow <1% pixel difference only when a deprecation is applied).

## Verification plan

### Automated
- Unit:
  - TS-002, TS-003, TS-005
  - TS-001/006 continue to run (no regressions)
- Integration:
  - IT-001 (worker) continues
  - optional: model download/inference integration tests
- Acceptance:
  - **AT-002**

### Manual checks
- Visual diversity rubric review for new presets.
- Performance sanity: render time for 10min export per mode recorded and compared.

## Dependencies / prerequisites
- Phase 1 must be stable:
  - export segmentation/resume
  - determinism harness
  - schema v1 migrations

## Risks + mitigation tasks
- ML licensing/distribution size:
  - require explicit downloads
  - store provenance + checksums
  - block production usage if license unknown
- GPU performance:
  - quality tiers and conservative defaults
  - avoid nondeterministic GPU features

## Explicit out-of-scope (deferred)
- B mixer (Phase 3)
- N/R automation (Phase 4)
- L/M YouTube (Phase 5)
- O/P/Q analytics/research/revenue (Phase 6)
