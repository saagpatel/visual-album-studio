import hashlib

from vas_studio import HardwareProfileV1, ModelRegistryServiceV2


def _register_active_model(registry: ModelRegistryServiceV2, models_dir, *, model_id: str, relpath: str, details: dict):
    model_path = models_dir / relpath
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_bytes(model_id.encode("utf-8"))
    digest = hashlib.sha256(model_path.read_bytes()).hexdigest()
    assert registry.register_candidate(
        model_id=model_id,
        name=model_id,
        version="2.0.0",
        license_name="Apache-2.0",
        license_spdx="Apache-2.0",
        source_url=f"https://example.com/{model_id}",
        sha256=digest,
        relpath=relpath,
        size_bytes=model_path.stat().st_size,
        details=details,
    )["ok"]
    assert registry.promote_model(model_id)["ok"]


def test_itpv2_001_eval_ingestion_creates_profile_benchmark(runtime, test_root):
    models_dir = test_root / "out" / "models"
    registry = ModelRegistryServiceV2(runtime.db, models_dir=models_dir)

    _register_active_model(
        registry,
        models_dir,
        model_id="depth_eval_ingest",
        relpath="depth_eval_ingest/model.onnx",
        details={"family": "depth", "min_ram_gb": 6, "min_vram_gb": 0, "min_cpu_cores": 4, "quality_tier": "mid"},
    )

    result = registry.record_evaluation(
        model_id="depth_eval_ingest",
        fixture_id="fx_eval",
        quality_score=0.87,
        perf_fps=38.0,
        safety_score=0.98,
        hardware_profile=HardwareProfileV1(cpu_cores=8, ram_gb=16, vram_gb=4),
        p95_latency_ms=30.0,
        memory_mb=650.0,
        success_rate=0.97,
    )
    assert result["ok"] is True
    assert result.get("benchmark_id")

    row = runtime.db.execute(
        "SELECT profile_class, avg_fps, success_rate FROM model_hw_benchmarks WHERE id = ?",
        (result["benchmark_id"],),
    ).fetchone()
    assert row is not None
    assert str(row["profile_class"]) == "mid"
    assert float(row["avg_fps"]) == 38.0
    assert float(row["success_rate"]) == 0.97


def test_itpv2_001_drift_guard_blocks_checksum_mismatch(runtime, test_root):
    models_dir = test_root / "out" / "models"
    registry = ModelRegistryServiceV2(runtime.db, models_dir=models_dir)

    relpath = "depth_drift/model.onnx"
    _register_active_model(
        registry,
        models_dir,
        model_id="depth_drift",
        relpath=relpath,
        details={"family": "depth", "min_ram_gb": 6, "min_vram_gb": 0, "min_cpu_cores": 4, "quality_tier": "mid"},
    )

    assert registry.record_evaluation(
        model_id="depth_drift",
        fixture_id="fx_drift",
        quality_score=0.9,
        perf_fps=41.0,
        safety_score=0.98,
        hardware_profile=HardwareProfileV1(cpu_cores=8, ram_gb=16, vram_gb=4),
    )["ok"]

    model_path = models_dir / relpath
    model_path.write_bytes(b"tampered")

    drift = registry.detect_model_artifact_drift(model_id="depth_drift")
    assert drift["ok"] is True
    assert drift["count"] == 1
    assert drift["incidents"][0]["issue_code"] == "E_MODEL_CHECKSUM_MISMATCH"

    recommendation = registry.recommend_model_for_hardware(
        model_family="depth",
        hardware_profile=HardwareProfileV1(cpu_cores=8, ram_gb=16, vram_gb=4),
    )
    assert recommendation["ok"] is False
    assert recommendation["error"] == "E_MODEL_NO_COMPATIBLE"
    assert recommendation["incidents"]
    assert recommendation["incidents"][0]["issue_code"] == "E_MODEL_CHECKSUM_MISMATCH"
