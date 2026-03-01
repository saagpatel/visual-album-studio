from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from .distribution_scheduler_v1 import DistributionSchedulingServiceV1
from .ids import new_id


@dataclass
class ProviderTimelineV1:
    provider: str
    scheduled: list[dict[str, Any]] = field(default_factory=list)
    deferred: list[dict[str, Any]] = field(default_factory=list)
    quota_overlay: dict[str, Any] = field(default_factory=dict)
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": int(self.schema_version),
            "provider": self.provider,
            "scheduled": [dict(item) for item in self.scheduled],
            "deferred": [dict(item) for item in self.deferred],
            "quota_overlay": dict(self.quota_overlay),
        }


class SchedulerSimulationDashboardV1:
    def __init__(self, db, *, scheduler: DistributionSchedulingServiceV1 | None = None):
        self.db = db
        self.scheduler = scheduler or DistributionSchedulingServiceV1(db)

    @staticmethod
    def _now() -> int:
        return int(time.time())

    def simulate(
        self,
        *,
        jobs: list[dict[str, Any]],
        provider_policies: dict[str, Any] | None = None,
        label: str = "simulation",
    ) -> dict[str, Any]:
        plan_result = self.scheduler.optimize_schedule(jobs=jobs, provider_policies=provider_policies)
        plan = dict(plan_result["plan"])
        plan_id = str(plan["plan_id"])
        providers: dict[str, ProviderTimelineV1] = {}

        for row in plan.get("scheduled_jobs", []):
            provider = str(row.get("provider", ""))
            timeline = providers.setdefault(provider, ProviderTimelineV1(provider=provider))
            timeline.scheduled.append(dict(row))
            timeline.quota_overlay = dict(row.get("detail", {}).get("forecast", timeline.quota_overlay))

        for row in plan.get("deferred_jobs", []):
            provider = str(row.get("provider", ""))
            timeline = providers.setdefault(provider, ProviderTimelineV1(provider=provider))
            timeline.deferred.append(dict(row))
            timeline.quota_overlay = dict(row.get("detail", {}).get("forecast", timeline.quota_overlay))

        now = self._now()
        side_by_side = []
        for provider in sorted(providers.keys()):
            timeline = providers[provider].to_dict()
            side_by_side.append(timeline)
            self.db.execute(
                """
                INSERT INTO scheduler_simulation_runs(id, plan_id, provider, status, timeline_json, quota_overlay_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id("sched_sim"),
                    plan_id,
                    provider,
                    "ready",
                    json.dumps(timeline, sort_keys=True),
                    json.dumps(timeline.get("quota_overlay", {}), sort_keys=True),
                    now,
                ),
            )
        self.db.commit()

        return {
            "ok": True,
            "label": label,
            "plan_id": plan_id,
            "generated_at": now,
            "scheduled_total": len(plan.get("scheduled_jobs", [])),
            "deferred_total": len(plan.get("deferred_jobs", [])),
            "side_by_side": side_by_side,
        }

    def latest_simulation(self, *, provider: str | None = None, limit: int = 20) -> dict[str, Any]:
        if provider:
            rows = self.db.execute(
                """
                SELECT plan_id, provider, timeline_json, quota_overlay_json, created_at
                FROM scheduler_simulation_runs
                WHERE provider = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (provider, int(limit)),
            ).fetchall()
        else:
            rows = self.db.execute(
                """
                SELECT plan_id, provider, timeline_json, quota_overlay_json, created_at
                FROM scheduler_simulation_runs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
        return {
            "ok": True,
            "runs": [
                {
                    "plan_id": str(row["plan_id"]),
                    "provider": str(row["provider"]),
                    "timeline": json.loads(row["timeline_json"]),
                    "quota_overlay": json.loads(row["quota_overlay_json"]),
                    "created_at": int(row["created_at"]),
                }
                for row in rows
            ],
        }
