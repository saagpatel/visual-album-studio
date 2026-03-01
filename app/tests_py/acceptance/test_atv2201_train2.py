import hashlib
import json
from pathlib import Path

from conftest import generate_wav
from vas_studio import MappingContext, MappingService, ModelRegistryServiceV2, PhotoAnimator


def test_atv2201_train2_mode_contracts_model_provenance_and_fallback(runtime, test_root):
    audio = test_root / "fixtures" / "tone_train2.wav"
    generate_wav(audio, duration_sec=6.0)
    audio_asset_id = runtime.assets.import_asset(audio)
    runtime.assets.set_license(audio_asset_id, source_type="original", license_name="Owned")

    project_id = runtime.create_project(name="ATV2201-PreviewExportParity", duration_sec=5, width=1920, height=1080)
    export_a = runtime.export_project(project_id=project_id, audio_asset_id=audio_asset_id, draft=False)
    export_b = runtime.export_project(project_id=project_id, audio_asset_id=audio_asset_id, draft=False)

    manifest_a = json.loads((Path(export_a["bundle_dir"]) / "build_manifest.json").read_text(encoding="utf-8"))
    manifest_b = json.loads((Path(export_b["bundle_dir"]) / "build_manifest.json").read_text(encoding="utf-8"))
    assert manifest_a["snapshot"]["checkpoints"] == manifest_b["snapshot"]["checkpoints"]

    mapping = """
    ng.wave.amplitude = clamp(0.5 + sin(time_sec) * 0.2, 0, 1)
    ml.depth.strength = clamp(0.2 + beat_phase * 0.7, 0, 1)
    """.strip()
    mapper = MappingService()
    ctx = MappingContext(time_sec=1.25, beat_phase=0.4, tempo_bpm=120.0, seed=9)
    eval_a = mapper.evaluate(mapping, ctx)
    eval_b = mapper.evaluate(mapping, ctx)
    assert eval_a == eval_b

    models_dir = test_root / "out" / "models"
    model_path = models_dir / "depth_v2/depth.onnx"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_bytes(b"depth-v2-train2")
    digest = hashlib.sha256(model_path.read_bytes()).hexdigest()

    registry = ModelRegistryServiceV2(runtime.db, models_dir=models_dir)
    create = registry.register_candidate(
        model_id="depth_v2",
        name="Depth V2",
        version="2.0.0",
        license_name="Apache-2.0",
        license_spdx="Apache-2.0",
        source_url="https://example.com/depth_v2",
        sha256=digest,
        relpath="depth_v2/depth.onnx",
        size_bytes=model_path.stat().st_size,
        details={"family": "depth"},
    )
    assert create["ok"] is True
    assert registry.promote_model("depth_v2")["ok"] is True

    animator = PhotoAnimator()
    resolved = animator.resolve_model_or_fallback(model_id="depth_v2", registry=registry)
    assert resolved["mode"] == "model"

    missing = animator.resolve_model_or_fallback(model_id="missing_model", registry=registry)
    assert missing["mode"] == "tier0"
    assert missing["reason"] == "E_MODEL_NOT_INSTALLED"
