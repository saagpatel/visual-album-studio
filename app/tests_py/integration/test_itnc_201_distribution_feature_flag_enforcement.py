from vas_studio import DistributionServiceV2, ProviderFeatureFlagServiceV1, make_request


def test_itnc_201_distribution_respects_feature_flags(runtime, test_root):
    video = test_root / "fixtures" / "itnc201.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"itnc201")

    flags = ProviderFeatureFlagServiceV1(runtime.db)
    flags.set_flag(provider="linkedin", enabled=False, rollout_stage="canary", candidate=True)

    service = DistributionServiceV2(runtime.db, feature_flags=flags)

    disabled = service.preflight_publish(
        make_request(
            provider="linkedin",
            channel_profile_id="ln_1",
            file_path=str(video),
            title="disabled",
            metadata={"allow_missing_file": True},
        )
    )

    flags.set_flag(provider="linkedin", enabled=True, rollout_stage="beta", candidate=True)
    enabled = service.preflight_publish(
        make_request(
            provider="linkedin",
            channel_profile_id="ln_1",
            file_path=str(video),
            title="enabled",
            metadata={"allow_missing_file": True},
        )
    )

    assert disabled["ok"] is False
    assert disabled["error_code"] == "E_PROVIDER_FEATURE_DISABLED"
    assert enabled["ok"] is False
    assert enabled["error_code"] == "E_PROVIDER_UNSUPPORTED"
