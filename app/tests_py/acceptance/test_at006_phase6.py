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

    notebook = NicheNotebook(runtime.db)
    kid = notebook.add_keyword("ambient study music")
    nid = notebook.add_note(kid, "offline note")
    assert kid.startswith("kw_")
    assert nid.startswith("note_")

    row = runtime.db.execute("SELECT COUNT(*) AS c FROM analytics_snapshots WHERE channel_row_id = 'ch6'").fetchone()
    assert int(row["c"]) >= 90
