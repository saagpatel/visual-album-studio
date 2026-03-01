from vas_studio import MappingContext, MappingService, NEXT_GEN_PRESETS


def test_tsv2_201_mode_contracts_allow_v2_namespaces():
    svc = MappingService()
    mapping = """
    ng.wave.amplitude = clamp(0.5 + sin(time_sec) * 0.1, 0, 1)
    ml.depth.strength = clamp(0.3 + beat_phase * 0.4, 0, 1)
    """.strip()
    assert svc.validate_mapping(mapping) is True
    out = svc.evaluate(mapping, MappingContext(time_sec=1.0, beat_phase=0.5, tempo_bpm=120.0, seed=7))
    assert list(out.keys()) == sorted(out.keys())
    assert "ng.wave.amplitude" in out
    assert "ml.depth.strength" in out


def test_tsv2_201_mode_contracts_reject_invalid_namespace():
    svc = MappingService()
    mapping = "zz.unknown.value = 1.0"
    try:
        svc.validate_mapping(mapping)
        raise AssertionError("Expected invalid namespace to raise")
    except Exception as exc:
        assert "E_PARAM_UNKNOWN" in str(exc)


def test_tsv2_201_mode_contracts_have_next_gen_presets():
    assert len(NEXT_GEN_PRESETS) >= 2
    preset = NEXT_GEN_PRESETS[0]
    assert preset.mode_id in {"nebula_waves", "pulse_mesh"}
    assert any(key.startswith("ng.") for key in preset.params.keys())
