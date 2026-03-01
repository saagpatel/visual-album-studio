import hashlib

from vas_studio import HardwareProfileV1, ModelRegistryServiceV2, PhotoAnimator


def _register_active_model(
    registry: ModelRegistryServiceV2,
    models_dir,
    *,
    model_id: str,
    relpath: str,
    details: dict,
):
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


def test_itpv2_001_adaptive_model_selection_prefers_compatible_profile(runtime, test_root):
    models_dir = test_root / "out" / "models"
    registry = ModelRegistryServiceV2(runtime.db, models_dir=models_dir)
    animator = PhotoAnimator()

    _register_active_model(
        registry,
        models_dir,
        model_id="depth_lite",
        relpath="depth_lite/model.onnx",
        details={"family": "depth", "min_ram_gb": 6, "min_vram_gb": 0, "min_cpu_cores": 4, "quality_tier": "mid"},
    )
    _register_active_model(
        registry,
        models_dir,
        model_id="depth_pro",
        relpath="depth_pro/model.onnx",
        details={"family": "depth", "min_ram_gb": 16, "min_vram_gb": 6, "min_cpu_cores": 8, "quality_tier": "high"},
    )

    assert registry.record_evaluation(
        model_id="depth_lite",
        fixture_id="fx_low",
        quality_score=0.84,
        perf_fps=48.0,
        safety_score=0.97,
        notes={"lane": "lite"},
    )["ok"]
    assert registry.record_evaluation(
        model_id="depth_pro",
        fixture_id="fx_high",
        quality_score=0.93,
        perf_fps=34.0,
        safety_score=0.98,
        notes={"lane": "pro"},
    )["ok"]

    low_profile = HardwareProfileV1(cpu_cores=4, ram_gb=8, vram_gb=1)
    high_profile = HardwareProfileV1(cpu_cores=12, ram_gb=32, vram_gb=12)

    low_reco = registry.recommend_model_for_hardware(model_family="depth", hardware_profile=low_profile)
    high_reco = registry.recommend_model_for_hardware(model_family="depth", hardware_profile=high_profile)

    assert low_reco["ok"] is True
    assert low_reco["model_id"] == "depth_lite"
    assert low_reco["profile_class"] == "low"
    assert high_reco["ok"] is True
    assert high_reco["model_id"] == "depth_pro"
    assert high_reco["profile_class"] == "high"

    resolved = animator.resolve_auto_model_or_fallback(
        model_family="depth",
        hardware_profile=high_profile,
        registry=registry,
    )
    assert resolved["mode"] == "model"
    assert resolved["model_id"] == "depth_pro"


def test_itpv2_001_adaptive_model_selection_returns_fallback_on_no_compatible(runtime, test_root):
    models_dir = test_root / "out" / "models"
    registry = ModelRegistryServiceV2(runtime.db, models_dir=models_dir)
    animator = PhotoAnimator()

    _register_active_model(
        registry,
        models_dir,
        model_id="depth_heavy_only",
        relpath="depth_heavy_only/model.onnx",
        details={"family": "depth", "min_ram_gb": 32, "min_vram_gb": 10, "min_cpu_cores": 12, "quality_tier": "high"},
    )
    assert registry.record_evaluation(
        model_id="depth_heavy_only",
        fixture_id="fx_heavy",
        quality_score=0.95,
        perf_fps=20.0,
        safety_score=0.99,
        notes={"lane": "heavy"},
    )["ok"]

    constrained_profile = HardwareProfileV1(cpu_cores=4, ram_gb=8, vram_gb=1)
    recommendation = registry.recommend_model_for_hardware(model_family="depth", hardware_profile=constrained_profile)
    assert recommendation["ok"] is False
    assert recommendation["error"] == "E_MODEL_NO_COMPATIBLE"
    assert recommendation["profile_class"] == "low"

    resolved = animator.resolve_auto_model_or_fallback(
        model_family="depth",
        hardware_profile=constrained_profile,
        registry=registry,
    )
    assert resolved["mode"] == "tier0"
    assert resolved["reason"] == "E_MODEL_NO_COMPATIBLE"


