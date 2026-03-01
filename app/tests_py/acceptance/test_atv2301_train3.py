import json

from vas_studio import DistributionServiceV2, make_request


def test_atv2301_train3_provider_flows_quota_policy_and_redaction(runtime, test_root):
    video = test_root / "fixtures" / "atv2301.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"distribution-v2")

    service = DistributionServiceV2(runtime.db)
    tikok_success = make_request(
        provider="tiktok",
        channel_profile_id="atv2301_tiktok",
        file_path=str(video),
        title="TikTok Success",
        metadata={"trace_id": "t1"},
    )
    instagram_success = make_request(
        provider="instagram",
        channel_profile_id="atv2301_instagram",
        file_path=str(video),
        title="Instagram Success",
        description="train3 acceptance",
        metadata={"trace_id": "i1"},
    )
    quota_fail = make_request(
        provider="tiktok",
        channel_profile_id="atv2301_quota_fail",
        file_path=str(video),
        title="quota fail",
        quota_budget=100,
        quota_used=10,
    )
    policy_fail = make_request(
        provider="instagram",
        channel_profile_id="atv2301_policy_fail",
        file_path=str(video),
        title="policy fail",
        metadata={"simulate_policy_block": True},
    )

    tiktok_result = service.publish(tikok_success)
    instagram_result = service.publish(instagram_success)
    quota_result = service.publish(quota_fail)
    policy_result = service.publish(policy_fail)

    assert tiktok_result["ok"] is True
    assert tiktok_result["publish_id"].startswith("tt_")
    assert instagram_result["ok"] is True
    assert instagram_result["publish_id"].startswith("ig_")
    assert quota_result["ok"] is False
    assert quota_result["error_code"] == "E_PROVIDER_QUOTA_EXCEEDED"
    assert policy_result["ok"] is False
    assert policy_result["error_code"] == "E_INSTAGRAM_POLICY_BLOCKED"

    diag_id = service.log_connector_diagnostic(
        "instagram",
        {"access_token": "secret-token", "message": "Bearer token", "normal": "safe"},
        severity="warn",
    )
    row = runtime.db.execute("SELECT payload_json, severity FROM connector_diagnostics WHERE id = ?", (diag_id,)).fetchone()
    payload = json.loads(row["payload_json"])
    assert row["severity"] == "warn"
    assert payload["access_token"] == "[REDACTED]"
    assert payload["message"] == "[REDACTED]"
    assert payload["normal"] == "safe"

    totals = runtime.db.execute(
        """
        SELECT
          SUM(CASE WHEN status = 'succeeded' THEN 1 ELSE 0 END) AS succeeded,
          SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed
        FROM distribution_publish_jobs
        """
    ).fetchone()
    assert int(totals["succeeded"]) >= 2
    assert int(totals["failed"]) >= 2
