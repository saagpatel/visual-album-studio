from vas_studio import DistributionSchedulingServiceV1


def test_atpv2_102_scheduler_optimization(runtime):
    scheduler = DistributionSchedulingServiceV1(runtime.db, max_backoff_seconds=900)

    jobs = [
        {
            "job_id": "at_job_1",
            "provider": "x",
            "priority": 80,
            "quota_budget": 1000,
            "quota_used": 100,
            "estimated_units": 90,
            "attempt": 1,
            "retryable": False,
        },
        {
            "job_id": "at_job_2",
            "provider": "facebook_reels",
            "priority": 70,
            "quota_budget": 1000,
            "quota_used": 200,
            "estimated_units": 100,
            "attempt": 2,
            "retryable": True,
            "error_code": "E_FB_REELS_TRANSIENT",
        },
        {
            "job_id": "at_job_3",
            "provider": "facebook_reels",
            "priority": 65,
            "quota_budget": 100,
            "quota_used": 20,
            "estimated_units": 120,
            "attempt": 1,
            "retryable": False,
        },
    ]

    plan = scheduler.optimize_schedule(jobs)

    assert plan["ok"] is True
    scheduled = plan["plan"]["scheduled_jobs"]
    deferred = plan["plan"]["deferred_jobs"]

    assert len(scheduled) == 2
    assert len(deferred) == 1

    first = scheduled[0]
    assert first["job_id"] == "at_job_1"

    second = next(item for item in scheduled if item["job_id"] == "at_job_2")
    assert second["detail"]["retry_policy"]["reason"] == "E_FB_REELS_TRANSIENT"

    quota_deferred = deferred[0]
    assert quota_deferred["job_id"] == "at_job_3"
    assert quota_deferred["detail"]["reason"] == "quota_exceeded"
