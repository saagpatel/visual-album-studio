from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from .ids import new_id


@dataclass
class QuotaForecastV1:
    provider: str
    quota_budget: int
    quota_used: int
    pending_units: int
    remaining_after: int
    within_budget: bool
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": int(self.schema_version),
            "provider": self.provider,
            "quota_budget": int(self.quota_budget),
            "quota_used": int(self.quota_used),
            "pending_units": int(self.pending_units),
            "remaining_after": int(self.remaining_after),
            "within_budget": bool(self.within_budget),
        }


@dataclass
class PublishRetryPolicyV1:
    provider: str
    attempt: int
    retry_after_seconds: int
    max_attempts: int
    reason: str
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": int(self.schema_version),
            "provider": self.provider,
            "attempt": int(self.attempt),
            "retry_after_seconds": int(self.retry_after_seconds),
            "max_attempts": int(self.max_attempts),
            "reason": self.reason,
        }


@dataclass
class ProviderSchedulePlanV1:
    plan_id: str
    generated_at: int
    scheduled_jobs: list[dict[str, Any]] = field(default_factory=list)
    deferred_jobs: list[dict[str, Any]] = field(default_factory=list)
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": int(self.schema_version),
            "plan_id": self.plan_id,
            "generated_at": int(self.generated_at),
            "scheduled_jobs": [dict(job) for job in self.scheduled_jobs],
            "deferred_jobs": [dict(job) for job in self.deferred_jobs],
        }


class DistributionSchedulingServiceV1:
    def __init__(self, db=None, *, max_backoff_seconds: int = 3600):
        self.db = db
        self.max_backoff_seconds = int(max_backoff_seconds)

    @staticmethod
    def forecast_quota(provider: str, quota_budget: int, quota_used: int, pending_units: int) -> QuotaForecastV1:
        remaining = int(quota_budget) - int(quota_used) - int(pending_units)
        return QuotaForecastV1(
            provider=provider,
            quota_budget=int(quota_budget),
            quota_used=int(quota_used),
            pending_units=int(pending_units),
            remaining_after=remaining,
            within_budget=remaining >= 0,
        )

    def retry_policy(self, *, provider: str, attempt: int, retryable: bool, error_code: str = "") -> PublishRetryPolicyV1:
        if not retryable:
            return PublishRetryPolicyV1(
                provider=provider,
                attempt=int(attempt),
                retry_after_seconds=0,
                max_attempts=1,
                reason=error_code or "non_retryable",
            )
        seconds = min(self.max_backoff_seconds, 30 * (2 ** max(0, int(attempt) - 1)))
        return PublishRetryPolicyV1(
            provider=provider,
            attempt=int(attempt),
            retry_after_seconds=int(seconds),
            max_attempts=5,
            reason=error_code or "retryable_transient",
        )

    @staticmethod
    def _in_blackout(provider: str, at_epoch: int, provider_policies: dict[str, Any]) -> bool:
        policy = dict(provider_policies.get(provider, {}))
        blackout = list(policy.get("blackout_hours", []))
        if not blackout:
            return False
        hour = int(time.gmtime(int(at_epoch)).tm_hour)
        return hour in {int(v) for v in blackout}

    def optimize_schedule(self, jobs: list[dict[str, Any]], provider_policies: dict[str, Any] | None = None) -> dict[str, Any]:
        provider_policies = dict(provider_policies or {})
        now = int(time.time())
        plan = ProviderSchedulePlanV1(plan_id=new_id("sched_plan"), generated_at=now)

        scored: list[tuple[int, int, int, dict[str, Any]]] = []
        for idx, job in enumerate(jobs):
            provider = str(job.get("provider", ""))
            priority = int(job.get("priority", 50))
            quota_budget = int(job.get("quota_budget", 10000))
            quota_used = int(job.get("quota_used", 0))
            estimated_units = int(job.get("estimated_units", 100))
            forecast = self.forecast_quota(provider, quota_budget, quota_used, estimated_units)
            score = (1 if forecast.within_budget else 0, priority, -idx)
            scored.append((score[0], score[1], score[2], {**job, "_forecast": forecast.to_dict()}))

        scored.sort(key=lambda item: (-item[0], -item[1], item[2]))

        for _, _, _, job in scored:
            provider = str(job.get("provider", ""))
            job_id = str(job.get("job_id", new_id("job")))
            forecast = dict(job.get("_forecast", {}))
            retryable = bool(job.get("retryable", False))
            attempt = int(job.get("attempt", 1))
            error_code = str(job.get("error_code", ""))
            status = "scheduled"
            detail: dict[str, Any] = {"forecast": forecast}
            scheduled_at = now

            if not bool(forecast.get("within_budget", True)):
                status = "deferred"
                detail["reason"] = "quota_exceeded"
                detail["error_code"] = "E_PROVIDER_QUOTA_EXCEEDED"
            elif self._in_blackout(provider, now, provider_policies):
                status = "deferred"
                detail["reason"] = "provider_blackout_window"
                detail["error_code"] = "E_PROVIDER_BLACKOUT"
            elif retryable and attempt > 1:
                policy = self.retry_policy(provider=provider, attempt=attempt, retryable=retryable, error_code=error_code)
                scheduled_at = now + int(policy.retry_after_seconds)
                detail["retry_policy"] = policy.to_dict()

            row = {
                "job_id": job_id,
                "provider": provider,
                "status": status,
                "scheduled_at": int(scheduled_at),
                "detail": detail,
            }
            if status == "scheduled":
                plan.scheduled_jobs.append(row)
            else:
                plan.deferred_jobs.append(row)

            if self.db:
                self.db.execute(
                    """
                    INSERT INTO distribution_schedule_plans(id, provider, job_id, status, scheduled_at, detail_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_id("sched_row"),
                        provider,
                        job_id,
                        status,
                        int(scheduled_at),
                        json.dumps(detail, sort_keys=True),
                        now,
                    ),
                )
                self.db.commit()

        return {"ok": True, "plan": plan.to_dict()}
