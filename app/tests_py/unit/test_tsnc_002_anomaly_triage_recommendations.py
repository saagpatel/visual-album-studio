from vas_studio import AnomalyTriageServiceV1


def test_tsnc_002_recommendations_include_escalation_for_critical(runtime):
    service = AnomalyTriageServiceV1(runtime.db)
    recs = service._recommend("connector_error_spike", "critical")

    assert len(recs) >= 3
    assert "escalate" in recs[0]


def test_tsnc_002_recommendations_for_sync_failures(runtime):
    service = AnomalyTriageServiceV1(runtime.db)
    recs = service._recommend("sync_replay_failures", "error")

    assert any("replay" in item for item in recs)


def test_tsnc_002_unknown_signal_fallback(runtime):
    service = AnomalyTriageServiceV1(runtime.db)
    recs = service._recommend("unknown_type", "warn")

    assert len(recs) == 1
    assert "review anomaly" in recs[0]
