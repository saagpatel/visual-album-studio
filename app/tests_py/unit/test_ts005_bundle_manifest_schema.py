import json
from pathlib import Path

from conftest import generate_wav


def test_ts005_bundle_and_manifest_shape(runtime, test_root):
    audio = test_root / "fixtures" / "tone.wav"
    generate_wav(audio, duration_sec=2.0)
    asset_id = runtime.assets.import_asset(audio)
    runtime.assets.set_license(asset_id, source_type="original", license_name="Owned")

    project_id = runtime.create_project(name="TS005", duration_sec=2)
    result = runtime.export_project(project_id=project_id, audio_asset_id=asset_id, draft=False)

    bundle = Path(result["bundle_dir"])
    assert bundle.exists()

    manifest = json.loads((bundle / "build_manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert "toolchain" in manifest
    assert "snapshot" in manifest
    assert "segment_plan" in manifest["snapshot"]
