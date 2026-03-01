# V2 Train 4 Threat Model and Ownership Map

## Scope
Train 4 cloud/collaboration scope (`RQ-V2-401..405`):
- Cloud sync queue/replay
- Collaboration RBAC and conflict resolution
- Versioned object storage references
- Outage fallback to local-only mode

## Assets and trust boundaries
1. Local project state and queued edits.
2. Sync envelopes (`SyncEnvelopeV1`) and replay logs.
3. Collaboration role assignments and conflict audit records.
4. Cloud object references and content checksums.

Trust boundaries:
1. Local runtime process boundary (Godot/core services).
2. Adapter boundary (`CloudSyncAdapter`, `ObjectStorageAdapter`) for cloud connectivity.
3. Persistence boundary (SQLite migration tables for queue/conflict/reference records).

## Threats and controls
| Threat | Control | Evidence |
|---|---|---|
| Cloud outage causes data loss | Queue-first local writes and explicit replay on recovery | `IT-V2-401`, `IT-V2-405`, `RT-V2-402`, `AT-V2-401` |
| Unauthorized collaborator edits | RBAC enforcement at collaboration service boundary | `TS-V2-401`, `IT-V2-402`, `AT-V2-401` |
| Non-deterministic conflict outcomes | Deterministic ranking rule with persisted conflict records | `TS-V2-402`, `IT-V2-403`, `RT-V2-401` |
| Corrupt or stale cloud object references | Versioned object metadata with checksum persistence | `TS-V2-403`, `IT-V2-404` |
| Sensitive diagnostics leakage | Existing redaction policy carry-forward for connector/sync diagnostics | `IT-V2-305`, security audit strict mode |

## Ownership map
- Program owner: `saagar210`
- Security owner: `saagar210`
- Risk owner (cloud sync/collab): `saagar210`
- Review cadence:
  - Weekly: outage/replay and provider policy drift checks
  - Monthly: residency and closeout-control revalidation

## Signoff
Train 4 threat model signoff recorded on `2026-03-01` with no unresolved blocking threat items for `AT-V2-401`.
