from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from .ids import new_id


@dataclass
class ResidencyConstraintV1:
    project_id: str
    home_region: str
    dr_region: str
    active_regions: list[str]
    allowed_regions: list[str]
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": int(self.schema_version),
            "project_id": self.project_id,
            "home_region": self.home_region,
            "dr_region": self.dr_region,
            "active_regions": list(self.active_regions),
            "allowed_regions": list(self.allowed_regions),
        }


@dataclass
class RegionReplicationPolicyV1:
    policy_id: str
    project_id: str
    active_regions: list[str]
    dr_regions: list[str]
    write_quorum: int
    read_quorum: int
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": int(self.schema_version),
            "policy_id": self.policy_id,
            "project_id": self.project_id,
            "active_regions": list(self.active_regions),
            "dr_regions": list(self.dr_regions),
            "write_quorum": int(self.write_quorum),
            "read_quorum": int(self.read_quorum),
        }


@dataclass
class ReplicationCheckpointV1:
    checkpoint_id: str
    project_id: str
    sequence: int
    region: str
    status: str
    created_at: int
    details: dict[str, Any] = field(default_factory=dict)
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": int(self.schema_version),
            "checkpoint_id": self.checkpoint_id,
            "project_id": self.project_id,
            "sequence": int(self.sequence),
            "region": self.region,
            "status": self.status,
            "created_at": int(self.created_at),
            "details": dict(self.details),
        }


class MultiRegionReplicationServiceV1:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def _now() -> int:
        return int(time.time())

    def set_residency_policy(
        self,
        *,
        project_id: str,
        home_region: str = "us-west-1",
        active_regions: list[str] | None = None,
        dr_region: str = "eu-west-1",
        allowed_regions: list[str] | None = None,
    ) -> dict[str, Any]:
        active = list(active_regions or ["us-west-1", "us-east-1"])
        allowed = list(allowed_regions or sorted(set(active + [dr_region])))
        now = self._now()
        self.db.execute(
            """
            INSERT OR REPLACE INTO project_residency_policies(project_id, home_region, active_regions_json, dr_region, allowed_regions_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                home_region,
                json.dumps(active, sort_keys=True),
                dr_region,
                json.dumps(allowed, sort_keys=True),
                now,
            ),
        )
        self.db.commit()
        constraint = ResidencyConstraintV1(
            project_id=project_id,
            home_region=home_region,
            dr_region=dr_region,
            active_regions=active,
            allowed_regions=allowed,
        )
        return {"ok": True, "constraint": constraint.to_dict()}

    def get_residency_policy(self, project_id: str) -> dict[str, Any]:
        row = self.db.execute(
            "SELECT project_id, home_region, active_regions_json, dr_region, allowed_regions_json FROM project_residency_policies WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        if not row:
            return self.set_residency_policy(project_id=project_id)
        constraint = ResidencyConstraintV1(
            project_id=str(row["project_id"]),
            home_region=str(row["home_region"]),
            dr_region=str(row["dr_region"]),
            active_regions=list(json.loads(row["active_regions_json"])),
            allowed_regions=list(json.loads(row["allowed_regions_json"])),
        )
        return {"ok": True, "constraint": constraint.to_dict()}

    def policy_for_project(self, project_id: str) -> dict[str, Any]:
        residency = self.get_residency_policy(project_id)
        c = dict(residency["constraint"])
        policy = RegionReplicationPolicyV1(
            policy_id=new_id("region_policy"),
            project_id=project_id,
            active_regions=list(c["active_regions"]),
            dr_regions=[str(c["dr_region"])],
            write_quorum=1,
            read_quorum=1,
        )
        return {"ok": True, "policy": policy.to_dict()}

    def route_region(
        self,
        *,
        project_id: str,
        preferred_region: str | None = None,
        available_regions: list[str] | None = None,
    ) -> dict[str, Any]:
        residency = self.get_residency_policy(project_id)
        c = dict(residency["constraint"])
        available = set(c["allowed_regions"]) if available_regions is None else set(available_regions)

        if preferred_region and preferred_region in available and preferred_region in set(c["allowed_regions"]):
            return {"ok": True, "region": preferred_region, "degraded": False, "reason": "preferred_region"}

        for region in c["active_regions"]:
            if region in available:
                return {
                    "ok": True,
                    "region": region,
                    "degraded": region != c["home_region"],
                    "reason": "active_region",
                }

        if c["dr_region"] in available:
            return {"ok": True, "region": c["dr_region"], "degraded": True, "reason": "dr_failover"}

        return {"ok": False, "error_code": "E_REGION_UNAVAILABLE", "mode": "local_only"}

    def replicate_envelope(
        self,
        *,
        project_id: str,
        sequence: int,
        envelope: dict[str, Any],
        available_regions: list[str] | None = None,
    ) -> dict[str, Any]:
        policy = self.policy_for_project(project_id)
        p = dict(policy["policy"])
        regions = list(p["active_regions"]) + list(p["dr_regions"])
        available = set(regions) if available_regions is None else set(available_regions)
        now = self._now()

        checkpoints: list[dict[str, Any]] = []
        for region in regions:
            status = "succeeded" if region in available else "pending"
            detail = {
                "region": region,
                "envelope": dict(envelope),
                "local_first_continuity": True,
            }
            record = ReplicationCheckpointV1(
                checkpoint_id=new_id("rep_ckpt"),
                project_id=project_id,
                sequence=int(sequence),
                region=region,
                status=status,
                created_at=now,
                details=detail,
            )
            self.db.execute(
                """
                INSERT INTO cloud_replication_checkpoints(id, project_id, sequence, region, status, detail_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.checkpoint_id,
                    project_id,
                    int(sequence),
                    region,
                    status,
                    json.dumps(record.details, sort_keys=True),
                    now,
                ),
            )
            checkpoints.append(record.to_dict())
        self.db.commit()

        return {
            "ok": True,
            "checkpoints": checkpoints,
            "succeeded": sum(1 for item in checkpoints if item["status"] == "succeeded"),
            "pending": sum(1 for item in checkpoints if item["status"] == "pending"),
        }

    def replay_order(self, *, project_id: str) -> dict[str, Any]:
        rows = self.db.execute(
            """
            SELECT sequence, region, status, detail_json, created_at
            FROM cloud_replication_checkpoints
            WHERE project_id = ?
            ORDER BY sequence ASC, region ASC, created_at ASC
            """,
            (project_id,),
        ).fetchall()
        replay = [
            {
                "sequence": int(row["sequence"]),
                "region": str(row["region"]),
                "status": str(row["status"]),
                "detail": json.loads(row["detail_json"]),
                "created_at": int(row["created_at"]),
            }
            for row in rows
        ]
        return {"ok": True, "replay_order": replay}
