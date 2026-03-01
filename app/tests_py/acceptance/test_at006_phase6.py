from pathlib import Path

from vas_studio import AnalyticsService, NicheNotebook


def test_at006_analytics_revenue_niche(runtime, test_root: Path):
    runtime.db.execute(
        "INSERT INTO oauth_profiles(id, provider, display_name, keyring_account, created_at, updated_at) VALUES ('op6', 'youtube', 'p', 'acc6', 0, 0)"
    )
    runtime.db.execute(
        "INSERT INTO channels(id, oauth_profile_id, channel_id, channel_title, created_at, updated_at) VALUES ('ch6', 'op6', 'cid6', 'title6', 0, 0)"
    )
    runtime.db.commit()

    analytics = AnalyticsService(runtime.db)
    for day in range(1, 91):
        analytics.store_snapshot("ch6", f"2026-01-{day:02d}" if day <= 31 else "2026-02-01", "2026-02-01", {"views": day})

    incremental = analytics.run_incremental_sync(
        "ch6",
        "2026-01-01",
        "2026-02-01",
        rows=[{"date_ymd": "2026-01-01", "metrics": {"views": 1}}, {"date_ymd": "2026-01-10", "metrics": {"views": 2}}],
    )
    assert incremental["status"] == "succeeded"
    assert incremental["ingest_run_id"].startswith("ingest_")
    dashboard = analytics.get_dashboard_snapshot("ch6", "2026-01-01", "2026-02-01")
    assert "availability" in dashboard

    notebook = NicheNotebook(runtime.db)
    kid = notebook.add_keyword("ambient study music")
    nid = notebook.add_note(kid, "offline note")
    assert kid.startswith("kw_")
    assert nid.startswith("note_")
    assert len(notebook.list_keywords()) >= 1
    assert len(notebook.list_notes(kid)) >= 1
    lookup = notebook.run_optional_lookup(["ambient", "study"], quota_budget=500, quota_used=0)
    assert lookup["ok"] is True

    row = runtime.db.execute("SELECT COUNT(*) AS c FROM analytics_snapshots WHERE channel_row_id = 'ch6'").fetchone()
    assert int(row["c"]) >= 90
