from vas_studio import DistributionServiceV2, make_request


def test_itpv2_101_facebook_reels_publish_flow_success(runtime, test_root):
    video = test_root / "fixtures" / "itpv2101_fr_success.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"pv2-101")

    service = DistributionServiceV2(runtime.db)
    request = make_request(
        provider="facebook_reels",
        channel_profile_id="channel_fb_success",
        file_path=str(video),
        title="Facebook Reels Success",
    )
    result = service.publish(request)

    assert result["ok"] is True
    assert result["provider"] == "facebook_reels"
    assert result["publish_id"].startswith("fr_")


def test_itpv2_101_facebook_reels_policy_and_retryable(runtime, test_root):
    video = test_root / "fixtures" / "itpv2101_fr_policy.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"pv2-101")

    service = DistributionServiceV2(runtime.db)
    blocked = make_request(
        provider="facebook_reels",
        channel_profile_id="channel_fb_blocked",
        file_path=str(video),
        title="blocked",
        metadata={"simulate_policy_block": True},
    )
    retryable = make_request(
        provider="facebook_reels",
        channel_profile_id="channel_fb_retry",
        file_path=str(video),
        title="retry",
        metadata={"simulate_retryable": True},
    )

    blocked_result = service.publish(blocked)
    retryable_result = service.publish(retryable)

    assert blocked_result["ok"] is False
    assert blocked_result["error_code"] == "E_FB_REELS_POLICY_BLOCKED"
    assert retryable_result["ok"] is False
    assert retryable_result["retryable"] is True
    assert retryable_result["error_code"] == "E_FB_REELS_TRANSIENT"
