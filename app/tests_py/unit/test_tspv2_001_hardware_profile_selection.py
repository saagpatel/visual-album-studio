from vas_studio import HardwareProfileV1, ModelRegistryServiceV2, PhotoAnimator


def test_tspv2_001_hardware_profile_classification():
    low = HardwareProfileV1(cpu_cores=4, ram_gb=8, vram_gb=1)
    mid = HardwareProfileV1(cpu_cores=8, ram_gb=16, vram_gb=4)
    high = HardwareProfileV1(cpu_cores=12, ram_gb=32, vram_gb=8)

    assert ModelRegistryServiceV2.classify_hardware_profile(low) == "low"
    assert ModelRegistryServiceV2.classify_hardware_profile(mid) == "mid"
    assert ModelRegistryServiceV2.classify_hardware_profile(high) == "high"


def test_tspv2_001_auto_model_fallback_without_registry():
    animator = PhotoAnimator()
    result = animator.resolve_auto_model_or_fallback(
        model_family="depth",
        hardware_profile=HardwareProfileV1(cpu_cores=4, ram_gb=8, vram_gb=1),
        registry=None,
    )
    assert result["mode"] == "tier0"
    assert result["reason"] == "E_MODEL_NOT_INSTALLED"
    assert result["model_id"] is None
