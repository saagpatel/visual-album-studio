from vas_studio import MappingContext, MappingService


def test_ts002_mapping_deterministic_eval():
    svc = MappingService()
    dsl = "mp.beat.pulse_amount = clamp(0.2 + beat_phase * 0.5, 0, 1)"
    ctx = MappingContext(time_sec=1.5, beat_phase=0.4, tempo_bpm=120.0, seed=101)

    out_a = svc.evaluate(dsl, ctx)
    out_b = svc.evaluate(dsl, ctx)

    assert out_a == out_b
    assert "mp.beat.pulse_amount" in out_a
