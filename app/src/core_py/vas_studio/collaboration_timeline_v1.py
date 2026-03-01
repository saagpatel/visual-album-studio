from __future__ import annotations

import json
import time
from typing import Any

from .ids import new_id


class CollaborationTimelineServiceV1:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def _now() -> int:
        return int(time.time())

    @staticmethod
    def _sort_key(event: dict[str, Any]) -> tuple[int, int, str]:
        return (int(event.get("sequence", 0)), int(event.get("created_at", 0)), str(event.get("event_id", "")))

    def build_timeline(
        self,
        *,
        project_id: str,
        actor_id: str | None = None,
        include_conflicts: bool = True,
    ) -> dict[str, Any]:
        events: list[dict[str, Any]] = []

        queued_rows = self.db.execute(
            """
            SELECT id, envelope_json, status, created_at, updated_at
            FROM cloud_sync_queue
            WHERE project_id = ?
            ORDER BY created_at ASC
            """,
            (project_id,),
        ).fetchall()
        for row in queued_rows:
            envelope = json.loads(row["envelope_json"])
            actor = str(envelope.get("actor_id", ""))
            if actor_id and actor != actor_id:
                continue
            events.append(
                {
                    "event_id": str(row["id"]),
                    "event_type": "sync_queue",
                    "status": str(row["status"]),
                    "actor_id": actor,
                    "operation": str(envelope.get("operation", "")),
                    "sequence": int(envelope.get("sequence", 0)),
                    "created_at": int(row["created_at"]),
                    "updated_at": int(row["updated_at"]),
                }
            )

        replay_rows = self.db.execute(
            """
            SELECT id, queue_id, sequence, status, detail_json, created_at
            FROM cloud_sync_replay_log
            WHERE project_id = ?
            ORDER BY created_at ASC
            """,
            (project_id,),
        ).fetchall()
        for row in replay_rows:
            detail = json.loads(row["detail_json"])
            events.append(
                {
                    "event_id": str(row["id"]),
                    "event_type": "sync_replay",
                    "status": str(row["status"]),
                    "actor_id": str(detail.get("actor_id", "")),
                    "operation": str(detail.get("operation", "")),
                    "sequence": int(row["sequence"]),
                    "created_at": int(row["created_at"]),
                    "queue_id": str(row["queue_id"]),
                }
            )

        if include_conflicts:
            conflict_rows = self.db.execute(
                """
                SELECT id, winner_actor_id, winner_sequence, resolution_json, created_at
                FROM collaboration_conflicts
                WHERE project_id = ?
                ORDER BY created_at ASC
                """,
                (project_id,),
            ).fetchall()
            for row in conflict_rows:
                resolution = json.loads(row["resolution_json"])
                loser_actor = str(resolution.get("loser_actor_id", ""))
                winner_actor = str(row["winner_actor_id"])
                if actor_id and actor_id not in {winner_actor, loser_actor}:
                    continue
                events.append(
                    {
                        "event_id": str(row["id"]),
                        "event_type": "conflict",
                        "status": "resolved",
                        "actor_id": winner_actor,
                        "operation": str(resolution.get("details", {}).get("winner_operation", "")),
                        "sequence": int(row["winner_sequence"]),
                        "created_at": int(row["created_at"]),
                        "loser_actor_id": loser_actor,
                    }
                )

        events.sort(key=self._sort_key)
        keyboard_path = [event["event_id"] for event in events[:5]]

        self.db.execute(
            "INSERT INTO collaboration_timeline_views(id, project_id, event_count, filters_json, generated_at) VALUES (?, ?, ?, ?, ?)",
            (
                new_id("timeline_view"),
                project_id,
                len(events),
                json.dumps({"actor_id": actor_id or "", "include_conflicts": bool(include_conflicts)}, sort_keys=True),
                self._now(),
            ),
        )
        self.db.commit()

        return {
            "ok": True,
            "project_id": project_id,
            "event_count": len(events),
            "events": events,
            "keyboard_path": keyboard_path,
        }
