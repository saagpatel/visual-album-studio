from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from .ids import new_id
from .multi_region_v1 import MultiRegionReplicationServiceV1


@dataclass
class DRRehearsalStepV1:
    step_name: str
    sequence: int
    status: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_name": self.step_name,
            "sequence": int(self.sequence),
            "status": self.status,
            "details": dict(self.details),
        }


@dataclass
class DRRehearsalReportV1:
    run_id: str
    project_id: str
    quarter_label: str
    status: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    created_at: int = 0
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": int(self.schema_version),
            "run_id": self.run_id,
            "project_id": self.project_id,
            "quarter_label": self.quarter_label,
            "status": self.status,
            "steps": [dict(step) for step in self.steps],
            "created_at": int(self.created_at),
        }


class DRRehearsalRunnerV1:
    def __init__(self, db, *, replication_service: MultiRegionReplicationServiceV1 | None = None):
        self.db = db
        self.replication_service = replication_service or MultiRegionReplicationServiceV1(db)

    @staticmethod
    def _now() -> int:
        return int(time.time())

    @staticmethod
    def _quarter_label(epoch: int) -> str:
        gm = time.gmtime(int(epoch))
        quarter = ((gm.tm_mon - 1) // 3) + 1
        return f"{gm.tm_year}-Q{quarter}"

    def run_quarterly_rehearsal(self, *, project_id: str, sequence_start: int = 1000) -> dict[str, Any]:
        now = self._now()
        run_id = new_id("dr_run")
        previous_policy = self.replication_service.get_residency_policy(project_id).get("constraint", {})
        restored = False
        restore_error = ""

        self.replication_service.set_residency_policy(
            project_id=project_id,
            home_region="us-west-1",
            active_regions=["us-west-1", "us-east-1"],
            dr_region="eu-west-1",
            allowed_regions=["us-west-1", "us-east-1", "eu-west-1"],
        )

        scenarios = [
            ("active_active_healthy", ["us-west-1", "us-east-1", "eu-west-1"], "us-west-1", ""),
            ("primary_outage_failover", ["us-east-1", "eu-west-1"], "us-east-1", ""),
            ("active_outage_dr_only", ["eu-west-1"], "eu-west-1", ""),
            ("global_outage_local_only", [], "", "E_REGION_UNAVAILABLE"),
        ]

        steps: list[dict[str, Any]] = []
        try:
            for idx, (name, available, expected_region, expected_error) in enumerate(scenarios):
                sequence = int(sequence_start) + idx
                route = self.replication_service.route_region(
                    project_id=project_id,
                    preferred_region="us-west-1",
                    available_regions=available,
                )

                if expected_error:
                    ok = route.get("ok") is False and route.get("error_code") == expected_error
                else:
                    ok = route.get("ok") is True and route.get("region") == expected_region

                replication = None
                if route.get("ok"):
                    replication = self.replication_service.replicate_envelope(
                        project_id=project_id,
                        sequence=sequence,
                        envelope={"operation": "dr_rehearsal", "scenario": name, "sequence": sequence},
                        available_regions=available,
                    )
                    if not expected_error:
                        ok = ok and replication.get("ok") is True

                step = DRRehearsalStepV1(
                    step_name=name,
                    sequence=sequence,
                    status="passed" if ok else "failed",
                    details={
                        "available_regions": available,
                        "route": route,
                        "replication": replication,
                    },
                ).to_dict()
                steps.append(step)
        finally:
            try:
                self.replication_service.set_residency_policy(
                    project_id=project_id,
                    home_region=str(previous_policy.get("home_region", "us-west-1")),
                    active_regions=[str(v) for v in list(previous_policy.get("active_regions", ["us-west-1", "us-east-1"]))],
                    dr_region=str(previous_policy.get("dr_region", "eu-west-1")),
                    allowed_regions=[str(v) for v in list(previous_policy.get("allowed_regions", ["us-west-1", "us-east-1", "eu-west-1"]))],
                )
                restored = True
            except Exception as exc:  # pragma: no cover - defensive safety net
                restore_error = str(exc)

        steps.append(
            DRRehearsalStepV1(
                step_name="policy_restore",
                sequence=int(sequence_start) + len(scenarios),
                status="passed" if restored else "failed",
                details={"restored": restored, "error": restore_error},
            ).to_dict()
        )

        status = "passed" if all(step["status"] == "passed" for step in steps) else "failed"
        report = DRRehearsalReportV1(
            run_id=run_id,
            project_id=project_id,
            quarter_label=self._quarter_label(now),
            status=status,
            steps=steps,
            created_at=now,
        )

        self.db.execute(
            "INSERT INTO dr_rehearsal_runs(id, project_id, quarter_label, status, summary_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (run_id, project_id, report.quarter_label, status, json.dumps(report.to_dict(), sort_keys=True), now),
        )
        for step in steps:
            self.db.execute(
                "INSERT INTO dr_rehearsal_steps(id, run_id, step_name, status, sequence, detail_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    new_id("dr_step"),
                    run_id,
                    str(step["step_name"]),
                    str(step["status"]),
                    int(step["sequence"]),
                    json.dumps(step["details"], sort_keys=True),
                    now,
                ),
            )
        self.db.commit()
        return {"ok": status == "passed", "report": report.to_dict()}

    def latest_report(self, *, project_id: str) -> dict[str, Any]:
        row = self.db.execute(
            "SELECT summary_json, status, quarter_label, created_at FROM dr_rehearsal_runs WHERE project_id = ? ORDER BY created_at DESC LIMIT 1",
            (project_id,),
        ).fetchone()
        if not row:
            return {"ok": False, "error_code": "E_DR_REPORT_NOT_FOUND"}
        return {
            "ok": True,
            "status": str(row["status"]),
            "quarter_label": str(row["quarter_label"]),
            "created_at": int(row["created_at"]),
            "report": json.loads(row["summary_json"]),
        }
