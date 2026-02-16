# Visual Album Studio — STATUS

**Project:** Visual Album Studio  
**Current state:** Not started  
**Last updated:** 2026-02-16

## Phase Plan (authoritative)

1. **Phase 1** — Local-only end-to-end production bundle (A, C, G, H, I, J, K)  
2. **Phase 2** — Visual modes expansion (D, E, F) + mapping/preset hardening  
3. **Phase 3** — Soundscape mixer + deterministic offline bounce (B)  
4. **Phase 4** — Automation: batch generation + remix + guardrails (N, R)  
5. **Phase 5** — Optional YouTube publishing + multi-channel (L, M)  
6. **Phase 6** — Analytics + niche + revenue (O, P, Q)

## Master Checklist (Codex maintains)

### Repo scaffolding
- [ ] Repo structure matches `docs/06-repo-structure.md`
- [ ] `.gitignore` blocks all generated artifacts (renders/exports/caches/models/binaries)
- [ ] Script entrypoints created:
  - [ ] `./scripts/bootstrap.*`
  - [ ] `./scripts/dev/run_editor.*`
  - [ ] `./scripts/test/unit.*`
  - [ ] `./scripts/test/integration.*`
  - [ ] `./scripts/test/acceptance_phase_01.*` … `acceptance_phase_06.*`

### Toolchain pinning
- [ ] Godot version pinned and recorded
- [ ] FFmpeg managed install pinned + checksum verified
- [ ] Python worker dependencies pinned (lock file) and recorded
- [ ] SQLite schema migrations versioned

### Cross-cutting non-negotiables
- [ ] Business logic separated from UI (core vs adapters vs UI)
- [ ] Export pipeline is segment-based, cancelable, resumable, crash-safe
- [ ] OAuth tokens never stored in plaintext; keychain/secure storage only
- [ ] Logs redact secrets and PII

## Phase Gate Checklists

### Phase 1 (AT-001)
- [ ] SQLite schema v1 locked + migrations apply cleanly
- [ ] Asset library v1: import + dedupe + license/provenance fields
- [ ] Audio analysis worker v1: BPM + beat grid cached
- [ ] Mapping/presets v1: stable parameter IDs
- [ ] Motion Poster mode v1: 6 distinct presets
- [ ] Export pipeline v1: segment render → encode → concat → bundle
- [ ] Determinism checks: checkpoint frame hashes stable
- [ ] Cancel/resume works at segment boundaries
- [ ] **AT-001 passes**

### Phase 2 (AT-002)
- [ ] Particle mode v1
- [ ] Landscape mode v1
- [ ] Photo animator Tier 0 (no ML) + optional Tier 1 (ML) scaffolding
- [ ] Mapping/presets v2: strict parameter registry + migrations
- [ ] **AT-002 passes**

### Phase 3 (AT-003)
- [ ] Mixer UI + persistence
- [ ] Offline bounce via FFmpeg filtergraph
- [ ] Loop-safe audio
- [ ] **AT-003 passes**

### Phase 4 (AT-004)
- [ ] Batch planner + executor
- [ ] Remix engine + variant graph
- [ ] Guardrails + variant distance checks
- [ ] Overnight batch reliability
- [ ] **AT-004 passes**

### Phase 5 (AT-005)
- [ ] OAuth installed-app flow (system browser + loopback)
- [ ] Secure token storage (keychain)
- [ ] Resumable upload with retry/backoff
- [ ] Metadata/thumbnail/playlists/scheduling
- [ ] Multi-channel safety guards
- [ ] Quota budgeting
- [ ] **AT-005 passes**

### Phase 6 (AT-006)
- [ ] Analytics dashboard + sync
- [ ] Reporting API bulk ingestion
- [ ] Revenue tracking + manual import fallback
- [ ] Niche analyzer + quota awareness
- [ ] Privacy tests (no tokens/PII in logs)
- [ ] **AT-006 passes**

## Assumptions made (append-only)

> None yet.
