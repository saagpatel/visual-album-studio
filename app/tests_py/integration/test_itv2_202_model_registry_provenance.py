import hashlib
import json

from vas_studio import ModelRegistryServiceV2


def test_itv2_202_model_registry_register_promote_and_eval(runtime, test_root):
    models_dir = test_root / "out" / "models"
    registry = ModelRegistryServiceV2(runtime.db, models_dir=models_dir)

    model_relpath = "depth_v2/depth.onnx"
    model_path = models_dir / model_relpath
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_bytes(b"depth-model-v2")
    digest = hashlib.sha256(model_path.read_bytes()).hexdigest()

    verify = registry.verify_checksum(model_path, digest)
    assert verify["ok"] is True

    created = registry.register_candidate(
        model_id="depth_v2",
        name="Depth v2",
        version="2.0.0",
        license_name="Apache-2.0",
        license_spdx="Apache-2.0",
        source_url="https://example.com/depth_v2",
        sha256=digest,
        relpath=model_relpath,
        size_bytes=model_path.stat().st_size,
        details={"family": "depth"},
    )
    assert created["ok"] is True

    promoted = registry.promote_model("depth_v2")
    assert promoted["ok"] is True
    model = registry.get_model("depth_v2")
    assert model is not None
    assert model["status"] == "active"
    provenance = json.loads(model["provenance_json"])
    assert provenance["schema_version"] == 1
    assert provenance["sha256"] == digest

    eval_record = registry.record_evaluation(
        model_id="depth_v2",
        fixture_id="fixture_depth_v2_smoke",
        quality_score=0.91,
        perf_fps=43.2,
        safety_score=0.99,
        notes={"determinism": "pass"},
    )
    assert eval_record["ok"] is True


def test_itv2_202_model_registry_blocks_unknown_license(runtime, test_root):
    registry = ModelRegistryServiceV2(runtime.db, models_dir=test_root / "out" / "models")
    try:
        registry.enforce_license_policy(license_name="Unknown", license_spdx="unknown")
        raise AssertionError("Expected policy error")
    except Exception as exc:
        assert "E_MODEL_LICENSE_UNKNOWN" in str(exc)
