from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .ids import new_id


@dataclass
class SyncEnvelopeV1:
    project_id: str
    actor_id: str
    device_id: str
    sequence: int
    operation: str
    payload: dict[str, Any] = field(default_factory=dict)
    base_version: int = 0
    created_at: int = 0
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": int(self.schema_version),
            "project_id": self.project_id,
            "actor_id": self.actor_id,
            "device_id": self.device_id,
            "sequence": int(self.sequence),
            "operation": self.operation,
            "payload": dict(self.payload),
            "base_version": int(self.base_version),
            "created_at": int(self.created_at),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SyncEnvelopeV1":
        return cls(
            project_id=str(payload.get("project_id", "")),
            actor_id=str(payload.get("actor_id", "")),
            device_id=str(payload.get("device_id", "")),
            sequence=int(payload.get("sequence", 0)),
            operation=str(payload.get("operation", "")),
            payload=dict(payload.get("payload", {})),
            base_version=int(payload.get("base_version", 0)),
            created_at=int(payload.get("created_at", 0)),
            schema_version=int(payload.get("schema_version", 1)),
        )


@dataclass
class ConflictRecordV1:
    conflict_id: str
    project_id: str
    resource_id: str
    winner_actor_id: str
    winner_sequence: int
    loser_actor_id: str
    loser_sequence: int
    rule_id: str
    created_at: int
    details: dict[str, Any] = field(default_factory=dict)
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": int(self.schema_version),
            "conflict_id": self.conflict_id,
            "project_id": self.project_id,
            "resource_id": self.resource_id,
            "winner_actor_id": self.winner_actor_id,
            "winner_sequence": int(self.winner_sequence),
            "loser_actor_id": self.loser_actor_id,
            "loser_sequence": int(self.loser_sequence),
            "rule_id": self.rule_id,
            "created_at": int(self.created_at),
            "details": dict(self.details),
        }


class CloudSyncAdapter:
    def is_available(self) -> bool:
        raise NotImplementedError

    def push_envelope(self, envelope: SyncEnvelopeV1) -> dict[str, Any]:
        raise NotImplementedError

    def fetch_updates(self, project_id: str, since_sequence: int = 0) -> list[dict[str, Any]]:
        raise NotImplementedError


class InMemoryCloudSyncAdapter(CloudSyncAdapter):
    def __init__(self, available: bool = True):
        self._available = bool(available)
        self._events: dict[str, list[dict[str, Any]]] = {}

    def set_available(self, available: bool) -> None:
        self._available = bool(available)

    def is_available(self) -> bool:
        return self._available

    def push_envelope(self, envelope: SyncEnvelopeV1) -> dict[str, Any]:
        if not self._available:
            return {"ok": False, "error_code": "E_CLOUD_UNAVAILABLE", "retryable": True}
        project_events = self._events.setdefault(envelope.project_id, [])
        project_events.append(envelope.to_dict())
        return {"ok": True, "sequence": envelope.sequence}

    def fetch_updates(self, project_id: str, since_sequence: int = 0) -> list[dict[str, Any]]:
        events = self._events.get(project_id, [])
        return [dict(item) for item in events if int(item.get("sequence", 0)) > int(since_sequence)]


class ObjectStorageAdapter:
    def is_available(self) -> bool:
        raise NotImplementedError

    def put_object(self, *, project_id: str, object_key: str, data: bytes, schema_version: int) -> dict[str, Any]:
        raise NotImplementedError

    def get_metadata(self, *, project_id: str, object_key: str) -> dict[str, Any] | None:
        raise NotImplementedError


