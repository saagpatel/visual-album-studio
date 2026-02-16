from __future__ import annotations

import csv
import json
import time
import uuid
from pathlib import Path


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

    def import_reporting_csv(self, channel_row_id: str, csv_path: Path, report_type: str) -> int:
        count = 0
        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.db.execute(
                    """
                    INSERT INTO revenue_records(id, channel_row_id, date_ymd, currency, amount_micros, source, created_at)
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
