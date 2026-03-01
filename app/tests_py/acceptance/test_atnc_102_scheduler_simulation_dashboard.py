from vas_studio import SchedulerSimulationDashboardV1


def test_atnc_102_scheduler_simulation_dashboard(runtime):
    dashboard = SchedulerSimulationDashboardV1(runtime.db)
    result = dashboard.simulate(
        jobs=[
            {"job_id": "j1", "provider": "x", "priority": 90, "quota_budget": 1000, "quota_used": 100, "estimated_units": 90},
            {"job_id": "j2", "provider": "facebook_reels", "priority": 85, "quota_budget": 1000, "quota_used": 100, "estimated_units": 90},
            {"job_id": "j3", "provider": "facebook_reels", "priority": 40, "quota_budget": 100, "quota_used": 90, "estimated_units": 50},
        ]
    )

    assert result["ok"] is True
    assert result["scheduled_total"] == 2
    assert result["deferred_total"] == 1
    providers = {row["provider"] for row in result["side_by_side"]}
    assert providers == {"x", "facebook_reels"}
