from vas_studio import DistributionAdapter, DistributionServiceV2, ProviderPublishStatusV1, make_request


class _EchoAdapter(DistributionAdapter):
    provider = "echo"

    def preflight(self, request):
        return ProviderPublishStatusV1(self.provider, True, "preflight_ok", details={"title": request.title})

    def publish(self, request):
        return ProviderPublishStatusV1(self.provider, True, "succeeded", publish_id=f"echo_{request.channel_profile_id}")


def test_tsv2_301_distribution_adapter_contract_accepts_custom_provider(test_root):
    video = test_root / "fixtures" / "distribution_contract.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"mp4-placeholder")

    service = DistributionServiceV2()
    service.register_adapter(_EchoAdapter())

    request = make_request(
        provider="echo",
        channel_profile_id="channelA",
        file_path=str(video),
        title="contract test",
    )
    preflight = service.preflight_publish(request)
    publish = service.publish(request)

    assert preflight["ok"] is True
    assert preflight["provider"] == "echo"
    assert preflight["schema_version"] == 1
    assert publish["ok"] is True
    assert publish["state"] == "succeeded"
    assert publish["publish_id"].startswith("echo_")


def test_tsv2_301_distribution_adapter_contract_rejects_unknown_provider(test_root):
    video = test_root / "fixtures" / "distribution_unknown.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"mp4-placeholder")

    service = DistributionServiceV2()
    request = make_request(
        provider="unsupported",
        channel_profile_id="channelA",
        file_path=str(video),
        title="unsupported",
    )

    preflight = service.preflight_publish(request)
    publish = service.publish(request)

    assert preflight["ok"] is False
    assert preflight["error_code"] == "E_PROVIDER_UNSUPPORTED"
    assert publish["ok"] is False
    assert publish["error_code"] == "E_PROVIDER_UNSUPPORTED"
