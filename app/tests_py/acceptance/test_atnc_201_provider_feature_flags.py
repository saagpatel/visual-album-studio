from vas_studio import DistributionServiceV2, ProviderFeatureFlagServiceV1, make_request


def test_atnc_201_provider_feature_flags(runtime, test_root):
    video = test_root / "fixtures" / "atnc201.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"atnc201")

    flags = ProviderFeatureFlagServiceV1(runtime.db)
    service = DistributionServiceV2(runtime.db, feature_flags=flags)

    req = make_request(
        provider="snapchat",
        channel_profile_id="snap_1",
        file_path=str(video),
        title="candidate",
        metadata={"allow_missing_file": True},
    )

    blocked = service.publish(req)
    assert blocked["ok"] is False
    assert blocked["error_code"] == "E_PROVIDER_FEATURE_DISABLED"

    flags.set_flag(provider="snapchat", enabled=True, rollout_stage="canary", candidate=True)
    opened = service.publish(req)
    assert opened["ok"] is False
    assert opened["error_code"] == "E_PROVIDER_UNSUPPORTED"
