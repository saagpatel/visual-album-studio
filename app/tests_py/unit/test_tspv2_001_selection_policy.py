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


def test_tspv2_001_selection_policy_is_deterministic_for_ties(runtime, test_root):
    models_dir = test_root / "out" / "models"
    registry = ModelRegistryServiceV2(runtime.db, models_dir=models_dir)

    common = {"family": "depth", "min_ram_gb": 6, "min_vram_gb": 0, "min_cpu_cores": 4, "quality_tier": "mid"}
    _register_active_model(registry, models_dir, model_id="depth_a", relpath="depth_a/model.onnx", details=common)
    _register_active_model(registry, models_dir, model_id="depth_b", relpath="depth_b/model.onnx", details=common)

    for model_id in ["depth_a", "depth_b"]:
        assert registry.record_evaluation(
            model_id=model_id,
            fixture_id="fx_tie",
            quality_score=0.9,
            perf_fps=40.0,
            safety_score=0.98,
            hardware_profile=HardwareProfileV1(cpu_cores=8, ram_gb=16, vram_gb=4),
            p95_latency_ms=32.0,
            memory_mb=700.0,
            success_rate=0.99,
        )["ok"]

    profile = HardwareProfileV1(cpu_cores=8, ram_gb=16, vram_gb=4)
    picks = []
    for _ in range(5):
        recommendation = registry.recommend_model_for_hardware(model_family="depth", hardware_profile=profile)
        assert recommendation["ok"] is True
        picks.append(recommendation["model_id"])

    assert len(set(picks)) == 1
    assert picks[0] == "depth_b"


def test_tspv2_001_record_evaluation_auto_ingests_benchmark(runtime, test_root):
    models_dir = test_root / "out" / "models"
    registry = ModelRegistryServiceV2(runtime.db, models_dir=models_dir)

    _register_active_model(
        registry,
        models_dir,
        model_id="depth_ingest",
        relpath="depth_ingest/model.onnx",
        details={"family": "depth", "min_ram_gb": 6, "min_vram_gb": 0, "min_cpu_cores": 4, "quality_tier": "mid"},
    )

    result = registry.record_evaluation(
        model_id="depth_ingest",
        fixture_id="fx_ingest",
        quality_score=0.85,
        perf_fps=36.0,
        safety_score=0.97,
        hardware_profile=HardwareProfileV1(cpu_cores=4, ram_gb=8, vram_gb=1),
        success_rate=1.2,
    )
    assert result["ok"] is True
    assert "benchmark_id" in result

    row = runtime.db.execute(
        "SELECT profile_class, success_rate, p95_latency_ms FROM model_hw_benchmarks WHERE model_id = ? ORDER BY created_at DESC LIMIT 1",
        ("depth_ingest",),
    ).fetchone()
    assert row is not None
    assert str(row["profile_class"]) == "low"
    assert float(row["success_rate"]) == 1.0
    assert float(row["p95_latency_ms"]) > 0.0
