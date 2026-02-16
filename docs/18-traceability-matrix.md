# Traceability Matrix (RQ → Modules → Phases → Tests)

This matrix is the authoritative traceability map.

Legend:
- Modules are A–T (see `docs/07-module-contracts.md`)
- Phases are numeric (1..7)
- Tests:
  - TS-### unit tests
  - IT-### integration tests
  - AT-### phase acceptance gates

## Matrix

| RQ ID | Requirement | Module(s) | Phase(s) | Test IDs |
|---|---|---|---:|---|
| RQ-001 | Local-first desktop editor; offline capable by default | C, J | 1, 2, 3, 4, 5, 6, 7 | AT-001, TS-004 |
| RQ-002 | Import audio files and normalize into a canonical WAV cache | A, J | 1 | TS-001, IT-001, AT-001 |
| RQ-003 | Compute BPM + beat grid + persistent analysis cache | A, J | 1, 3 | IT-001, TS-008, AT-001 |
| RQ-004 | One production-grade visual mode in Phase 1 | C, G | 1 | AT-001, TS-003 |
| RQ-005 | Map audio features → visual parameters with stable parameter IDs | H, A, C | 1, 2, 3, 4 | TS-002, TS-003, AT-001, AT-002 |
| RQ-006 | Real-time preview consistent with offline render | C, H | 1, 2 | AT-001, AT-002, IT-003 |
| RQ-007 | Offline render supports 10s–2h+ reliably | I, C | 1, 2, 3, 4 | AT-001, IT-003 |
| RQ-008 | Export bundle: MP4 + thumbnail + metadata JSON | I, K | 1, 2, 3, 4, 5 | TS-005, AT-001 |
| RQ-009 | Crash-safe render queue with progress + cancel | I | 1, 2, 3, 4 | TS-004, IT-002, AT-001 |
| RQ-010 | Segment-based resume for long renders | I | 1, 2, 3, 4 | IT-003, AT-001 |
| RQ-011 | Asset metadata supports license provenance and attribution notes | J | 1, 2, 3, 4, 5, 6, 7 | TS-006, AT-001 |
| RQ-012 | Templates: per-channel default title/description/tags schemas | K | 1, 4, 5 | IT-005, AT-001, AT-004 |
| RQ-013 | Beat-synced particle mode | D, C, H | 2 | AT-002 |
| RQ-014 | Photo animator supports non-ML tier (manual depth/parallax) | E, C | 2 | AT-002 |
| RQ-015 | Photo animator supports optional local ML tier (depth/segment) | E | 2 | AT-002, IT-001 |
| RQ-016 | Landscape mode with audio-reactive geometry | F, C, H | 2 | AT-002 |
| RQ-017 | Mixer supports multi-track soundscape projects | B | 3 | AT-003 |
| RQ-018 | Offline bounce to WAV is deterministic and loop-safe | B, I | 3 | AT-003, IT-002 |
| RQ-019 | Batch generation can generate N variations overnight | N, I, K | 4 | AT-004 |
| RQ-020 | Remix engine can swap audio, vary length, grade visuals | R, A, B, C, H, I | 4 | AT-004, TS-007 |
| RQ-021 | Batch guardrails prevent low-variation template spam | N, R, K | 4 | TS-007, AT-004 |
| RQ-022 | OAuth installed-app authorization via system browser | L | 5 | AT-005, IT-004 |
| RQ-023 | Resumable uploads for large files | L | 5 | AT-005, IT-006 |
| RQ-024 | Upload video with metadata (title/desc/tags/category/privacy) | L | 5 | AT-005 |
| RQ-025 | Upload custom thumbnail | L | 5 | AT-005 |
| RQ-026 | Schedule publish time | L | 5 | AT-005, TS-004 |
| RQ-027 | Add to playlists / manage playlists | L | 5 | AT-005 |
| RQ-028 | Multi-channel profiles with explicit channel binding | M, L, K | 5 | AT-005 |
| RQ-029 | Local analytics dashboard with official APIs only | P | 6 | AT-006 |
| RQ-030 | Bulk analytics ingestion for historical storage | P | 6 | AT-006, IT-007 |
| RQ-031 | Revenue tracking with graceful data-unavailable UX | Q | 6 | AT-006 |
| RQ-032 | Niche analyzer is quota-aware and supports manual workflows | O | 6 | AT-006, TS-010 |
| RQ-033 | Export bundles record pinned toolchain versions and schema versions | I, C, A, H, K | 1, 2, 3, 4, 5, 6, 7 | TS-005, AT-001 |
| RQ-034 | Managed FFmpeg strategy with checksum verification and license mode tracking | I | 1, 2, 3, 4, 5, 6, 7 | IT-002, TS-005, AT-001 |
| RQ-035 | Determinism harness with checkpoint frame hashing | C, I, H | 1, 2, 3, 4 | TS-005, AT-001, AT-002 |
| RQ-036 | Job queue persistence, crash recovery, and resume semantics | I, A, L, P, N, R | 1, 2, 3, 4, 5, 6, 7 | TS-004, AT-001 |
| RQ-037 | Workspace isolation and cleanup policy for renders/exports | I, J | 1, 2, 3, 4 | IT-003, AT-001 |
| RQ-038 | Secure storage adapter using OS keychain/secure storage (no plaintext tokens) | L, M | 5, 6 | IT-004, AT-005 |
| RQ-039 | Privacy-first logging and diagnostics with redaction | C, I, L, P | 1, 2, 3, 4, 5, 6, 7 | TS-004, AT-001, AT-005 |
| RQ-040 | SQLite schema migrations with forward-only versioning | J | 1, 2, 3, 4, 5, 6, 7 | TS-008, AT-001 |
| RQ-041 | Immutable export snapshots for rerenderability | I, J, H, K | 1, 2, 3, 4, 5, 6, 7 | IT-003, AT-001 |
| RQ-042 | Template variable engine for metadata and on-canvas typography | K, G, C | 1, 4, 5 | IT-005, AT-001 |
| RQ-043 | Deterministic, YouTube-valid thumbnail generation | I, C | 1, 2, 3, 4, 5 | TS-005, AT-001 |
| RQ-044 | Production export gating enforces audio license provenance completeness | J, I | 1, 2, 3, 4, 5, 6, 7 | TS-006, AT-001 |
| RQ-045 | Originality ledger per export (anti-template-spam support) | K, R, N, I | 1, 4 | AT-001, AT-004 |
| RQ-046 | Unified progress reporting using FFmpeg -progress and render progress events | I | 1, 2, 3, 4, 5, 6, 7 | IT-002, AT-001 |
| RQ-047 | ML model download manager with provenance and version pinning | E, J | 2 | AT-002 |
| RQ-048 | Multi-process architecture keeps editor responsive during heavy work | A, I, L | 1, 2, 3, 4, 5, 6, 7 | IT-001, IT-003, AT-001 |
| RQ-049 | Configuration, profiles, and data directory conventions are explicit and portable | J, I | 1, 2, 3, 4, 5, 6, 7 | TS-004, AT-001 |
| RQ-050 | Export presets are versioned; determinism boundaries are documented and enforced | I, K, C | 1, 2, 3, 4, 5, 6, 7 | TS-005, AT-001 |
| RQ-051 | Quota budgeting and quota-aware scheduling for YouTube operations | L, N, M | 5, 6 | TS-010, AT-005 |
| RQ-052 | Audit readiness checklist and manual-publish fallback artifacts | L, K, J | 5 | AT-005 |
| RQ-053 | Disk usage management and cache pruning | J, I, A | 1, 2, 3, 4, 6 | AT-001, AT-006 |
| RQ-054 | Backup/restore for local database and managed library | J | 6 | AT-006 |
| RQ-055 | Asset integrity verification and relink workflow | J | 1, 2, 3, 4, 5, 6, 7 | TS-001, AT-001 |
| RQ-056 | UX design system and component standardization | S, C | 7 | TS-011, AT-007 |
| RQ-057 | First-run onboarding and readiness checks | S, C, I, J | 7 | IT-008, AT-007 |
| RQ-058 | Guided workflow for import/preset/export | S, H, I, J, K | 7 | TS-012, IT-009, AT-007 |
| RQ-059 | Export command center with recoverability UX | S, I | 7 | IT-009, AT-007 |
| RQ-060 | Asset/provenance health and relink wizard UX | S, J, I | 7 | IT-010, AT-007 |
| RQ-061 | Preset browser/diff/migration UX | S, H, K | 7 | IT-011, AT-007 |
| RQ-062 | Accessibility baseline (keyboard/contrast/reduced motion) | S, C | 7 | TS-014, IT-012, AT-007 |
| RQ-063 | Command palette and productivity shortcuts | S | 7 | TS-013, AT-007 |
| RQ-064 | Diagnostics export and in-app troubleshooting runbooks | T, S, I, L, P | 7 | TS-015, AT-007 |
| RQ-065 | Packaging/update readiness architecture | T, I, J | 7 | TS-016, AT-007 |
| RQ-066 | UI responsiveness and performance instrumentation | S, C, I | 7 | IT-012, AT-007 |

## Coverage guarantees
- Every RQ-### maps to at least one test ID.
- Acceptance tests (AT-###) are phase gates and must pass before proceeding.
