from __future__ import annotations

import csv
import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AvailabilityStateV1:
    available: bool
    reason_code: str
    manual_fallback_available: bool

    def to_dict(self) -> dict:
        return {
            "available": self.available,
            "reason_code": self.reason_code,
            "manual_fallback_available": self.manual_fallback_available,
        }


class AnalyticsService:
    def __init__(self, db):
        self.db = db

    def store_snapshot(self, channel_row_id: str, start_ymd: str, end_ymd: str, metrics: dict) -> str:
        snapshot_id = f"snapshot_{uuid.uuid4().hex}"
        self.db.execute(
            """
            INSERT INTO analytics_snapshots(id, channel_row_id, range_start_ymd, range_end_ymd,
                                           metrics_json, dimensions_json, data_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot_id,
                channel_row_id,
                start_ymd,
                end_ymd,
                json.dumps(metrics),
                json.dumps({}),
                json.dumps(metrics),
                int(time.time()),
            ),
        )
        self.db.commit()
        return snapshot_id

    def get_dashboard_snapshot(self, channel_row_id: str, range_start_ymd: str = "", range_end_ymd: str = "") -> dict:
        if range_start_ymd and range_end_ymd:
            row = self.db.execute(
                """
                SELECT COUNT(*) AS c, COALESCE(MAX(created_at), 0) AS latest_snapshot_at
                FROM analytics_snapshots
                WHERE channel_row_id = ? AND range_start_ymd >= ? AND range_end_ymd <= ?
                """,
                (channel_row_id, range_start_ymd, range_end_ymd),
            ).fetchone()
        elif range_start_ymd:
            row = self.db.execute(
                """
                SELECT COUNT(*) AS c, COALESCE(MAX(created_at), 0) AS latest_snapshot_at
                FROM analytics_snapshots
                WHERE channel_row_id = ? AND range_start_ymd >= ?
                """,
                (channel_row_id, range_start_ymd),
            ).fetchone()
        elif range_end_ymd:
            row = self.db.execute(
                """
                SELECT COUNT(*) AS c, COALESCE(MAX(created_at), 0) AS latest_snapshot_at
                FROM analytics_snapshots
                WHERE channel_row_id = ? AND range_end_ymd <= ?
                """,
                (channel_row_id, range_end_ymd),
            ).fetchone()
        else:
            row = self.db.execute(
                """
                SELECT COUNT(*) AS c, COALESCE(MAX(created_at), 0) AS latest_snapshot_at
                FROM analytics_snapshots
                WHERE channel_row_id = ?
                """,
                (channel_row_id,),
            ).fetchone()
        synced = self.db.execute(
            "SELECT COALESCE(MAX(updated_at), 0) AS ts FROM analytics_ingest_runs WHERE channel_row_id = ? AND status = 'succeeded'",
            (channel_row_id,),
        ).fetchone()
        count = int(row["c"]) if row else 0
        availability = AvailabilityStateV1(
            available=count > 0,
            reason_code="" if count > 0 else "E_ANALYTICS_EMPTY",
            manual_fallback_available=count == 0,
        )
        return {
            "channel_row_id": channel_row_id,
            "range_start_ymd": range_start_ymd,
            "range_end_ymd": range_end_ymd,
            "snapshot_count": count,
            "latest_snapshot_at": int(row["latest_snapshot_at"]) if row else 0,
            "last_synced_at": int(synced["ts"]) if synced else 0,
            "availability": availability.to_dict(),
        }

    def run_incremental_sync(
        self,
        channel_row_id: str,
        range_start_ymd: str,
        range_end_ymd: str,
        rows: list[dict] | None = None,
    ) -> dict:
        ingest_run_id = f"ingest_{uuid.uuid4().hex}"
        now = int(time.time())
        self.db.execute(
            """
            INSERT INTO analytics_ingest_runs(id, channel_row_id, source, range_start_ymd, range_end_ymd, rows_ingested, status, details_json, created_at, updated_at)
            VALUES (?, ?, 'analytics_api', ?, ?, 0, 'started', '{}', ?, ?)
            """,
            (ingest_run_id, channel_row_id, range_start_ymd, range_end_ymd, now, now),
        )

        ingested = 0
        for row in rows or []:
            day = str(row.get("date_ymd", range_start_ymd))
            existing = self.db.execute(
                """
                SELECT COUNT(*) AS c
                FROM analytics_snapshots
                WHERE channel_row_id = ? AND range_start_ymd = ? AND range_end_ymd = ?
                """,
                (channel_row_id, day, day),
            ).fetchone()
            if existing and int(existing["c"]) > 0:
                continue
            metrics = row.get("metrics", {})
            if not isinstance(metrics, dict):
                metrics = {"value": metrics}
            self.store_snapshot(channel_row_id, day, day, metrics)
            ingested += 1

        done = int(time.time())
        self.db.execute(
            """
            UPDATE analytics_ingest_runs
            SET rows_ingested = ?, status = 'succeeded', updated_at = ?
            WHERE id = ?
            """,
            (ingested, done, ingest_run_id),
        )
        self.db.commit()
        return {"ingest_run_id": ingest_run_id, "rows_ingested": ingested, "status": "succeeded", "last_synced_at": done}

    def import_reporting_csv(self, channel_row_id: str, csv_path: Path, report_type: str) -> int:
        ingest_run_id = f"ingest_{uuid.uuid4().hex}"
        started = int(time.time())
        self.db.execute(
            """
            INSERT INTO analytics_ingest_runs(id, channel_row_id, source, range_start_ymd, range_end_ymd, rows_ingested, status, details_json, created_at, updated_at)
            VALUES (?, ?, 'manual_import', '', '', 0, 'started', ?, ?, ?)
            """,
            (ingest_run_id, channel_row_id, json.dumps({"report_type": report_type, "csv_path": str(csv_path)}), started, started),
        )
        count = 0
        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.db.execute(
                    """
                    INSERT OR REPLACE INTO revenue_records(id, channel_row_id, date_ymd, currency, amount_micros, source, created_at)
                    VALUES (?, ?, ?, ?, ?, 'manual_import', ?)
                    """,
                    (
                        f"rev_{channel_row_id}_{row['date']}",
                        channel_row_id,
                        row["date"],
                        row.get("currency", "USD"),
                        int(float(row.get("amount", "0")) * 1_000_000),
                        int(time.time()),
                    ),
                )
                count += 1
        completed = int(time.time())
        self.db.execute(
            """
            UPDATE analytics_ingest_runs
            SET rows_ingested = ?, status = 'succeeded', updated_at = ?
            WHERE id = ?
            """,
            (count, completed, ingest_run_id),
        )
        self.db.commit()
        return count


class NicheNotebook:
    def __init__(self, db):
        self.db = db

    def add_keyword(self, keyword: str) -> str:
        kid = f"kw_{int(time.time() * 1000)}"
        self.db.execute(
            "INSERT INTO niche_keywords(id, channel_row_id, keyword, created_at) VALUES (?, NULL, ?, ?)",
            (kid, keyword, int(time.time())),
        )
        self.db.commit()
        return kid

    def add_note(self, keyword_id: str, text: str) -> str:
        nid = f"note_{int(time.time() * 1000)}"
        now = int(time.time())
        self.db.execute(
            "INSERT INTO niche_notes(id, keyword_id, note_text, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (nid, keyword_id, text, now, now),
        )
        self.db.commit()
        return nid

    def list_keywords(self, limit: int = 200) -> list[dict]:
        rows = self.db.execute(
            "SELECT id, keyword, created_at FROM niche_keywords ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_notes(self, keyword_id: str, limit: int = 500) -> list[dict]:
        rows = self.db.execute(
            "SELECT id, keyword_id, note_text, created_at, updated_at FROM niche_notes WHERE keyword_id = ? ORDER BY updated_at DESC LIMIT ?",
            (keyword_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def estimate_quota_for_lookup(self, terms: list[str]) -> dict:
        estimated_units = max(1, len(terms)) * 100
        return {"estimated_units": estimated_units, "availability": AvailabilityStateV1(True, "", False).to_dict()}

    def run_optional_lookup(self, terms: list[str], quota_budget: int = 10000, quota_used: int = 0) -> dict:
        estimated = self.estimate_quota_for_lookup(terms)
        estimated_units = int(estimated["estimated_units"])
        remaining = quota_budget - quota_used
        if estimated_units > remaining:
            return {
                "ok": False,
                "results": [],
                "estimated_units": estimated_units,
                "availability": AvailabilityStateV1(False, "E_QUOTA_BUDGET_EXCEEDED", True).to_dict(),
            }
        results = [{"term": t, "score": 0.5, "source": "manual_notebook"} for t in terms]
        return {
            "ok": True,
            "results": results,
            "estimated_units": estimated_units,
            "availability": AvailabilityStateV1(True, "", False).to_dict(),
        }