class LocalObjectStorageAdapter(ObjectStorageAdapter):
    def __init__(self, base_dir: Path | str, available: bool = True):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._available = bool(available)

    def set_available(self, available: bool) -> None:
        self._available = bool(available)

    def is_available(self) -> bool:
        return self._available

    def _path_for(self, project_id: str, object_key: str) -> Path:
        rel = str(object_key).lstrip("/")
        return self.base_dir / project_id / rel

    def put_object(self, *, project_id: str, object_key: str, data: bytes, schema_version: int) -> dict[str, Any]:
        if not self._available:
            return {"ok": False, "error_code": "E_CLOUD_STORAGE_UNAVAILABLE", "retryable": True}
        path = self._path_for(project_id, object_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        checksum = hashlib.sha256(data).hexdigest()
        storage_ref = f"local://{project_id}/{object_key}?schema_version={int(schema_version)}"
        return {
            "ok": True,
            "storage_ref": storage_ref,
            "path": str(path),
            "checksum": checksum,
            "size_bytes": len(data),
            "schema_version": int(schema_version),
        }

    def get_metadata(self, *, project_id: str, object_key: str) -> dict[str, Any] | None:
        path = self._path_for(project_id, object_key)
        if not path.exists():
            return None
        payload = path.read_bytes()
        return {
            "path": str(path),
            "checksum": hashlib.sha256(payload).hexdigest(),
            "size_bytes": len(payload),
        }


class CollaborationService:
    _ALLOWED_ROLES = {"owner", "editor", "viewer"}
    _ROLE_ACTIONS = {
        "owner": {"view", "edit", "sync", "resolve_conflict"},
        "editor": {"view", "edit", "sync"},
        "viewer": {"view"},
    }

    def __init__(
        self,
        db,
        sync_adapter: CloudSyncAdapter | None = None,
        storage_adapter: ObjectStorageAdapter | None = None,
    ):
        self.db = db
        self.sync_adapter = sync_adapter or InMemoryCloudSyncAdapter(available=True)
        self.storage_adapter = storage_adapter or LocalObjectStorageAdapter(Path("out/cloud_storage"))

    @staticmethod
    def _now() -> int:
        return int(time.time())

    def set_member_role(self, *, project_id: str, user_id: str, role: str) -> dict[str, Any]:
        role = str(role).strip().lower()
        if role not in self._ALLOWED_ROLES:
            return {"ok": False, "error_code": "E_ROLE_INVALID", "role": role}
        now = self._now()
        self.db.execute(
            """
            INSERT OR REPLACE INTO collaboration_members(project_id, user_id, role, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (project_id, user_id, role, now),
        )
        self.db.commit()
        return {"ok": True, "project_id": project_id, "user_id": user_id, "role": role}

    def get_member_role(self, *, project_id: str, user_id: str) -> str:
        row = self.db.execute(
            "SELECT role FROM collaboration_members WHERE project_id = ? AND user_id = ?",
            (project_id, user_id),
        ).fetchone()
        if not row:
            return "viewer"
        return str(row["role"])

    def authorize(self, *, project_id: str, user_id: str, action: str) -> bool:
        role = self.get_member_role(project_id=project_id, user_id=user_id)
        return str(action) in self._ROLE_ACTIONS.get(role, set())

    def _next_sequence(self, project_id: str) -> int:
        row = self.db.execute("SELECT last_sequence FROM cloud_sync_state WHERE project_id = ?", (project_id,)).fetchone()
        current = int(row["last_sequence"]) if row else 0
        sequence = current + 1
        self.db.execute(
            "INSERT OR REPLACE INTO cloud_sync_state(project_id, last_sequence, updated_at) VALUES (?, ?, ?)",
            (project_id, sequence, self._now()),
        )
        self.db.commit()
        return sequence

    def build_envelope(
        self,
        *,
        project_id: str,
        actor_id: str,
        device_id: str,
        operation: str,
        payload: dict[str, Any] | None = None,
        base_version: int = 0,
        sequence: int | None = None,
    ) -> SyncEnvelopeV1:
        return SyncEnvelopeV1(
            project_id=project_id,
            actor_id=actor_id,
            device_id=device_id,
            sequence=sequence if sequence is not None else self._next_sequence(project_id),
            operation=operation,
            payload=dict(payload or {}),
            base_version=base_version,
            created_at=self._now(),
        )

    def queue_local_edit(
        self,
        *,
        project_id: str,
        user_id: str,
        device_id: str,
        operation: str,
        payload: dict[str, Any] | None = None,
        base_version: int = 0,
    ) -> dict[str, Any]:
        if not self.authorize(project_id=project_id, user_id=user_id, action="edit"):
            return {"ok": False, "error_code": "E_COLLAB_FORBIDDEN", "mode": self.sync_mode()}

        envelope = self.build_envelope(
            project_id=project_id,
            actor_id=user_id,
            device_id=device_id,
            operation=operation,
            payload=payload,
            base_version=base_version,
        )
        queue_id = new_id("syncq")
        now = self._now()
        self.db.execute(
            """
            INSERT INTO cloud_sync_queue(id, project_id, envelope_json, status, error_code, created_at, updated_at)
            VALUES (?, ?, ?, 'queued', '', ?, ?)
            """,
            (queue_id, project_id, json.dumps(envelope.to_dict(), sort_keys=True), now, now),
        )
        self.db.commit()
        return {
            "ok": True,
            "queue_id": queue_id,
            "sequence": envelope.sequence,
            "mode": self.sync_mode(),
            "envelope": envelope.to_dict(),
        }

    def replay_queued(self, *, project_id: str) -> dict[str, Any]:
        queued = self.db.execute(
            """
            SELECT id, envelope_json
            FROM cloud_sync_queue
            WHERE project_id = ? AND status = 'queued'
            ORDER BY created_at ASC
            """,
            (project_id,),
        ).fetchall()
        if not self.sync_adapter.is_available():
            return {"ok": True, "mode": "local_only", "queued": len(queued), "replayed": 0}

        replayed = 0
        failed = 0
        for row in queued:
            queue_id = str(row["id"])
            envelope = SyncEnvelopeV1.from_dict(json.loads(row["envelope_json"]))
            result = self.sync_adapter.push_envelope(envelope)
            now = self._now()
            if result.get("ok"):
                replayed += 1
                self.db.execute(
                    "UPDATE cloud_sync_queue SET status = 'replayed', updated_at = ? WHERE id = ?",
                    (now, queue_id),
                )
                self.db.execute(
                    """
                    INSERT INTO cloud_sync_replay_log(id, project_id, queue_id, sequence, status, detail_json, created_at)
                    VALUES (?, ?, ?, ?, 'succeeded', ?, ?)
                    """,
                    (
                        new_id("sync_replay"),
                        project_id,
                        queue_id,
                        envelope.sequence,
                        json.dumps(result, sort_keys=True),
                        now,
                    ),
                )
            else:
                failed += 1
                error_code = str(result.get("error_code", "E_SYNC_PUSH_FAILED"))
                self.db.execute(
                    "UPDATE cloud_sync_queue SET status = 'failed', error_code = ?, updated_at = ? WHERE id = ?",
                    (error_code, now, queue_id),
                )
                self.db.execute(
                    """
                    INSERT INTO cloud_sync_replay_log(id, project_id, queue_id, sequence, status, detail_json, created_at)
                    VALUES (?, ?, ?, ?, 'failed', ?, ?)
                    """,
                    (
                        new_id("sync_replay"),
                        project_id,
                        queue_id,
                        envelope.sequence,
                        json.dumps(result, sort_keys=True),
                        now,
                    ),
                )
            self.db.commit()
        return {"ok": failed == 0, "mode": "cloud_online", "queued": len(queued), "replayed": replayed, "failed": failed}

    @staticmethod
    def _rank(envelope: SyncEnvelopeV1) -> tuple[int, str, str]:
        payload_hash = hashlib.sha256(json.dumps(envelope.payload, sort_keys=True).encode("utf-8")).hexdigest()
        return (int(envelope.sequence), envelope.actor_id, payload_hash)

    def resolve_conflict(
        self,
        *,
        project_id: str,
        resource_id: str,
        local_envelope: SyncEnvelopeV1,
        remote_envelope: SyncEnvelopeV1,
    ) -> dict[str, Any]:
        if self._rank(local_envelope) >= self._rank(remote_envelope):
            winner = local_envelope
            loser = remote_envelope
        else:
            winner = remote_envelope
            loser = local_envelope

        now = self._now()
        conflict = ConflictRecordV1(
            conflict_id=new_id("conflict"),
            project_id=project_id,
            resource_id=resource_id,
            winner_actor_id=winner.actor_id,
            winner_sequence=winner.sequence,
            loser_actor_id=loser.actor_id,
            loser_sequence=loser.sequence,
            rule_id="prefer_newer_sequence_then_actor_then_payload_hash",
            created_at=now,
            details={
                "winner_operation": winner.operation,
                "loser_operation": loser.operation,
                "winner_payload": winner.payload,
                "loser_payload": loser.payload,
            },
        )
        self.db.execute(
            """
            INSERT INTO collaboration_conflicts(
              id, project_id, resource_id, winner_actor_id, winner_sequence, resolution_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conflict.conflict_id,
                project_id,
                resource_id,
                conflict.winner_actor_id,
                conflict.winner_sequence,
                json.dumps(conflict.to_dict(), sort_keys=True),
                now,
            ),
        )
        self.db.commit()
        return {"ok": True, "conflict": conflict.to_dict()}

    def store_object_reference(
        self,
        *,
        project_id: str,
        object_key: str,
        data: bytes,
        schema_version: int = 1,
    ) -> dict[str, Any]:
        stored = self.storage_adapter.put_object(
            project_id=project_id,
            object_key=object_key,
            data=data,
            schema_version=schema_version,
        )
        if not stored.get("ok"):
            return {"ok": False, "error_code": stored.get("error_code", "E_STORAGE_FAILED"), "mode": self.sync_mode()}

        now = self._now()
        self.db.execute(
            """
            INSERT OR REPLACE INTO cloud_objects(
              id, project_id, object_key, schema_version, storage_ref, checksum, size_bytes, created_at, updated_at
            ) VALUES (
              COALESCE((SELECT id FROM cloud_objects WHERE project_id = ? AND object_key = ?), ?),
              ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM cloud_objects WHERE project_id = ? AND object_key = ?), ?), ?
            )
            """,
            (
                project_id,
                object_key,
                new_id("cloud_obj"),
                project_id,
                object_key,
                int(schema_version),
                str(stored["storage_ref"]),
                str(stored["checksum"]),
                int(stored["size_bytes"]),
                project_id,
                object_key,
                now,
                now,
            ),
        )
        self.db.commit()
        return {
            "ok": True,
            "project_id": project_id,
            "object_key": object_key,
            "schema_version": int(schema_version),
            "storage_ref": str(stored["storage_ref"]),
            "checksum": str(stored["checksum"]),
            "size_bytes": int(stored["size_bytes"]),
        }

    def object_reference(self, *, project_id: str, object_key: str) -> dict[str, Any] | None:
        row = self.db.execute(
            """
            SELECT project_id, object_key, schema_version, storage_ref, checksum, size_bytes, created_at, updated_at
            FROM cloud_objects
            WHERE project_id = ? AND object_key = ?
            """,
            (project_id, object_key),
        ).fetchone()
        if not row:
            return None
        return dict(row)

    def sync_mode(self) -> str:
        return "cloud_online" if self.sync_adapter.is_available() else "local_only"
