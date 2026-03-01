import json

from vas_studio import ProductizationService


def test_itv2_511_provenance_closeout_bundle_sign_verify_and_redact(runtime, test_root, monkeypatch):
    monkeypatch.setenv("VAS_RELEASE_SIGNING_KEY", "test-signing-key")
    service = ProductizationService(runtime.db, out_dir=test_root / "out")

    signed = service.sign_release_manifest(profile_id="v2_closeout_profile", channel="canary")
    assert signed["ok"] is True
    signature_payload = signed["signature"]
    assert signature_payload["schema_version"] == 2
    assert signature_payload["gate_requirements"]["must_verify_signature"] is True

    verify = service.verify_release_manifest_signature(profile_id="v2_closeout_profile", channel="canary")
    assert verify["ok"] is True
    assert verify["valid"] is True

    promoted = service.promote_release_channel(
        profile_id="v2_closeout_profile",
        target_channel="beta",
        gate_report={"status": "pass", "gate_id": "AT-V2-501", "source_channel": "canary"},
    )
    assert promoted["ok"] is True
    assert promoted["state"]["current_channel"] == "beta"

    log_path = test_root / "out" / "logs" / "closeout.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("Authorization: Bearer secret-token\nnormal line\n", encoding="utf-8")
    diagnostics = service.export_diagnostics({"log_paths": [str(log_path)]})
    assert diagnostics["ok"] is True

    bundle_path = diagnostics["diagnostics"]["output_path"]
    payload = json.loads(open(bundle_path, "r", encoding="utf-8").read())
    files = payload["payload"]["files"]
    assert len(files) == 1
    assert "[REDACTED]" in files[0]["content"]
