from vas_studio import DistributionServiceV2, make_request


def test_itv2_302_tiktok_publish_flow_success(runtime, test_root):
    video = test_root / "fixtures" / "itv2302_tiktok.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"distribution-v2")

    service = DistributionServiceV2(runtime.db)
    request = make_request(
        provider="tiktok",
        channel_profile_id="channel_tiktok_success",
        file_path=str(video),
        title="TikTok Success",
    )
    result = service.publish(request)

    assert result["ok"] is True
    assert result["provider"] == "tiktok"
    assert result["state"] == "succeeded"
    assert result["publish_id"].startswith("tt_")


def test_itv2_302_tiktok_publish_flow_handles_policy_and_retryable(runtime, test_root):
    video = test_root / "fixtures" / "itv2302_tiktok_policy.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"distribution-v2")

    service = DistributionServiceV2(runtime.db)
    blocked = make_request(
        provider="tiktok",
        channel_profile_id="channel_tiktok_blocked",
        file_path=str(video),
        title="blocked",
        metadata={"simulate_policy_block": True},
    )
    retryable = make_request(
        provider="tiktok",
        channel_profile_id="channel_tiktok_retryable",
        file_path=str(video),
        title="retry",
        metadata={"simulate_retryable": True},
    )

    blocked_result = service.publish(blocked)
    retryable_result = service.publish(retryable)

    assert blocked_result["ok"] is False
    assert blocked_result["error_code"] == "E_TIKTOK_POLICY_BLOCKED"
    assert retryable_result["ok"] is False
    assert retryable_result["retryable"] is True
    assert retryable_result["error_code"] == "E_TIKTOK_TRANSIENT"
