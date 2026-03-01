from vas_studio import ProviderPolicyPreflight, TikTokDistributionAdapter, make_request


def test_tsv2_302_policy_preflight_quota_checks(test_root):
    video = test_root / "fixtures" / "distribution_quota.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"mp4-placeholder")

    request_ok = make_request(
        provider="tiktok",
        channel_profile_id="channelA",
        file_path=str(video),
        title="quota pass",
        quota_budget=500,
        quota_used=200,
    )
    request_fail = make_request(
        provider="tiktok",
        channel_profile_id="channelA",
        file_path=str(video),
        title="quota fail",
        quota_budget=200,
        quota_used=150,
    )

    ok = ProviderPolicyPreflight.check_quota(request_ok, estimated_units=100)
    fail = ProviderPolicyPreflight.check_quota(request_fail, estimated_units=100)

    assert ok.ok is True
    assert ok.state == "preflight_ok"
    assert fail.ok is False
    assert fail.error_code == "E_PROVIDER_QUOTA_EXCEEDED"
    assert fail.http_status == 429


def test_tsv2_302_provider_policy_controls_reject_invalid_title_and_allow_retryable(test_root):
    video = test_root / "fixtures" / "distribution_policy.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"mp4-placeholder")
    adapter = TikTokDistributionAdapter()

    invalid_title = make_request(
        provider="tiktok",
        channel_profile_id="channelA",
        file_path=str(video),
        title=" ",
    )
    retryable = make_request(
        provider="tiktok",
        channel_profile_id="channelA",
        file_path=str(video),
        title="retryable",
        metadata={"simulate_retryable": True},
    )

    preflight = adapter.preflight(invalid_title)
    result = adapter.publish(retryable)

    assert preflight.ok is False
    assert preflight.error_code == "E_TIKTOK_TITLE_REQUIRED"
    assert result.ok is False
    assert result.retryable is True
    assert result.error_code == "E_TIKTOK_TRANSIENT"
