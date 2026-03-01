from vas_studio import MultiRegionReplicationServiceV1


def test_itpv2_201_residency_routing(runtime):
    service = MultiRegionReplicationServiceV1(runtime.db)
    project_id = "project_itpv2_201_route"

    set_result = service.set_residency_policy(
        project_id=project_id,
        home_region="us-west-1",
        active_regions=["us-west-1", "us-east-1"],
        dr_region="eu-west-1",
    )
    assert set_result["ok"] is True

    preferred = service.route_region(
        project_id=project_id,
        preferred_region="us-east-1",
        available_regions=["us-east-1", "eu-west-1"],
    )
    assert preferred["ok"] is True
    assert preferred["region"] == "us-east-1"
    assert preferred["degraded"] is False

    failover = service.route_region(
        project_id=project_id,
        preferred_region="us-west-1",
        available_regions=["eu-west-1"],
    )
    assert failover["ok"] is True
    assert failover["region"] == "eu-west-1"
    assert failover["reason"] == "dr_failover"

    local_only = service.route_region(project_id=project_id, available_regions=[])
    assert local_only["ok"] is False
    assert local_only["error_code"] == "E_REGION_UNAVAILABLE"
