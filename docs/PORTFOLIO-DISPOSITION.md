# visual-album-studio (VAS) — Portfolio Disposition

**Status:** Release Frozen — Python local-first music-synced video
generation pipeline on `origin/main`. **V1 and V2 are complete per
operator's own README**, with frame-accurate deterministic resumable
exports, BLAKE3 content-hash verification, SQLite migrations, and
distribution adapters for Facebook Reels and X. Long backlog of
security-hardening + verification-cadence commits indicates serious
release discipline. **Introduces a new disposition sub-shape:
local-first pipeline tool with distribution adapters.**

> Disposition uses strict `origin/main` verification.
> README explicitly declares V1 + V2 complete with a `next-cycle`
> roadmap for future scope — Release Frozen is the right call.

---

## Verification posture

This repo has both `origin` (`saagpatel/visual-album-studio`) and
`legacy-origin` (`saagar210/visual-album-studio`) remotes. **Local
clone's `main` is tracking `origin/main` correctly** — no trap.

Specifically verified on `origin/main`:

- Substantive commits on `origin/main` (sample of many):
  - `cf79c6e` feat(distribution): add facebook reels and x adapters (#27)
  - `768a764` feat(next-cycle): complete NC remaining action items (#39)
  - `0031984` feat(next-cycle): kick off control plane and nc-003 (#38)
  - `ebec093` feat(postv2): complete remaining backlog waves (#28)
  - `c427cc2` feat(models): close PV2-001 wave1 selection hardening (#26)
  - `df49e94` feat(models): start PV2-001 adaptive auto-selection (#18)
  - `db96020` feat(v2): complete trains 3-5 and closeout artifacts (#16)
  - `8df0022` feat(v2): implement train2 model registry and gate suites (#13)
  - `4682874` feat(train1): implement signed release promotion workflow
  - **Heavy `fix(security):` + `fix(hardening):` cadence** —
    `4a4f718`, `d920ca4`, `38dac43`, `cbf4698`, `409b09b`, etc.
- Tree on `origin/main`:
  - `app/` — Python application code
  - `worker/` — background worker(s)
  - `native/` — likely native bridge / FFI helpers
  - `openapi/` — OpenAPI spec(s)
  - `migrations/` — SQLite migrations
  - `tools/`, `scripts/`, `docs/`, `.codex/`
- Release scaffolding: `feat(train1): implement signed release
  promotion workflow` indicates a release promotion pipeline exists
  on canonical main
- Default branch: `main`

---

## Legacy-origin orphan note

`legacy-origin/main` orphans not assessed in this pass (operator
can run `git log origin/main..legacy-origin/main --oneline` to
check). Given the long substantive history on `origin/main`, legacy
orphans are likely low-stakes — but worth a sweep before next
session.

---

## Current state in one paragraph

Visual Album Studio is a Python 3.11+ local-first desktop pipeline
for generating music-synced visual videos. Per README: frame-accurate
deterministic exports, resumable across pipeline interruptions,
BLAKE3 content-hash verification for output integrity, SQLite for
state with migrations directory, pytest at three levels (unit,
integration, acceptance). V1 and V2 are both complete per the
operator's own README, with a `next-cycle` roadmap covering provider
policy watching, anomaly auto-triage, and scheduler simulation
overlays. Distribution adapters for **Facebook Reels** and **X** ship
on canonical main (commit `cf79c6e`). The commit history shows a
release discipline that's heavier than most cluster members —
signed-release-promotion workflow, model registry + gate suites,
phase 4-6 verification hardening, scope-diagnostic-hardening,
secret/token handoff hardening, and an explicit
`VAS_SECURITY_STRICT=1` env mode for strict verification.

For full detail see:
- `README.md` on `origin/main`
- `docs/` on `origin/main`
- `openapi/` for the service-side surface

---

## Why "Release Frozen" instead of other dispositions

- **Active** — wrong. README explicitly says "V1 and V2 are complete"
  and positions `next-cycle` as future scope, not current.
- **Cold Storage / Archived** — wrong. Recent commit cadence is
  active; this is a maintained product.
- **Release Frozen** — correct. V1 + V2 shipped, signed-release-
  promotion workflow exists, security-hardening backlog has been
  closing.

This is a **new sub-shape** in the cluster taxonomy: **local-first
pipeline tool with distribution adapters**. Different from:

- **Signing cluster** — no Tauri/Rust desktop shell, doesn't need
  Apple notarization
- **Static-host cluster** — runs a real pipeline, not a static SPA
- **Self-hosted service cluster** — no long-running daemon model;
  operator triggers pipeline runs

The closest fit is **operator-tool / local-CLI shape** — operator
runs pipelines locally to generate videos, then dispatches via the
distribution adapters to social platforms.

---

## Unblock trigger (operator)

When ready to ship:

1. **Decide distribution model.** Four options:
   - Operator-personal use only (current default-friendly stance)
   - Open-source as a community tool (the OpenAPI spec is on
     canonical main — implies external integration was contemplated)
   - SaaS/hosted (would require rebuilding the local-first
     architecture — large refactor, lower fit)
   - Paid CLI license (would require LemonSqueezy-style
     integration analogous to RealEstate; not present today)
2. **Audit Facebook Reels + X adapter credentials.** Distribution
   adapters need operator-supplied OAuth/API tokens. The strict-
   mode flag (`VAS_SECURITY_STRICT=1`) plus the long token-handoff
   hardening commit history suggest this is taken seriously.
3. **Confirm next-cycle scope.** The roadmap mentions provider
   policy watching, anomaly auto-triage, scheduler simulation
   overlays — operator picks which (if any) land in v3.
4. Tag v2.0 release per the signed-release-promotion workflow
   (`feat(train1): implement signed release promotion workflow`).

Estimated operator time: ~3 hours including credential audit and
release-promotion run.

---

## Portfolio operating system instructions

| Aspect | Posture |
|---|---|
| Portfolio status | `Release Frozen (local-first pipeline)` |
| Distribution model | **Operator runs pipeline locally**; distribution adapters publish to Facebook Reels + X |
| Review cadence | Suspend overdue counting |
| Resurface conditions | (a) Operator picks distribution model, (b) Facebook/X adapter credentials audited, (c) operator opens next-cycle scope packet |
| Do **not** auto-add to signing cluster | No desktop shell needing Apple notarization |
| Do **not** auto-add to static-host cluster | Runs a real pipeline, not a static SPA |
| Do **not** auto-add to self-hosted service cluster | No long-running daemon; operator triggers runs |
| **New sub-shape** | **Local-first pipeline tool with distribution adapters.** First member. Future similar repos (Python CLI + social platform adapters) batch here. |
| Special concern | **Distribution adapter credentials.** Facebook Reels + X tokens must be production-ready before public release. |
| Special concern | **Strict-mode flag.** `VAS_SECURITY_STRICT=1` should be the default for release builds, per the heavy security-hardening commit history. |

---

## Why this row introduces another sub-shape

The session's existing clusters don't quite fit:

| Sub-shape | Fit | Reasoning |
|---|---|---|
| Signing | No | No Tauri/Rust desktop shell |
| Static-host | No | Pipeline, not static SPA |
| Self-hosted service | Partial | Has `worker/` but no obvious daemon |
| Active awaiting product decision | No | V1+V2 declared complete by operator |
| **Local-first pipeline tool (new)** | **Yes** | Operator runs pipeline locally, distribution adapters publish to external platforms |

The OpenAPI spec on canonical main hints that some service-side
surface was contemplated — if that's ever exposed, this could
shift toward self-hosted service. For now it's local-first.

---

## Reactivation procedure (for the next code session)

1. Verify `git branch -vv` shows `main` tracking `origin/main`.
   Already correct as of this disposition pass.
2. Review the local stash (`r10-vas-stash`) — contains any
   uncommitted work from before this pass.
3. `git log origin/main..legacy-origin/main --oneline` — check
   for legacy orphans this disposition pass deferred.
4. Re-run `pip install -r app/requirements.txt && pytest` to
   confirm toolchain.
5. Run `VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh`
   to confirm strict-mode verification still green.
6. **Pick distribution model and audit adapter credentials before
   any next-cycle scope.**

---

## Last known reference

| Field | Value |
|---|---|
| Default branch | `main` |
| Build system | Python 3.11+ (custom `vas_studio` pipeline engine) + SQLite + BLAKE3 content hashing |
| Phases shipped | V1 + V2 complete (per operator README) plus `next-cycle` initial waves |
| Distribution adapters | **Facebook Reels** + **X** (commit `cf79c6e`) |
| Release scaffolding | `feat(train1): implement signed release promotion workflow` — promotion pipeline exists on `origin/main` |
| Security cadence | Heavy — multiple `fix(security):` and `fix(hardening):` waves, `VAS_SECURITY_STRICT=1` env flag |
| Testing posture | pytest at three levels (unit, integration, acceptance) |
| Blocker | Distribution model decision + Facebook/X adapter credential audit (operator-only) |
| Migration state | `legacy-origin` present but local tracking is correct; orphan sweep deferred |
| Distinguishing feature | **Local-first pipeline + distribution adapters** — new sub-shape. Operator runs pipeline locally, adapters publish to social platforms. |
