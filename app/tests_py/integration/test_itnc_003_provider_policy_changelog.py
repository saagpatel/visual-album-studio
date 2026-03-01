from vas_studio import ProviderPolicyWatcherV1


def test_itnc_003_ingest_snapshot_records_changes_and_recommendations(runtime):
    watcher = ProviderPolicyWatcherV1(runtime.db)

    baseline = {
        "youtube": {"quota": {"daily": 10000}, "policy": {"requires_disclosure": False}},
        "x": {"quota": {"daily": 5000}, "policy": {"requires_disclosure": False}},
    }
    changed = {
        "youtube": {"quota": {"daily": 12000}, "policy": {"requires_disclosure": True}},
        "x": {"quota": {"daily": 5000}, "policy": {"requires_disclosure": False}},
    }

    first = watcher.ingest_snapshot(snapshot=baseline, source="integration")
    second = watcher.ingest_snapshot(snapshot=changed, source="integration")

    assert first["ok"] is True
    assert first["changes_detected"] == 0
    assert second["ok"] is True
    assert second["changes_detected"] == 1

    changes = watcher.recent_changes(provider="youtube", limit=5)
    assert changes["ok"] is True
    assert len(changes["changes"]) == 1
    assert "quota.daily" in changes["changes"][0]["changed_fields"]

    triage = watcher.triage_recommendations(provider="youtube", limit=5)
    assert triage["ok"] is True
    assert len(triage["recommendations"]) == 1
    assert any("quota" in rec for rec in triage["recommendations"][0]["recommendations"])

    run_rows = runtime.db.execute("SELECT COUNT(*) AS c FROM provider_policy_watch_runs").fetchone()
    assert int(run_rows["c"]) == 2
