from vas_studio import SchedulerSimulationDashboardV1


def test_tsnc_102_simulation_groups_providers(runtime):
    dashboard = SchedulerSimulationDashboardV1(runtime.db)
    result = dashboard.simulate(
        jobs=[
            {"job_id": "a", "provider": "x", "priority": 80, "quota_budget": 1000, "quota_used": 100, "estimated_units": 100},
            {"job_id": "b", "provider": "facebook_reels", "priority": 70, "quota_budget": 1000, "quota_used": 200, "estimated_units": 100},
        ]
    )

    assert result["ok"] is True
    assert len(result["side_by_side"]) == 2


def test_tsnc_102_deferred_job_visible(runtime):
    dashboard = SchedulerSimulationDashboardV1(runtime.db)
    result = dashboard.simulate(
        jobs=[
            {"job_id": "a", "provider": "x", "priority": 80, "quota_budget": 100, "quota_used": 90, "estimated_units": 30},
        ]
    )

    assert result["deferred_total"] == 1
    assert result["scheduled_total"] == 0


def test_tsnc_102_latest_simulation_empty_ok(runtime):
    dashboard = SchedulerSimulationDashboardV1(runtime.db)
    rows = dashboard.latest_simulation(provider="unknown")

    assert rows["ok"] is True
    assert rows["runs"] == []
