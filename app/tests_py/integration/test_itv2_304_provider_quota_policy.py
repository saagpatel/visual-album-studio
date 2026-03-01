from vas_studio import DistributionServiceV2, make_request


def test_itv2_304_provider_quota_policy_blocks_over_budget(runtime, test_root):
    video = test_root / "fixtures" / "itv2304_quota.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"distribution-v2")

    service = DistributionServiceV2(runtime.db)
    tiktok_quota_fail = make_request(
        provider="tiktok",
        channel_profile_id="channel_tiktok_quota",
        file_path=str(video),
        title="quota fail",
        quota_budget=100,
        quota_used=20,
    )
    instagram_quota_fail = make_request(
        provider="instagram",
        channel_profile_id="channel_instagram_quota",
        file_path=str(video),
        title="quota fail",
        quota_budget=100,
        quota_used=0,
    )

    result_tiktok = service.publish(tiktok_quota_fail)
    result_instagram = service.publish(instagram_quota_fail)

    assert result_tiktok["ok"] is False
    assert result_tiktok["error_code"] == "E_PROVIDER_QUOTA_EXCEEDED"
    assert result_tiktok["http_status"] == 429
    assert result_instagram["ok"] is False
    assert result_instagram["error_code"] == "E_PROVIDER_QUOTA_EXCEEDED"
    assert result_instagram["http_status"] == 429


def test_itv2_304_provider_quota_policy_records_failure_taxonomy(runtime, test_root):
    video = test_root / "fixtures" / "itv2304_policy.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"distribution-v2")

    service = DistributionServiceV2(runtime.db)
    blocked = make_request(
        provider="instagram",
        channel_profile_id="channel_instagram_policy",
        file_path=str(video),
        title="policy",
        metadata={"simulate_policy_block": True},
    )
    retryable = make_request(
        provider="instagram",
        channel_profile_id="channel_instagram_retry",
        file_path=str(video),
        title="retry",
        metadata={"simulate_retryable": True},
    )

    blocked_result = service.publish(blocked)
    retryable_result = service.publish(retryable)

    assert blocked_result["ok"] is False
    assert blocked_result["retryable"] is False
    assert blocked_result["error_code"] == "E_INSTAGRAM_POLICY_BLOCKED"
    assert retryable_result["ok"] is False
    assert retryable_result["retryable"] is True
    assert retryable_result["error_code"] == "E_INSTAGRAM_TRANSIENT"
