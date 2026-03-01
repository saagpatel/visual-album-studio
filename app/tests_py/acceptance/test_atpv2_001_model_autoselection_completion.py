import hashlib

from vas_studio import HardwareProfileV1, ModelRegistryServiceV2, PhotoAnimator


def _register_active_model(registry: ModelRegistryServiceV2, models_dir, *, model_id: str, relpath: str, details: dict):
    model_path = models_dir / relpath
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_bytes(model_id.encode("utf-8"))
    digest = hashlib.sha256(model_path.read_bytes()).hexdigest()
    assert registry.register_candidate(
        model_id=model_id,
        name=model_id,
        version="2.1.0",
        license_name="Apache-2.0",
        license_spdx="Apache-2.0",
        source_url=f"https://example.com/{model_id}",
        sha256=digest,
        relpath=relpath,
        size_bytes=model_path.stat().st_size,
        details=details,
    )["ok"]
    assert registry.promote_model(model_id)["ok"]


def test_atpv2_001_model_autoselection_completion(runtime, test_root):
    models_dir = test_root / "out" / "models"
    registry = ModelRegistryServiceV2(runtime.db, models_dir=models_dir)
    animator = PhotoAnimator()

    _register_active_model(
        registry,
        models_dir,
        model_id="depth_low",
        relpath="depth_low/model.onnx",
        details={"family": "depth", "min_ram_gb": 4, "min_vram_gb": 0, "min_cpu_cores": 2, "quality_tier": "mid"},
    )
    _register_active_model(
        registry,
        models_dir,
        model_id="depth_mid",
        relpath="depth_mid/model.onnx",
        details={"family": "depth", "min_ram_gb": 12, "min_vram_gb": 2, "min_cpu_cores": 6, "quality_tier": "mid"},
    )
    _register_active_model(
        registry,
        models_dir,
        model_id="depth_high",
        relpath="depth_high/model.onnx",
        details={"family": "depth", "min_ram_gb": 24, "min_vram_gb": 6, "min_cpu_cores": 8, "quality_tier": "high"},
    )

    assert registry.record_evaluation(
        model_id="depth_low",
        fixture_id="fx_low",
        quality_score=0.82,
        perf_fps=52.0,
        safety_score=0.97,
        hardware_profile=HardwareProfileV1(cpu_cores=4, ram_gb=8, vram_gb=1),
        p95_latency_ms=28.0,
        memory_mb=500.0,
        success_rate=0.99,
    )["ok"]
    assert registry.record_evaluation(
        model_id="depth_mid",
        fixture_id="fx_mid",
        quality_score=0.9,
        perf_fps=44.0,
        safety_score=0.98,
        hardware_profile=HardwareProfileV1(cpu_cores=8, ram_gb=16, vram_gb=4),
        p95_latency_ms=32.0,
        memory_mb=900.0,
        success_rate=0.98,
    )["ok"]
    assert registry.record_evaluation(
        model_id="depth_high",
        fixture_id="fx_high",
        quality_score=0.95,
        perf_fps=36.0,
        safety_score=0.99,
        hardware_profile=HardwareProfileV1(cpu_cores=12, ram_gb=32, vram_gb=8),
        p95_latency_ms=34.0,
        memory_mb=1400.0,
        success_rate=0.98,
    )["ok"]

    low = animator.resolve_auto_model_or_fallback(
        model_family="depth",
        hardware_profile=HardwareProfileV1(cpu_cores=4, ram_gb=8, vram_gb=1),
        registry=registry,
    )
    mid = animator.resolve_auto_model_or_fallback(
        model_family="depth",
        hardware_profile=HardwareProfileV1(cpu_cores=8, ram_gb=16, vram_gb=4),
        registry=registry,
    )
    high = animator.resolve_auto_model_or_fallback(
        model_family="depth",
        hardware_profile=HardwareProfileV1(cpu_cores=12, ram_gb=32, vram_gb=8),
        registry=registry,
    )

    assert low["mode"] == "model"
    assert low["model_id"] == "depth_low"
    assert mid["mode"] == "model"
    assert mid["model_id"] == "depth_mid"
    assert high["mode"] == "model"
    assert high["model_id"] == "depth_high"

    # Drift path: checksum mismatch should make the candidate unusable and force fallback.
    single_relpath = "matte_single/model.onnx"
    _register_active_model(
        registry,
        models_dir,
        model_id="matte_single",
        relpath=single_relpath,
        details={"family": "matte", "min_ram_gb": 6, "min_vram_gb": 0, "min_cpu_cores": 4, "quality_tier": "mid"},
    )
    assert registry.record_evaluation(
        model_id="matte_single",
        fixture_id="fx_matte",
        quality_score=0.84,
        perf_fps=40.0,
        safety_score=0.97,
        hardware_profile=HardwareProfileV1(cpu_cores=8, ram_gb=16, vram_gb=4),
    )["ok"]

    (models_dir / single_relpath).write_bytes(b"tampered")
    fallback = animator.resolve_auto_model_or_fallback(
        model_family="matte",
        hardware_profile=HardwareProfileV1(cpu_cores=8, ram_gb=16, vram_gb=4),
        registry=registry,
    )
    assert fallback["mode"] == "tier0"
    assert fallback["reason"] == "E_MODEL_NO_COMPATIBLE"

    drift = registry.detect_model_artifact_drift(model_id="matte_single")
    assert drift["count"] == 1
    assert drift["incidents"][0]["issue_code"] == "E_MODEL_CHECKSUM_MISMATCH"
