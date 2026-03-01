import json

from vas_studio import DistributionServiceV2, make_request


def test_itpv2_101_provider_policy_quota_and_redaction(runtime, test_root):
    video = test_root / "fixtures" / "itpv2101_provider_policy.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"pv2-101")

    service = DistributionServiceV2(runtime.db)

    quota_fail = make_request(
        provider="facebook_reels",
        channel_profile_id="channel_fb_quota_fail",
        file_path=str(video),
        title="quota fail",
        quota_budget=100,
        quota_used=10,
    )
    policy_fail = make_request(
        provider="x",
        channel_profile_id="channel_x_policy_fail",
        file_path=str(video),
        title="policy",
        description="fail",
        metadata={"simulate_policy_block": True},
    )

    quota_result = service.publish(quota_fail)
    policy_result = service.publish(policy_fail)

    assert quota_result["ok"] is False
    assert quota_result["error_code"] == "E_PROVIDER_QUOTA_EXCEEDED"
    assert policy_result["ok"] is False
    assert policy_result["error_code"] == "E_X_POLICY_BLOCKED"

    diag_id = service.log_connector_diagnostic(
        "facebook_reels",
        {"access_token": "secret-token", "message": "Bearer token", "normal": "safe"},
        severity="warn",
        project_id="project_itpv2_101",
    )
    row = runtime.db.execute("SELECT payload_json, severity FROM connector_diagnostics WHERE id = ?", (diag_id,)).fetchone()
    payload = json.loads(row["payload_json"])

    assert row["severity"] == "warn"
    assert payload["access_token"] == "[REDACTED]"
    assert payload["message"] == "[REDACTED]"
    assert payload["normal"] == "safe"
