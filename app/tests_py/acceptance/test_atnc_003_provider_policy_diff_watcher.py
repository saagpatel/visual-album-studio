from vas_studio import ProviderPolicyWatcherV1


def test_atnc_003_provider_policy_diff_watcher(runtime):
    watcher = ProviderPolicyWatcherV1(runtime.db)

    snapshot_v1 = {
        "youtube": {
            "quota": {"daily": 10000, "upload": 1600},
            "policy": {"requires_disclosure": False},
            "blackout_hours": [2, 3],
        },
        "instagram": {
            "quota": {"daily": 7000},
            "policy": {"requires_disclosure": False},
        },
    }
    snapshot_v2 = {
        "youtube": {
            "quota": {"daily": 8000, "upload": 1600},
            "policy": {"requires_disclosure": True},
            "blackout_hours": [4, 5],
        },
        "instagram": {
            "quota": {"daily": 7000},
            "policy": {"requires_disclosure": False},
        },
    }

    baseline = watcher.ingest_snapshot(snapshot=snapshot_v1, source="acceptance")
    delta = watcher.ingest_snapshot(snapshot=snapshot_v2, source="acceptance")

    assert baseline["ok"] is True
    assert baseline["changes_detected"] == 0
    assert delta["ok"] is True
    assert delta["changes_detected"] == 1

    recent = watcher.recent_changes(provider="youtube", limit=10)
    assert recent["ok"] is True
    assert len(recent["changes"]) == 1
    change = recent["changes"][0]
    assert "quota.daily" in change["changed_fields"]
    assert "policy.requires_disclosure" in change["changed_fields"]

    triage = watcher.triage_recommendations(provider="youtube", limit=10)
    assert triage["ok"] is True
    assert len(triage["recommendations"]) == 1
    assert triage["recommendations"][0]["provider"] == "youtube"
    assert len(triage["recommendations"][0]["recommendations"]) >= 1
