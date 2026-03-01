from vas_studio import MultiRegionReplicationServiceV1


def test_atpv2_201_multiregion_replication(runtime):
    service = MultiRegionReplicationServiceV1(runtime.db)
    project_id = "project_atpv2_201"

    policy = service.set_residency_policy(
        project_id=project_id,
        home_region="us-west-1",
        active_regions=["us-west-1", "us-east-1"],
        dr_region="eu-west-1",
        allowed_regions=["us-west-1", "us-east-1", "eu-west-1"],
    )
    assert policy["ok"] is True
    assert policy["constraint"]["home_region"] == "us-west-1"

    first = service.replicate_envelope(
        project_id=project_id,
        sequence=10,
        envelope={"operation": "upsert_asset", "asset_id": "a1"},
        available_regions=["us-west-1", "us-east-1"],
    )
    assert first["ok"] is True
    assert first["succeeded"] == 2
    assert first["pending"] == 1

    route = service.route_region(
        project_id=project_id,
        preferred_region="us-west-1",
        available_regions=["eu-west-1"],
    )
    assert route["ok"] is True
    assert route["region"] == "eu-west-1"

    second = service.replicate_envelope(
        project_id=project_id,
        sequence=11,
        envelope={"operation": "upsert_asset", "asset_id": "a2"},
        available_regions=["eu-west-1"],
    )
    assert second["ok"] is True
    assert second["succeeded"] == 1
    assert second["pending"] == 2

    replay = service.replay_order(project_id=project_id)
    assert replay["ok"] is True
    assert len(replay["replay_order"]) == 6
