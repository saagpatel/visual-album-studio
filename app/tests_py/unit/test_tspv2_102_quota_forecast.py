from vas_studio import DistributionSchedulingServiceV1


def test_tspv2_102_quota_forecast_within_budget():
    scheduler = DistributionSchedulingServiceV1()
    forecast = scheduler.forecast_quota("x", quota_budget=1000, quota_used=200, pending_units=100)

    assert forecast.provider == "x"
    assert forecast.remaining_after == 700
    assert forecast.within_budget is True


def test_tspv2_102_quota_forecast_exceeded_and_non_retryable_policy():
    scheduler = DistributionSchedulingServiceV1()
    forecast = scheduler.forecast_quota("facebook_reels", quota_budget=100, quota_used=40, pending_units=70)
    policy = scheduler.retry_policy(provider="facebook_reels", attempt=1, retryable=False, error_code="E_POLICY")

    assert forecast.within_budget is False
    assert forecast.remaining_after < 0
    assert policy.retry_after_seconds == 0
    assert policy.max_attempts == 1


def test_tspv2_102_retry_policy_backoff_growth_capped():
    scheduler = DistributionSchedulingServiceV1(max_backoff_seconds=300)

    second = scheduler.retry_policy(provider="x", attempt=2, retryable=True)
    fifth = scheduler.retry_policy(provider="x", attempt=5, retryable=True)

    assert second.retry_after_seconds == 60
    assert fifth.retry_after_seconds == 300
    assert fifth.max_attempts == 5