def test_itpv2_001_benchmark_telemetry_biases_selection(runtime, test_root):
    models_dir = test_root / "out" / "models"
    registry = ModelRegistryServiceV2(runtime.db, models_dir=models_dir)

    _register_active_model(
        registry,
        models_dir,
        model_id="depth_fast",
        relpath="depth_fast/model.onnx",
        details={"family": "depth", "min_ram_gb": 6, "min_vram_gb": 0, "min_cpu_cores": 4, "quality_tier": "mid"},
    )
    _register_active_model(
        registry,
        models_dir,
        model_id="depth_high_quality",
        relpath="depth_hq/model.onnx",
        details={"family": "depth", "min_ram_gb": 6, "min_vram_gb": 0, "min_cpu_cores": 4, "quality_tier": "high"},
    )

    assert registry.record_evaluation(
        model_id="depth_fast",
        fixture_id="fx_fast",
        quality_score=0.81,
        perf_fps=42.0,
        safety_score=0.97,
    )["ok"]
    assert registry.record_evaluation(
        model_id="depth_high_quality",
        fixture_id="fx_hq",
        quality_score=0.95,
        perf_fps=46.0,
        safety_score=0.98,
    )["ok"]

    # Low-profile telemetry marks depth_high_quality as unreliable on low hardware.
    assert registry.record_hardware_benchmark(
        model_id="depth_fast",
        profile_class="low",
        avg_fps=44.0,
        p95_latency_ms=38.0,
        memory_mb=780.0,
        success_rate=0.99,
    )["ok"]
    assert registry.record_hardware_benchmark(
        model_id="depth_high_quality",
        profile_class="low",
        avg_fps=35.0,
        p95_latency_ms=82.0,
        memory_mb=1800.0,
        success_rate=0.72,
    )["ok"]

    low_profile = HardwareProfileV1(cpu_cores=4, ram_gb=8, vram_gb=1)
    recommendation = registry.recommend_model_for_hardware(model_family="depth", hardware_profile=low_profile)

    assert recommendation["ok"] is True
    assert recommendation["model_id"] == "depth_fast"
    assert recommendation["candidates"][0]["success_rate"] >= 0.9


def test_itpv2_001_selection_events_recorded(runtime, test_root):
    models_dir = test_root / "out" / "models"
    registry = ModelRegistryServiceV2(runtime.db, models_dir=models_dir)
    animator = PhotoAnimator()

    _register_active_model(
        registry,
        models_dir,
        model_id="depth_event",
        relpath="depth_event/model.onnx",
        details={"family": "depth", "min_ram_gb": 6, "min_vram_gb": 0, "min_cpu_cores": 4, "quality_tier": "mid"},
    )
    assert registry.record_evaluation(
        model_id="depth_event",
        fixture_id="fx_event",
        quality_score=0.82,
        perf_fps=41.0,
        safety_score=0.96,
    )["ok"]

    selected_profile = HardwareProfileV1(cpu_cores=8, ram_gb=16, vram_gb=4)
    selected = animator.resolve_auto_model_or_fallback(
        model_family="depth",
        hardware_profile=selected_profile,
        registry=registry,
    )
    assert selected["mode"] == "model"

    fallback_profile = HardwareProfileV1(cpu_cores=2, ram_gb=4, vram_gb=0)
    fallback = animator.resolve_auto_model_or_fallback(
        model_family="depth",
        hardware_profile=fallback_profile,
        registry=registry,
    )
    assert fallback["mode"] == "tier0"

    rows = runtime.db.execute(
        """
        SELECT outcome, reason
        FROM model_selection_events
        ORDER BY created_at ASC
        """
    ).fetchall()
    outcomes = [str(row["outcome"]) for row in rows]
    assert "selected" in outcomes
    assert "fallback" in outcomes


def test_itpv2_001_missing_model_file_forces_fallback_event(runtime, test_root):
    models_dir = test_root / "out" / "models"
    registry = ModelRegistryServiceV2(runtime.db, models_dir=models_dir)
    animator = PhotoAnimator()

    relpath = "depth_missing/model.onnx"
    _register_active_model(
        registry,
        models_dir,
        model_id="depth_missing",
        relpath=relpath,
        details={"family": "depth", "min_ram_gb": 6, "min_vram_gb": 0, "min_cpu_cores": 4, "quality_tier": "mid"},
    )
    assert registry.record_evaluation(
        model_id="depth_missing",
        fixture_id="fx_missing",
        quality_score=0.88,
        perf_fps=48.0,
        safety_score=0.98,
    )["ok"]

    # Simulate drift between registry state and filesystem artifact state.
    (models_dir / relpath).unlink()

    profile = HardwareProfileV1(cpu_cores=8, ram_gb=16, vram_gb=4)
    recommendation = registry.recommend_model_for_hardware(model_family="depth", hardware_profile=profile)
    assert recommendation["ok"] is False
    assert recommendation["error"] == "E_MODEL_NO_COMPATIBLE"
    assert recommendation["candidates"]
    assert recommendation["candidates"][0]["installed"] is False

    resolved = animator.resolve_auto_model_or_fallback(
        model_family="depth",
        hardware_profile=profile,
        registry=registry,
    )
    assert resolved["mode"] == "tier0"
    assert resolved["reason"] == "E_MODEL_NO_COMPATIBLE"

    latest = runtime.db.execute(
        """
        SELECT outcome, reason
        FROM model_selection_events
        ORDER BY created_at DESC
        LIMIT 1
        """
    ).fetchone()
    assert latest is not None
    assert str(latest["outcome"]) == "fallback"
    assert str(latest["reason"]) == "E_MODEL_NO_COMPATIBLE"
