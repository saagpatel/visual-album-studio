from vas_studio import MultiRegionReplicationServiceV1


def test_rtpv2_201_failover_replay_order(runtime):
    service = MultiRegionReplicationServiceV1(runtime.db)
    project_id = "project_rtpv2_201"

    service.set_residency_policy(
        project_id=project_id,
        home_region="us-west-1",
        active_regions=["us-west-1", "us-east-1"],
        dr_region="eu-west-1",
    )

    first = service.replicate_envelope(
        project_id=project_id,
        sequence=1,
        envelope={"operation": "set_title", "value": "A"},
        available_regions=["us-west-1", "eu-west-1"],
    )
    second = service.replicate_envelope(
        project_id=project_id,
        sequence=2,
        envelope={"operation": "set_title", "value": "B"},
        available_regions=["us-east-1", "eu-west-1"],
    )

    assert first["ok"] is True
    assert second["ok"] is True
    assert first["pending"] >= 1
    assert second["pending"] >= 1

    replay = service.replay_order(project_id=project_id)
    assert replay["ok"] is True

    sequences = [item["sequence"] for item in replay["replay_order"]]
    assert sequences == sorted(sequences)
    assert all(item["detail"]["local_first_continuity"] is True for item in replay["replay_order"])
