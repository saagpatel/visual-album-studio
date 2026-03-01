import hashlib

from vas_studio import ModelRegistryServiceV2, PhotoAnimator


def test_itv2_203_model_fallback_when_missing(runtime, test_root):
    animator = PhotoAnimator()
    registry = ModelRegistryServiceV2(runtime.db, models_dir=test_root / "out" / "models")

    resolved = animator.resolve_model_or_fallback(model_id="missing_depth_model", registry=registry)
    assert resolved["mode"] == "tier0"
    assert resolved["reason"] == "E_MODEL_NOT_INSTALLED"


def test_itv2_203_model_fallback_when_blocked(runtime, test_root):
    models_dir = test_root / "out" / "models"
    registry = ModelRegistryServiceV2(runtime.db, models_dir=models_dir)
    animator = PhotoAnimator()

    relpath = "depth_blocked/model.onnx"
    model_path = models_dir / relpath
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_bytes(b"blocked-model")
    digest = hashlib.sha256(model_path.read_bytes()).hexdigest()

    assert registry.register_candidate(
        model_id="depth_blocked",
        name="Depth Blocked",
        version="2.0.0",
        license_name="Apache-2.0",
        license_spdx="Apache-2.0",
        source_url="https://example.com/depth_blocked",
        sha256=digest,
        relpath=relpath,
        size_bytes=model_path.stat().st_size,
    )["ok"]

    runtime.db.execute("UPDATE model_registry SET status = 'blocked' WHERE id = ?", ("depth_blocked",))
    runtime.db.commit()
    blocked = animator.resolve_model_or_fallback(model_id="depth_blocked", registry=registry)
    assert blocked["mode"] == "tier0"
    assert blocked["reason"] == "E_MODEL_UNAVAILABLE"


def test_itv2_203_model_uses_active_model(runtime, test_root):
    models_dir = test_root / "out" / "models"
    registry = ModelRegistryServiceV2(runtime.db, models_dir=models_dir)
    animator = PhotoAnimator()

    relpath = "depth_active/model.onnx"
    model_path = models_dir / relpath
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_bytes(b"active-model")
    digest = hashlib.sha256(model_path.read_bytes()).hexdigest()

    assert registry.register_candidate(
        model_id="depth_active",
        name="Depth Active",
        version="2.0.0",
        license_name="Apache-2.0",
        license_spdx="Apache-2.0",
        source_url="https://example.com/depth_active",
        sha256=digest,
        relpath=relpath,
        size_bytes=model_path.stat().st_size,
    )["ok"]
    assert registry.promote_model("depth_active")["ok"]

    active = animator.resolve_model_or_fallback(model_id="depth_active", registry=registry)
    assert active["mode"] == "model"
    assert active["model_path"].endswith(relpath)
