from vas_studio import SchedulerSimulationDashboardV1


def test_itnc_102_policy_overlay_and_persistence(runtime):
    dashboard = SchedulerSimulationDashboardV1(runtime.db)
    result = dashboard.simulate(
        jobs=[
            {
                "job_id": "retry_job",
                "provider": "x",
                "priority": 60,
                "quota_budget": 1000,
                "quota_used": 500,
                "estimated_units": 100,
                "retryable": True,
                "attempt": 3,
                "error_code": "E_X_TRANSIENT",
            }
        ],
        provider_policies={"x": {"blackout_hours": []}},
    )

    assert result["ok"] is True
    latest = dashboard.latest_simulation(provider="x", limit=1)
    assert latest["ok"] is True
    assert len(latest["runs"]) == 1
    assert latest["runs"][0]["provider"] == "x"
