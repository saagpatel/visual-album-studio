from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from .ids import new_id


@dataclass
class AuditEventAggregateV1:
    project_id: str
    total_events: int
    error_events: int
    warn_events: int
    failed_sync_replays: int
    conflict_count: int
    connector_breakdown: dict[str, int] = field(default_factory=dict)
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": int(self.schema_version),
            "project_id": self.project_id,
            "total_events": int(self.total_events),
            "error_events": int(self.error_events),
            "warn_events": int(self.warn_events),
            "failed_sync_replays": int(self.failed_sync_replays),
            "conflict_count": int(self.conflict_count),
            "connector_breakdown": dict(self.connector_breakdown),
        }


@dataclass
class AnomalySignalV1:
    signal_id: str
    project_id: str
    signal_type: str
    severity: str
    metric_name: str
    metric_value: float
    threshold_value: float
    created_at: int
    details: dict[str, Any] = field(default_factory=dict)
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
            "created_at": int(self.created_at),
            "details": dict(self.details),
        }


@dataclass
class OwnershipEscalationV1:
    signal_id: str
    owner: str
    channel: str
    severity: str
    status: str
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": int(self.schema_version),
            "signal_id": self.signal_id,
            "owner": self.owner,
            "channel": self.channel,
            "severity": self.severity,
            "status": self.status,
        }


class AuditDashboardServiceV1:
    def __init__(self, db, *, default_owner: str = "saagar210"):
        self.db = db
        self.default_owner = default_owner

    @staticmethod
    def _now() -> int:
        return int(time.time())

    def aggregate(self, *, project_id: str, since_epoch: int = 0) -> dict[str, Any]:
        connector_rows = self.db.execute(
            """
            SELECT connector, severity, COUNT(*) AS c
            FROM connector_diagnostics
            WHERE project_id = ? AND created_at >= ?
            GROUP BY connector, severity
            """,
            (project_id, int(since_epoch)),
        ).fetchall()

        total_events = 0
        error_events = 0
        warn_events = 0
        connector_breakdown: dict[str, int] = {}
        for row in connector_rows:
            connector = str(row["connector"])
            count = int(row["c"])
            total_events += count
            connector_breakdown[connector] = connector_breakdown.get(connector, 0) + count
            if str(row["severity"]) == "error":
                error_events += count
            if str(row["severity"]) == "warn":
                warn_events += count

        failed_sync_replays_row = self.db.execute(
            """
            SELECT COUNT(*) AS c
            FROM cloud_sync_replay_log
            WHERE project_id = ? AND status = 'failed' AND created_at >= ?
            """,
            (project_id, int(since_epoch)),
        ).fetchone()
        conflicts_row = self.db.execute(
            """
            SELECT COUNT(*) AS c
            FROM collaboration_conflicts
            WHERE project_id = ? AND created_at >= ?
            """,
            (project_id, int(since_epoch)),
        ).fetchone()

        aggregate = AuditEventAggregateV1(
            project_id=project_id,
            total_events=total_events,
            error_events=error_events,
            warn_events=warn_events,
            failed_sync_replays=int(failed_sync_replays_row["c"]),
            conflict_count=int(conflicts_row["c"]),
            connector_breakdown=connector_breakdown,
        )
        return {"ok": True, "aggregate": aggregate.to_dict()}

    def detect_anomalies(
        self,
        *,
        project_id: str,
        since_epoch: int = 0,
        thresholds: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        thresholds = {
            "error_events": 3,
            "failed_sync_replays": 2,
            "conflict_count": 2,
            **(thresholds or {}),
        }
        aggregate = self.aggregate(project_id=project_id, since_epoch=since_epoch)
        agg = dict(aggregate["aggregate"])
        now = self._now()

        signals: list[dict[str, Any]] = []
        mappings = [
            ("connector_error_spike", "error_events", "critical"),
            ("sync_replay_failures", "failed_sync_replays", "error"),
            ("conflict_spike", "conflict_count", "warn"),
        ]

        for signal_type, metric_name, severity in mappings:
            value = float(agg.get(metric_name, 0))
            threshold = float(thresholds.get(metric_name, 0))
            if value >= threshold:
                signal = AnomalySignalV1(
                    signal_id=new_id("anomaly"),
                    project_id=project_id,
                    signal_type=signal_type,
                    severity=severity,
                    metric_name=metric_name,
                    metric_value=value,
                    threshold_value=threshold,
                    created_at=now,
                    details={"aggregate": agg},
                )
                signals.append(signal.to_dict())

        return {"ok": True, "signals": signals, "aggregate": agg}

    def resolve_owner(self, signal_type: str) -> dict[str, Any]:
        row = self.db.execute(
            "SELECT owner, channel FROM audit_ownership_map WHERE signal_type = ?",
            (signal_type,),
        ).fetchone()
        if row:
            return {"owner": str(row["owner"]), "channel": str(row["channel"])}
        return {"owner": self.default_owner, "channel": "ops"}

    def record_and_escalate(self, *, project_id: str, since_epoch: int = 0) -> dict[str, Any]:
        detection = self.detect_anomalies(project_id=project_id, since_epoch=since_epoch)
        escalations: list[dict[str, Any]] = []

        for signal in detection["signals"]:
            owner_info = self.resolve_owner(str(signal["signal_type"]))
            escalation = OwnershipEscalationV1(
                signal_id=str(signal["signal_id"]),
                owner=owner_info["owner"],
                channel=owner_info["channel"],
                severity=str(signal["severity"]),
                status="open",
            )
            self.db.execute(
                """
                INSERT INTO audit_anomaly_events(
                  id, project_id, signal_type, severity, metric_name, metric_value, threshold_value, owner, status, detail_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(signal["signal_id"]),
                    project_id,
                    str(signal["signal_type"]),
                    str(signal["severity"]),
                    str(signal["metric_name"]),
                    float(signal["metric_value"]),
                    float(signal["threshold_value"]),
                    escalation.owner,
                    escalation.status,
                    json.dumps(signal.get("details", {}), sort_keys=True),
                    int(signal["created_at"]),
                ),
            )
            escalations.append(escalation.to_dict())
        self.db.commit()

        return {"ok": True, "signals": detection["signals"], "escalations": escalations, "aggregate": detection["aggregate"]}

    def dashboard(self, *, project_id: str, since_epoch: int = 0) -> dict[str, Any]:
        report = self.record_and_escalate(project_id=project_id, since_epoch=since_epoch)
        open_rows = self.db.execute(
            """
            SELECT id, signal_type, severity, owner, status, created_at
            FROM audit_anomaly_events
            WHERE project_id = ? AND status = 'open'
            ORDER BY created_at DESC
            """,
            (project_id,),
        ).fetchall()
        return {
            "ok": True,
            "aggregate": report["aggregate"],
            "signals": report["signals"],
            "escalations": report["escalations"],
            "open_events": [dict(row) for row in open_rows],
        }
