from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from .audit_dashboard_v1 import AuditDashboardServiceV1
from .ids import new_id


@dataclass
class AnomalyTriageContextV1:
    signal_id: str
    project_id: str
    signal_type: str
    severity: str
    metric_name: str
    metric_value: float
    threshold_value: float
    historical_count: int
    recommendations: list[str] = field(default_factory=list)
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": int(self.schema_version),
            "signal_id": self.signal_id,
            "project_id": self.project_id,
            "signal_type": self.signal_type,
            "severity": self.severity,
            "metric_name": self.metric_name,
            "metric_value": float(self.metric_value),
            "threshold_value": float(self.threshold_value),
            "historical_count": int(self.historical_count),
            "recommendations": list(self.recommendations),
        }


class AnomalyTriageServiceV1:
    def __init__(self, db, *, audit_service: AuditDashboardServiceV1 | None = None):
        self.db = db
        self.audit_service = audit_service or AuditDashboardServiceV1(db)

    @staticmethod
    def _now() -> int:
        return int(time.time())

    @staticmethod
    def _recommend(signal_type: str, severity: str) -> list[str]:
        out: list[str] = []
        if signal_type == "connector_error_spike":
            out.append("inspect connector diagnostics and pause risky provider rollouts")
            out.append("re-run provider acceptance smoke after policy sanity checks")
        elif signal_type == "sync_replay_failures":
            out.append("run replay queue triage and validate cloud adapter availability")
            out.append("verify local-first continuity path is still writable")
        elif signal_type == "conflict_spike":
            out.append("review conflict resolution traces and actor sequencing")
            out.append("capture collaboration timeline for impacted project")
        else:
            out.append("review anomaly details and run targeted regression checks")
        if severity in {"critical", "error"}:
            out.insert(0, "escalate to owner immediately and open incident note")
        return out

    def _historical_count(self, *, project_id: str, signal_type: str, created_at: int, history_window_seconds: int) -> int:
        row = self.db.execute(
            """
            SELECT COUNT(*) AS c
            FROM audit_anomaly_events
            WHERE project_id = ? AND signal_type = ? AND created_at < ? AND created_at >= ?
            """,
            (project_id, signal_type, int(created_at), int(created_at) - int(history_window_seconds)),
        ).fetchone()
        return int(row["c"]) if row else 0

    def enrich(self, *, project_id: str, since_epoch: int = 0, history_window_seconds: int = 86400) -> dict[str, Any]:
        detection = self.audit_service.detect_anomalies(project_id=project_id, since_epoch=since_epoch)
        now = self._now()
        triaged: list[dict[str, Any]] = []

        for signal in detection.get("signals", []):
            signal_id = str(signal.get("signal_id", new_id("triage_signal")))
            signal_type = str(signal.get("signal_type", "unknown"))
            severity = str(signal.get("severity", "warn"))
            created_at = int(signal.get("created_at", now))
            historical_count = self._historical_count(
                project_id=project_id,
                signal_type=signal_type,
                created_at=created_at,
                history_window_seconds=history_window_seconds,
            )
            recommendations = self._recommend(signal_type, severity)
            context = AnomalyTriageContextV1(
                signal_id=signal_id,
                project_id=project_id,
                signal_type=signal_type,
                severity=severity,
                metric_name=str(signal.get("metric_name", "")),
                metric_value=float(signal.get("metric_value", 0.0)),
                threshold_value=float(signal.get("threshold_value", 0.0)),
                historical_count=historical_count,
                recommendations=recommendations,
            )
            payload = context.to_dict()
            self.db.execute(
                """
                INSERT INTO anomaly_triage_reports(id, project_id, signal_id, severity, context_json, recommendations_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id("triage_report"),
                    project_id,
                    signal_id,
                    severity,
                    json.dumps(payload, sort_keys=True),
                    json.dumps(recommendations, sort_keys=True),
                    now,
                ),
            )
            triaged.append(payload)

        self.db.commit()
        return {"ok": True, "triaged": triaged, "aggregate": detection.get("aggregate", {})}

    def recent_reports(self, *, project_id: str, limit: int = 20) -> dict[str, Any]:
        rows = self.db.execute(
            """
            SELECT context_json, created_at
            FROM anomaly_triage_reports
            WHERE project_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (project_id, int(limit)),
        ).fetchall()
        return {
            "ok": True,
            "reports": [
                {
                    "context": json.loads(row["context_json"]),
                    "created_at": int(row["created_at"]),
                }
                for row in rows
            ],
        }
