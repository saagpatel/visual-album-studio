from vas_studio import DistributionServiceV2, make_request


def test_itv2_301_distribution_adapter_contract_records_publish_jobs(runtime, test_root):
    video = test_root / "fixtures" / "itv2301_contract.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"distribution-v2")

    service = DistributionServiceV2(runtime.db)
    request = make_request(
        provider="tiktok",
        channel_profile_id="channel_primary",
        file_path=str(video),
        title="contract pass",
    )
    result = service.publish(request)
    row = runtime.db.execute(
        "SELECT provider, status, retryable FROM distribution_publish_jobs WHERE channel_profile_id = ?",
        ("channel_primary",),
    ).fetchone()

    assert result["ok"] is True
    assert result["provider"] == "tiktok"
    assert row is not None
    assert row["provider"] == "tiktok"
    assert row["status"] == "succeeded"
    assert int(row["retryable"]) == 0


def test_itv2_301_distribution_adapter_contract_rejects_unknown_provider(runtime, test_root):
    video = test_root / "fixtures" / "itv2301_unknown.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"distribution-v2")

    service = DistributionServiceV2(runtime.db)
    request = make_request(
        provider="unknown",
        channel_profile_id="channel_unknown",
        file_path=str(video),
        title="unknown",
    )
    result = service.publish(request)

    assert result["ok"] is False
    assert result["error_code"] == "E_PROVIDER_UNSUPPORTED"
