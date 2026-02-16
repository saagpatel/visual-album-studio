import json
from pathlib import Path

from conftest import generate_wav


def test_at001_phase1_end_to_end(runtime, test_root):
    audio = test_root / "fixtures" / "tone.wav"
    generate_wav(audio, duration_sec=10.0)
    asset_id = runtime.assets.import_asset(audio)
    runtime.assets.set_license(asset_id, source_type="original", license_name="Owned")

    project_10s = runtime.create_project(name="AT001-10s", duration_sec=10)
    export_10s = runtime.export_project(project_id=project_10s, audio_asset_id=asset_id, draft=False)

    bundle_dir = Path(export_10s["bundle_dir"])
    for name in ["video.mp4", "thumbnail.png", "metadata.json", "provenance.json", "build_manifest.json"]:
        assert (bundle_dir / name).exists()

    project_10m = runtime.create_project(name="AT001-10m", duration_sec=600)
    export_10m = runtime.export_project(project_id=project_10m, audio_asset_id=asset_id, draft=False, simulate_only=True)
    assert len(export_10m["segments"]) >= 10

    project_2h = runtime.create_project(name="AT001-2h", duration_sec=7200)
    export_2h = runtime.export_project(project_id=project_2h, audio_asset_id=asset_id, draft=False, simulate_only=True)
    assert len(export_2h["segments"]) >= 100

    manifest = json.loads((bundle_dir / "build_manifest.json").read_text(encoding="utf-8"))
    checkpoints_a = manifest["snapshot"]["checkpoints"]

    export_10s_b = runtime.export_project(project_id=project_10s, audio_asset_id=asset_id, draft=False)
    bundle_dir_b = Path(export_10s_b["bundle_dir"])
    manifest_b = json.loads((bundle_dir_b / "build_manifest.json").read_text(encoding="utf-8"))

    assert checkpoints_a == manifest_b["snapshot"]["checkpoints"]
