from vas_studio import DistributionServiceV2, make_request


def test_itpv2_101_x_publish_flow_success(runtime, test_root):
    video = test_root / "fixtures" / "itpv2101_x_success.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"pv2-101")

    service = DistributionServiceV2(runtime.db)
    request = make_request(
        provider="x",
        channel_profile_id="channel_x_success",
        file_path=str(video),
        title="X Success",
        description="post body",
    )
    result = service.publish(request)

    assert result["ok"] is True
    assert result["provider"] == "x"
    assert result["publish_id"].startswith("x_")


def test_itpv2_101_x_publish_flow_rejects_long_content(runtime, test_root):
    video = test_root / "fixtures" / "itpv2101_x_invalid.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"pv2-101")

    service = DistributionServiceV2(runtime.db)
    too_long = make_request(
        provider="x",
        channel_profile_id="channel_x_fail",
        file_path=str(video),
        title="x" * 200,
        description="y" * 90,
    )
    result = service.publish(too_long)

    assert result["ok"] is False
    assert result["error_code"] == "E_X_TEXT_TOO_LONG"
    assert result["http_status"] == 400
