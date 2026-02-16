# Automation: Batch Generation & Remix (Phase 4)

Phase 4 adds automation without creating monetization-risk “mass-produced” output. Guardrails are mandatory.

## Goals
- Execute large batches reliably (100+ overnight) with crash recovery.
- Generate controlled variations via declarative remix rules.
- Enforce “minimum meaningful difference” between variants.
- Produce provenance and reviewer reports.

## Key concepts

### Variant graph (R)
A declarative graph that produces VariantSpecs from a base project/template/preset.

Variant knobs:
- seed variation
- palette / color grading preset
- typography variants (font/weight/layout)
- camera path variants (where applicable)
- audio swaps (Phase 4 assumes mixer exists from Phase 3)
- length variants (10s/30s/10m/2h) based on loop rules

### Batch plan (N)
A plan that schedules a set of exports (projects + VariantSpecs) over time.

Batch controls:
- max concurrent jobs
- overnight scheduling window
- retry limits + backoff
- disk space guard (pause when low)

## Architecture (job graph)

```text
BatchPlan (N)
  -> for each VariantSpec:
       (R) apply variant to base snapshot -> derived export snapshot
       (I) enqueue export job (segment render/encode)
       (I) finalize bundle
       (optional Phase 5) enqueue upload job
```

All operations are persisted jobs:
- batch orchestration job
- per-item export jobs
- per-item upload jobs (Phase 5)

## Variation strategies (authoritative)

### Seed strategy
- Seeds must be explicit and recorded per variant.
- Variation can use:
  - `seed = base_seed + variant_index` (stable)
  - or `seed = hash(base_seed, variant_id)` (stable)

### Controlled envelopes (avoid random soup)
Variants must differ along:
- **at least X parameters** (default X=5)
- **at least one structural change**, e.g.:
  - layout preset family changes (Motion Poster layout A vs B)
  - camera path change (Landscape)
  - particle emitter mode change (Particles)
  - typography system change (font family/weight/layout style)

### Length variants (loop rules)
- Length variants must respect loop logic:
  - if audio shorter than target, loop seamlessly (Phase 3 bounce)
  - do not arbitrarily truncate without fade out
- For multi-track mixes, loop regions must align to beat boundaries when configured.

## Guardrails (mandatory)

### Variant distance metric
Compute a distance score between two VariantSpecs based on:
- parameter ID deltas (normalized)
- categorical changes (layout family, palette family, camera path)
- asset changes (audio swap, album art swap)
- template changes

Distance policy:
- A variant is valid only if it passes:
  - `num_params_changed >= X`
  - `structural_change == true`
  - `distance_score >= threshold`

### Reviewer report
Batch execution must emit a report artifact:
- per variant:
  - seed
  - changed parameters (top N)
  - structural changes
  - asset changes
  - template/preset IDs
- summary statistics:
  - min/avg/max distance
  - any near-duplicates flagged

### Human rubric alignment
Provide a creator-facing rubric aligned to YouTube guidance:
- Are outputs meaningfully different?
- Is there evidence of original creative input?
- Are you relying on a single template with trivial changes?

## Provenance tracking
Each bundle’s provenance/originality ledger must include:
- base project snapshot hash
- variant graph ID
- variant spec ID
- distance score summary
- user notes (optional)

## Reliability requirements
- Batch of 100 overnight renders completes with:
  - <2% failure rate
  - failures recoverable via retry
  - no orphan temp files beyond configured threshold
- Job scheduling must detect:
  - low disk
  - machine sleep interruption
  - repeated failure loops (circuit breaker)

## Verification (Phase 4 acceptance AT-004)
- Synthetic batch stress suite:
  - generates 100 variants
  - runs export jobs under constrained disk/time
  - validates resume and cleanup
- Guardrails suite:
  - ensures near-duplicate variants are rejected or flagged
- Manual spot-check runbook:
  - reviewer uses rubric to validate visual diversity
