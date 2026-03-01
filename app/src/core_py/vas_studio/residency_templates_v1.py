from __future__ import annotations

import json
from typing import Any

from .multi_region_v1 import MultiRegionReplicationServiceV1


class ResidencyTemplateServiceV1:
    def __init__(self, db, *, replication_service: MultiRegionReplicationServiceV1 | None = None):
        self.db = db
        self.replication_service = replication_service or MultiRegionReplicationServiceV1(db)

    def list_templates(self) -> dict[str, Any]:
        rows = self.db.execute(
            "SELECT id, display_name, template_json, created_at, updated_at FROM residency_policy_templates ORDER BY id ASC"
        ).fetchall()
        return {
            "ok": True,
            "templates": [
                {
                    "id": str(row["id"]),
                    "display_name": str(row["display_name"]),
                    "template": json.loads(row["template_json"]),
                    "created_at": int(row["created_at"]),
                    "updated_at": int(row["updated_at"]),
                }
                for row in rows
            ],
        }

    @staticmethod
    def validate_template(template: dict[str, Any]) -> dict[str, Any]:
        home = str(template.get("home_region", "")).strip()
        active = [str(v) for v in list(template.get("active_regions", []))]
        dr = str(template.get("dr_region", "")).strip()
        allowed = [str(v) for v in list(template.get("allowed_regions", []))]

        if not home:
            return {"ok": False, "error_code": "E_TEMPLATE_HOME_REQUIRED"}
        if not active:
            return {"ok": False, "error_code": "E_TEMPLATE_ACTIVE_REQUIRED"}
        if home not in active:
            return {"ok": False, "error_code": "E_TEMPLATE_HOME_NOT_ACTIVE"}
        if dr and dr not in allowed:
            return {"ok": False, "error_code": "E_TEMPLATE_DR_NOT_ALLOWED"}
        if not set(active).issubset(set(allowed)):
            return {"ok": False, "error_code": "E_TEMPLATE_ACTIVE_NOT_ALLOWED"}
        return {"ok": True}

    def apply_template(self, *, project_id: str, template_id: str) -> dict[str, Any]:
        row = self.db.execute(
            "SELECT template_json FROM residency_policy_templates WHERE id = ?",
            (template_id,),
        ).fetchone()
        if row is None:
            return {"ok": False, "error_code": "E_TEMPLATE_NOT_FOUND", "template_id": template_id}

        template = json.loads(row["template_json"])
        validated = self.validate_template(template)
        if not validated["ok"]:
            return {"ok": False, "error_code": validated["error_code"], "template_id": template_id}

        result = self.replication_service.set_residency_policy(
            project_id=project_id,
            home_region=str(template["home_region"]),
            active_regions=[str(v) for v in list(template["active_regions"])],
            dr_region=str(template["dr_region"]),
            allowed_regions=[str(v) for v in list(template["allowed_regions"])],
        )
        return {"ok": True, "template_id": template_id, "constraint": result["constraint"]}
