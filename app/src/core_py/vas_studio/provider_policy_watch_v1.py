from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from .ids import new_id


@dataclass
class ProviderPolicyDiffV1:
    provider: str
    changed_fields: list[str] = field(default_factory=list)
    added_fields: list[str] = field(default_factory=list)
    removed_fields: list[str] = field(default_factory=list)
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": int(self.schema_version),
            "provider": self.provider,
            "changed_fields": list(self.changed_fields),
            "added_fields": list(self.added_fields),
            "removed_fields": list(self.removed_fields),
        }


class ProviderPolicyWatcherV1:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def _canonical(value: Any) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _flatten(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(value, dict):
                result.update(ProviderPolicyWatcherV1._flatten(value, prefix=path))
            else:
                result[path] = value
        return result

    def _diff(self, provider: str, previous: dict[str, Any], current: dict[str, Any]) -> ProviderPolicyDiffV1:
        prev_flat = self._flatten(previous)
        curr_flat = self._flatten(current)

        prev_keys = set(prev_flat.keys())
        curr_keys = set(curr_flat.keys())

        added = sorted(curr_keys - prev_keys)
        removed = sorted(prev_keys - curr_keys)
        changed = sorted(path for path in prev_keys & curr_keys if prev_flat[path] != curr_flat[path])

        return ProviderPolicyDiffV1(
            provider=provider,
            changed_fields=changed,
            added_fields=added,
            removed_fields=removed,
        )

    def ingest_policy(self, *, provider: str, policy: dict[str, Any], source: str = "manual") -> dict[str, Any]:
        provider = str(provider).strip().lower()
        policy = dict(policy)
        now = int(time.time())

        existing = self.db.execute(
            "SELECT id, policy_json FROM provider_policy_cache WHERE provider = ? ORDER BY fetched_at DESC LIMIT 1",
            (provider,),
        ).fetchone()

        if existing is None:
            self.db.execute(
                "INSERT INTO provider_policy_cache(id, provider, policy_json, fetched_at) VALUES (?, ?, ?, ?)",
                (new_id("policy_cache"), provider, self._canonical(policy), now),
            )
            self.db.commit()
            return {"ok": True, "provider": provider, "changed": False, "baseline": True, "changed_fields": []}

        previous = json.loads(existing["policy_json"])
        diff = self._diff(provider, previous, policy)
        changed = bool(diff.changed_fields or diff.added_fields or diff.removed_fields)

        self.db.execute(
            "UPDATE provider_policy_cache SET policy_json = ?, fetched_at = ? WHERE id = ?",
            (self._canonical(policy), now, existing["id"]),
        )

        if changed:
            self.db.execute(
                """
                INSERT INTO provider_policy_changelog(
                  id, provider, previous_policy_json, current_policy_json, changed_fields_json, diff_json, source, detected_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id("policy_change"),
                    provider,
                    self._canonical(previous),
                    self._canonical(policy),
                    self._canonical(diff.changed_fields + diff.added_fields + diff.removed_fields),
                    self._canonical(diff.to_dict()),
                    source,
                    now,
                ),
            )
        self.db.commit()

        return {
            "ok": True,
            "provider": provider,
            "changed": changed,
            "baseline": False,
            "changed_fields": diff.changed_fields,
            "added_fields": diff.added_fields,
            "removed_fields": diff.removed_fields,
        }

    def ingest_snapshot(self, *, snapshot: dict[str, dict[str, Any]], source: str = "scheduled") -> dict[str, Any]:
        providers_checked = 0
        changes_detected = 0
        results: list[dict[str, Any]] = []

        for provider, policy in sorted(snapshot.items()):
            providers_checked += 1
            result = self.ingest_policy(provider=provider, policy=policy, source=source)
            if result.get("changed"):
                changes_detected += 1
            results.append(result)

        self.db.execute(
            "INSERT INTO provider_policy_watch_runs(id, source, providers_checked, changes_detected, created_at) VALUES (?, ?, ?, ?, ?)",
            (new_id("policy_run"), source, providers_checked, changes_detected, int(time.time())),
        )
        self.db.commit()

        return {
            "ok": True,
            "providers_checked": providers_checked,
            "changes_detected": changes_detected,
            "results": results,
        }

    def recent_changes(self, *, provider: str | None = None, limit: int = 20) -> dict[str, Any]:
        limit = max(1, int(limit))
        if provider:
            rows = self.db.execute(
                """
                SELECT provider, previous_policy_json, current_policy_json, changed_fields_json, diff_json, source, detected_at
                FROM provider_policy_changelog
                WHERE provider = ?
                ORDER BY detected_at DESC
                LIMIT ?
                """,
                (provider, limit),
            ).fetchall()
        else:
            rows = self.db.execute(
                """
                SELECT provider, previous_policy_json, current_policy_json, changed_fields_json, diff_json, source, detected_at
                FROM provider_policy_changelog
                ORDER BY detected_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return {
            "ok": True,
            "changes": [
                {
                    "provider": str(row["provider"]),
                    "previous": json.loads(row["previous_policy_json"]),
                    "current": json.loads(row["current_policy_json"]),
                    "changed_fields": json.loads(row["changed_fields_json"]),
                    "diff": json.loads(row["diff_json"]),
                    "source": str(row["source"]),
                    "detected_at": int(row["detected_at"]),
                }
                for row in rows
            ],
        }

    def triage_recommendations(self, *, provider: str | None = None, limit: int = 20) -> dict[str, Any]:
        recent = self.recent_changes(provider=provider, limit=limit)
        recommendations: list[dict[str, Any]] = []

        for change in recent["changes"]:
            fields = [str(v) for v in change["changed_fields"]]
            suggestions: list[str] = []
            if any("quota" in path for path in fields):
                suggestions.append("revalidate provider quota budgets and scheduler thresholds")
            if any("policy" in path or "compliance" in path for path in fields):
                suggestions.append("review provider policy gating and metadata defaults before publish")
            if any("blackout" in path for path in fields):
                suggestions.append("update blackout windows in scheduler policy config")
            if not suggestions:
                suggestions.append("review provider change impact and rerun acceptance publish flow")
            recommendations.append(
                {
                    "provider": change["provider"],
                    "changed_fields": fields,
                    "recommendations": suggestions,
                    "detected_at": change["detected_at"],
                }
            )

        return {"ok": True, "recommendations": recommendations}
