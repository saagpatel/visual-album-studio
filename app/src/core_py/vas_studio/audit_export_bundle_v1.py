from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .audit_dashboard_v1 import AuditDashboardServiceV1
from .ids import new_id

_REDACT_KEYS = ("token", "secret", "access", "refresh", "authorization")


class AuditDashboardExportServiceV1:
    def __init__(self, db, *, audit_service: AuditDashboardServiceV1 | None = None):
        self.db = db
        self.audit_service = audit_service or AuditDashboardServiceV1(db)

    @staticmethod
    def _now() -> int:
        return int(time.time())

    def _redact(self, value: Any) -> Any:
        if isinstance(value, dict):
            out: dict[str, Any] = {}
            for key, item in value.items():
                key_str = str(key)
                if any(marker in key_str.lower() for marker in _REDACT_KEYS):
                    out[key_str] = "[REDACTED]"
                else:
                    out[key_str] = self._redact(item)
            return out
        if isinstance(value, list):
            return [self._redact(item) for item in value]
        if isinstance(value, str):
            lower = value.lower()
            if "bearer " in lower or "token" in lower:
                return "[REDACTED]"
        return value

    def export_bundle(
        self,
        *,
        project_id: str,
        output_dir: Path | str,
        since_epoch: int = 0,
        include_raw: bool = False,
    ) -> dict[str, Any]:
        report = self.audit_service.dashboard(project_id=project_id, since_epoch=since_epoch)
        # Include bounded recent diagnostics so exported summaries prove redaction paths.
        diagnostics = self.db.execute(
            """
            SELECT id, connector, severity, payload_json, created_at
            FROM connector_diagnostics
            WHERE project_id = ? AND created_at >= ?
            ORDER BY created_at DESC
            LIMIT 25
            """,
            (project_id, int(since_epoch)),
        ).fetchall()
        report["diagnostics"] = [
            {
                "id": str(row["id"]),
                "connector": str(row["connector"]),
                "severity": str(row["severity"]),
                "payload": json.loads(row["payload_json"]),
                "created_at": int(row["created_at"]),
            }
            for row in diagnostics
        ]
        now = self._now()
        export_id = new_id("audit_export")
        root = Path(output_dir) / project_id / export_id
        root.mkdir(parents=True, exist_ok=True)

        safe_report = self._redact(report)
        summary_path = root / "dashboard_summary.json"
        summary_path.write_text(json.dumps(safe_report, indent=2, sort_keys=True), encoding="utf-8")

        text_path = root / "dashboard_summary.txt"
        text_path.write_text(
            "\n".join(
                [
                    f"project_id={project_id}",
                    f"open_events={len(report.get('open_events', []))}",
                    f"signals={len(report.get('signals', []))}",
                    f"generated_at={now}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        files = [str(summary_path), str(text_path)]
        if include_raw:
            raw_path = root / "dashboard_raw.json"
            # Keep exported raw payload redacted to preserve bundle safety guarantees.
            raw_path.write_text(json.dumps(safe_report, indent=2, sort_keys=True), encoding="utf-8")
            files.append(str(raw_path))

        manifest = {
            "schema_version": 1,
            "export_id": export_id,
            "project_id": project_id,
            "generated_at": now,
            "files": files,
        }
        manifest_path = root / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        files.append(str(manifest_path))

        self.db.execute(
            "INSERT INTO audit_dashboard_exports(id, project_id, export_path, manifest_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (export_id, project_id, str(root), json.dumps(manifest, sort_keys=True), now),
        )
        self.db.commit()

        return {"ok": True, "export_id": export_id, "export_path": str(root), "manifest": manifest}

    def list_exports(self, *, project_id: str, limit: int = 20) -> dict[str, Any]:
        rows = self.db.execute(
            """
            SELECT id, export_path, manifest_json, created_at
            FROM audit_dashboard_exports
            WHERE project_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (project_id, int(limit)),
        ).fetchall()
        return {
            "ok": True,
            "exports": [
                {
                    "id": str(row["id"]),
                    "export_path": str(row["export_path"]),
                    "manifest": json.loads(row["manifest_json"]),
                    "created_at": int(row["created_at"]),
                }
                for row in rows
            ],
        }
