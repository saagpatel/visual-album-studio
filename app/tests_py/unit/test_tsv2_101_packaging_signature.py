import json
import os
from pathlib import Path

from vas_studio import ProductizationService


def test_tsv2_101_packaging_signature_sign_and_verify(runtime, test_root: Path):
    svc = ProductizationService(runtime.db, out_dir=test_root / "out")

    os.environ["VAS_RELEASE_SIGNING_KEY"] = "tsv2-signing-key"
    signed = svc.sign_release_manifest("profile_tsv2_101", channel="beta", signer_id="tsv2")
    assert signed["ok"]

    signature_path = Path(signed["signature_path"])
    assert signature_path.exists()

    verify = svc.verify_release_manifest_signature("profile_tsv2_101", channel="beta")
    assert verify["ok"]
    assert verify["valid"] is True

    payload = json.loads(signature_path.read_text(encoding="utf-8"))
    assert payload["signature"]["algorithm"] == "HMAC-SHA256"
    assert payload["channel"] == "beta"
    assert payload["schema_version"] == 2
    assert payload["gate_requirements"]["required_gate"] == "AT-V2-101"


def test_tsv2_101_packaging_signature_missing_key(runtime, test_root: Path):
    svc = ProductizationService(runtime.db, out_dir=test_root / "out")

    if "VAS_RELEASE_SIGNING_KEY" in os.environ:
        del os.environ["VAS_RELEASE_SIGNING_KEY"]

    signed = svc.sign_release_manifest("profile_tsv2_101_no_key")
    assert signed["ok"] is False
    assert signed["error"] == "E_SIGNING_KEY_MISSING"


def test_tsv2_101_packaging_signature_tamper_detected(runtime, test_root: Path):
    svc = ProductizationService(runtime.db, out_dir=test_root / "out")

    os.environ["VAS_RELEASE_SIGNING_KEY"] = "tsv2-signing-key"
    signed = svc.sign_release_manifest("profile_tsv2_101_tamper")
    assert signed["ok"]

    signature_path = Path(signed["signature_path"])
    payload = json.loads(signature_path.read_text(encoding="utf-8"))
    payload["signature"]["value"] = "bad-signature"
    signature_path.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")

    verify = svc.verify_release_manifest_signature("profile_tsv2_101_tamper")
    assert verify["ok"]
    assert verify["valid"] is False
