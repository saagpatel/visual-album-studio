import json

from vas_studio import DistributionServiceV2, make_request


def test_atpv2_101_provider_expansion_flow(runtime, test_root):
    video = test_root / "fixtures" / "atpv2101.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"pv2-101")

    service = DistributionServiceV2(runtime.db)

    fb_success = make_request(
        provider="facebook_reels",
        channel_profile_id="atpv2101_fb",
        file_path=str(video),
        title="Facebook Reels Success",
    )
    x_success = make_request(
        provider="x",
        channel_profile_id="atpv2101_x",
        file_path=str(video),
        title="X Success",
        description="Ship it",
    )
    quota_fail = make_request(
        provider="facebook_reels",
        channel_profile_id="atpv2101_quota_fail",
        file_path=str(video),
        title="quota fail",
        quota_budget=100,
        quota_used=10,
    )
    policy_fail = make_request(
        provider="x",
        channel_profile_id="atpv2101_policy_fail",
        file_path=str(video),
        title="policy fail",
        description="blocked",
        metadata={"simulate_policy_block": True},
    )

    fb_result = service.publish(fb_success)
    x_result = service.publish(x_success)
    quota_result = service.publish(quota_fail)
    policy_result = service.publish(policy_fail)

    assert fb_result["ok"] is True
    assert fb_result["publish_id"].startswith("fr_")
    assert x_result["ok"] is True
    assert x_result["publish_id"].startswith("x_")
    assert quota_result["ok"] is False
    assert quota_result["error_code"] == "E_PROVIDER_QUOTA_EXCEEDED"
    assert policy_result["ok"] is False
    assert policy_result["error_code"] == "E_X_POLICY_BLOCKED"

    diag_id = service.log_connector_diagnostic(
        "x",
        {"refresh_token": "secret-token", "message": "Bearer token", "normal": "safe"},
        severity="warn",
    )
    row = runtime.db.execute("SELECT payload_json FROM connector_diagnostics WHERE id = ?", (diag_id,)).fetchone()
    payload = json.loads(row["payload_json"])
    assert payload["refresh_token"] == "[REDACTED]"
    assert payload["message"] == "[REDACTED]"
    assert payload["normal"] == "safe"

    totals = runtime.db.execute(
        """
        SELECT
          SUM(CASE WHEN status = 'succeeded' THEN 1 ELSE 0 END) AS succeeded,
          SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed
        FROM distribution_publish_jobs
        WHERE provider IN ('facebook_reels', 'x')
        """
    ).fetchone()
    assert int(totals["succeeded"]) >= 2
    assert int(totals["failed"]) >= 2
