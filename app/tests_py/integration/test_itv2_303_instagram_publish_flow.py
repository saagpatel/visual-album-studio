from vas_studio import DistributionServiceV2, make_request


def test_itv2_303_instagram_publish_flow_success(runtime, test_root):
    video = test_root / "fixtures" / "itv2303_instagram.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"distribution-v2")

    service = DistributionServiceV2(runtime.db)
    request = make_request(
        provider="instagram",
        channel_profile_id="channel_instagram_success",
        file_path=str(video),
        title="Instagram Success",
        description="caption",
    )
    result = service.publish(request)

    assert result["ok"] is True
    assert result["provider"] == "instagram"
    assert result["state"] == "succeeded"
    assert result["publish_id"].startswith("ig_")


def test_itv2_303_instagram_publish_flow_rejects_invalid_caption(runtime, test_root):
    video = test_root / "fixtures" / "itv2303_instagram_invalid.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"distribution-v2")

    service = DistributionServiceV2(runtime.db)
    too_long = make_request(
        provider="instagram",
        channel_profile_id="channel_instagram_fail",
        file_path=str(video),
        title="Instagram Long",
        description="x" * 2201,
    )
    result = service.publish(too_long)

    assert result["ok"] is False
    assert result["error_code"] == "E_INSTAGRAM_CAPTION_TOO_LONG"
    assert result["http_status"] == 400
