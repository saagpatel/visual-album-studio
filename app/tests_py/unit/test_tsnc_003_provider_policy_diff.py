from vas_studio import ProviderPolicyWatcherV1


def test_tsnc_003_diff_detects_added_changed_removed(runtime):
    watcher = ProviderPolicyWatcherV1(runtime.db)

    previous = {
        "quota": {"daily": 10000, "upload": 1600},
        "policy": {"requires_disclosure": False},
        "blackout_hours": [2, 3],
    }
    current = {
        "quota": {"daily": 12000, "upload": 1600},
        "policy": {"requires_disclosure": True},
        "compliance": {"requires_music_rights": True},
    }

    diff = watcher._diff("youtube", previous, current)

    assert "quota.daily" in diff.changed_fields
    assert "policy.requires_disclosure" in diff.changed_fields
    assert "compliance.requires_music_rights" in diff.added_fields
    assert "blackout_hours" in diff.removed_fields


def test_tsnc_003_first_ingest_is_baseline(runtime):
    watcher = ProviderPolicyWatcherV1(runtime.db)
    result = watcher.ingest_policy(provider="youtube", policy={"quota": {"daily": 10000}}, source="test")

    assert result["ok"] is True
    assert result["baseline"] is True
    assert result["changed"] is False


def test_tsnc_003_reingest_unchanged_has_no_changelog(runtime):
    watcher = ProviderPolicyWatcherV1(runtime.db)
    policy = {"quota": {"daily": 10000}, "policy": {"requires_disclosure": False}}

    watcher.ingest_policy(provider="youtube", policy=policy, source="test")
    second = watcher.ingest_policy(provider="youtube", policy=policy, source="test")

    rows = runtime.db.execute("SELECT COUNT(*) AS c FROM provider_policy_changelog WHERE provider = 'youtube'").fetchone()

    assert second["changed"] is False
    assert int(rows["c"]) == 0
