from pathlib import Path

from vas_studio import AnalyticsService


def test_it007_analytics_ingestion(runtime, test_root: Path):
    runtime.db.execute(
        "INSERT INTO oauth_profiles(id, provider, display_name, keyring_account, created_at, updated_at) VALUES ('op1', 'youtube', 'test', 'acc', 0, 0)"
    )
    runtime.db.execute(
        "INSERT INTO channels(id, oauth_profile_id, channel_id, channel_title, created_at, updated_at) VALUES ('ch1', 'op1', 'cid', 'title', 0, 0)"
    )
    runtime.db.commit()

    analytics = AnalyticsService(runtime.db)
    sid = analytics.store_snapshot("ch1", "2026-01-01", "2026-01-07", {"views": 123})
    assert sid.startswith("snapshot_")

    dashboard = analytics.get_dashboard_snapshot("ch1", "2026-01-01", "2026-01-31")
    assert dashboard["snapshot_count"] >= 1
    assert "last_synced_at" in dashboard

    csv_path = test_root / "report.csv"
    csv_path.write_text("date,currency,amount\n2026-01-01,USD,1.23\n", encoding="utf-8")
    count = analytics.import_reporting_csv("ch1", csv_path, "revenue")
    assert count == 1

    incremental = analytics.run_incremental_sync(
        "ch1",
        "2026-01-01",
        "2026-01-31",
        rows=[{"date_ymd": "2026-01-01", "metrics": {"views": 50}}, {"date_ymd": "2026-01-02", "metrics": {"views": 60}}],
    )
    assert incremental["status"] == "succeeded"
    assert incremental["rows_ingested"] >= 1
