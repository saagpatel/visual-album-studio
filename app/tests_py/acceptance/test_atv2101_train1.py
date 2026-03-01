import hashlib
import hmac
import json
import os
from pathlib import Path

from conftest import generate_wav
from vas_studio import ProductizationService


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def test_atv2101_train1_4k_and_signing(runtime, test_root):
    audio = test_root / "fixtures" / "tone_train1.wav"
    generate_wav(audio, duration_sec=6.0)
    asset_id = runtime.assets.import_asset(audio)
    runtime.assets.set_license(asset_id, source_type="original", license_name="Owned")

    # 4K deterministic lane (short real export at 3840x2160)
    project_4k = runtime.create_project(name="ATV2101-4K", duration_sec=4, width=3840, height=2160)
    export_a = runtime.export_project(project_id=project_4k, audio_asset_id=asset_id, draft=False)
    export_b = runtime.export_project(project_id=project_4k, audio_asset_id=asset_id, draft=False)

    bundle_a = Path(export_a["bundle_dir"])
    bundle_b = Path(export_b["bundle_dir"])
    manifest_a = json.loads((bundle_a / "build_manifest.json").read_text(encoding="utf-8"))
    manifest_b = json.loads((bundle_b / "build_manifest.json").read_text(encoding="utf-8"))

    assert manifest_a["snapshot"]["width"] == 3840
    assert manifest_a["snapshot"]["height"] == 2160
    assert manifest_a["snapshot"]["checkpoints"] == manifest_b["snapshot"]["checkpoints"]

    # 4K long-run resume semantics (simulate 2h plan)
    project_2h_4k = runtime.create_project(name="ATV2101-2H-4K", duration_sec=7200, width=3840, height=2160)
    sim_a = runtime.export_project(project_id=project_2h_4k, audio_asset_id=asset_id, draft=False, simulate_only=True)
    sim_b = runtime.export_project(project_id=project_2h_4k, audio_asset_id=asset_id, draft=False, simulate_only=True)

    assert len(sim_a["segments"]) >= 100
    assert sim_a["segments"] == sim_b["segments"]

    # Packaging/signing verification lane
    os.environ["VAS_RELEASE_SIGNING_KEY"] = "train1-test-signing-key"
    productization = ProductizationService(runtime.db, out_dir=test_root / "out")
    package = productization.run_packaging_dry_run("atv2101_profile", channel="beta")
    assert package["ok"]

    signed = productization.sign_release_manifest("atv2101_profile", channel="beta", signer_id="atv2101-ci")
    assert signed["ok"]
    verify = productization.verify_release_manifest_signature("atv2101_profile")
    assert verify["ok"]
    assert verify["valid"] is True

    # Validate signature value against expected HMAC for determinism
    manifest_path = Path(package["package"]["manifest_path"])
    manifest_content = manifest_path.read_text(encoding="utf-8")
    expected = hmac.new(
        b"train1-test-signing-key", manifest_content.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    signature_path = manifest_path.with_name("manifest.sig.json")
    sig_payload = json.loads(signature_path.read_text(encoding="utf-8"))
    assert sig_payload["signature"]["value"] == expected

    # Signed payload should be deterministic for unchanged manifest content
    signed_again = productization.sign_release_manifest("atv2101_profile", channel="beta", signer_id="atv2101-ci")
    assert signed_again["ok"]
    sig_payload_again = json.loads(signature_path.read_text(encoding="utf-8"))
    assert sig_payload_again["signature"]["value"] == sig_payload["signature"]["value"]

    # Guardrail: artifact hash in signature payload matches manifest file
    assert sig_payload["manifest_sha256"] == _sha256(manifest_path)
