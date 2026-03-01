import json
import os
from pathlib import Path

from vas_studio import ProductizationService


def test_itv2_103_release_channel_promotion_path_and_gate(runtime, test_root: Path):
    svc = ProductizationService(runtime.db, out_dir=test_root / "out")
    os.environ["VAS_RELEASE_SIGNING_KEY"] = "itv2-103-signing-key"

    profile = "itv2_103_gate"
    signed = svc.sign_release_manifest(profile, channel="canary", signer_id="itv2")
    assert signed["ok"]

    blocked = svc.promote_release_channel(profile, "beta", gate_report={"status": "fail", "gate_id": "AT-V2-101"})
    assert blocked["ok"] is False
    assert blocked["error"] == "E_GATE_REQUIRED"

    promoted = svc.promote_release_channel(
        profile, "beta", gate_report={"status": "pass", "gate_id": "AT-V2-101", "source_channel": "canary"}
    )
    assert promoted["ok"]
    assert promoted["state"]["current_channel"] == "beta"

    skip_profile = "itv2_103_skip"
    assert svc.sign_release_manifest(skip_profile, channel="canary", signer_id="itv2")["ok"]
    skipped = svc.promote_release_channel(
        skip_profile, "stable", gate_report={"status": "pass", "gate_id": "AT-V2-101", "source_channel": "canary"}
    )
    assert skipped["ok"] is False
    assert skipped["error"] == "E_CHANNEL_PROMOTION_PATH"


def test_itv2_103_release_channel_signature_and_rollback(runtime, test_root: Path):
    svc = ProductizationService(runtime.db, out_dir=test_root / "out")
    os.environ["VAS_RELEASE_SIGNING_KEY"] = "itv2-103-signing-key"

    tamper_profile = "itv2_103_tamper"
    signed = svc.sign_release_manifest(tamper_profile, channel="canary", signer_id="itv2")
    assert signed["ok"]
    signature_path = Path(signed["signature_path"])
    payload = json.loads(signature_path.read_text(encoding="utf-8"))
    payload["signature"]["value"] = "tampered"
    signature_path.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
    tampered = svc.promote_release_channel(
        tamper_profile, "beta", gate_report={"status": "pass", "gate_id": "AT-V2-101", "source_channel": "canary"}
    )
    assert tampered["ok"] is False
    assert tampered["error"] == "E_SIGNATURE_INVALID"

    profile = "itv2_103_rollback"
    assert svc.sign_release_manifest(profile, channel="canary", signer_id="itv2")["ok"]
    assert svc.promote_release_channel(
        profile, "beta", gate_report={"status": "pass", "gate_id": "AT-V2-101", "source_channel": "canary"}
    )["ok"]
    assert svc.promote_release_channel(profile, "stable", gate_report={"status": "pass", "gate_id": "AT-V2-101"})["ok"]

    rollback = svc.rollback_release_channel(profile, "beta", reason="smoke")
    assert rollback["ok"]
    assert rollback["state"]["current_channel"] == "beta"

    invalid_direction = svc.rollback_release_channel(profile, "stable")
    assert invalid_direction["ok"] is False
    assert invalid_direction["error"] == "E_ROLLBACK_DIRECTION_INVALID"
