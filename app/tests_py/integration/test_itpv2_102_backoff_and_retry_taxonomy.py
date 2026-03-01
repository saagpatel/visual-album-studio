from vas_studio import DistributionSchedulingServiceV1


def test_itpv2_102_backoff_retry_and_blackout_paths(runtime):
    scheduler = DistributionSchedulingServiceV1(runtime.db, max_backoff_seconds=600)

    jobs = [
        {
            "job_id": "job_high_priority",
            "provider": "x",
            "priority": 90,
            "quota_budget": 1000,
            "quota_used": 100,
            "estimated_units": 100,
            "attempt": 1,
            "retryable": False,
        },
        {
            "job_id": "job_retryable",
            "provider": "x",
            "priority": 60,
            "quota_budget": 1000,
            "quota_used": 500,
            "estimated_units": 100,
            "attempt": 3,
            "retryable": True,
            "error_code": "E_X_TRANSIENT",
        },
        {
            "job_id": "job_quota_deferred",
            "provider": "facebook_reels",
            "priority": 99,
            "quota_budget": 100,
            "quota_used": 20,
            "estimated_units": 200,
            "attempt": 1,
            "retryable": False,
        },
    ]

    plan = scheduler.optimize_schedule(jobs, provider_policies={"facebook_reels": {"blackout_hours": []}})

    assert plan["ok"] is True
    scheduled = plan["plan"]["scheduled_jobs"]
    deferred = plan["plan"]["deferred_jobs"]

    assert any(item["job_id"] == "job_high_priority" for item in scheduled)
    retry_item = next(item for item in scheduled if item["job_id"] == "job_retryable")
    assert retry_item["detail"]["retry_policy"]["reason"] == "E_X_TRANSIENT"
    assert retry_item["detail"]["retry_policy"]["retry_after_seconds"] > 0

    quota_item = next(item for item in deferred if item["job_id"] == "job_quota_deferred")
    assert quota_item["detail"]["error_code"] == "E_PROVIDER_QUOTA_EXCEEDED"

    rows = runtime.db.execute("SELECT COUNT(*) AS c FROM distribution_schedule_plans").fetchone()
    assert int(rows["c"]) == 3
