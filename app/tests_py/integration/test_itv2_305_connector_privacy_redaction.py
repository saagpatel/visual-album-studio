import json

from vas_studio import DistributionServiceV2


def test_itv2_305_connector_privacy_redaction_masks_sensitive_keys(runtime):
    service = DistributionServiceV2(runtime.db)
    diag_id = service.log_connector_diagnostic(
        "tiktok",
        {
            "access_token": "abc",
            "nested": {
                "refresh_token": "def",
                "Authorization": "Bearer token",
            },
            "normal_value": "ok",
        },
        project_id="project_itv2305_a",
    )
    row = runtime.db.execute("SELECT payload_json FROM connector_diagnostics WHERE id = ?", (diag_id,)).fetchone()
    payload = json.loads(row["payload_json"])

    assert payload["access_token"] == "[REDACTED]"
    assert payload["nested"]["refresh_token"] == "[REDACTED]"
    assert payload["nested"]["Authorization"] == "[REDACTED]"
    assert payload["normal_value"] == "ok"


def test_itv2_305_connector_privacy_redaction_masks_sensitive_text(runtime):
    service = DistributionServiceV2(runtime.db)
    diag_id = service.log_connector_diagnostic(
        "instagram",
        {
            "message": "Bearer abcdef",
            "details": ["keep", "refresh_token=xyz"],
        },
        project_id="project_itv2305_b",
    )
    row = runtime.db.execute("SELECT payload_json FROM connector_diagnostics WHERE id = ?", (diag_id,)).fetchone()
    payload = json.loads(row["payload_json"])

    assert payload["message"] == "[REDACTED]"
    assert payload["details"][0] == "keep"
    assert payload["details"][1] == "[REDACTED]"
