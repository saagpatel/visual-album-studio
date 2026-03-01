from vas_studio import ModelRegistryServiceV2


def test_tsv2_203_model_eval_harness_weighted_score_bounds():
    score = ModelRegistryServiceV2.score_candidate(quality_score=0.92, perf_fps=48.0, safety_score=0.98)
    assert 0.0 <= score <= 1.0
    assert score > 0.8


def test_tsv2_203_model_eval_harness_safety_dominates():
    high_quality_low_safety = ModelRegistryServiceV2.score_candidate(quality_score=0.99, perf_fps=120.0, safety_score=0.2)
    moderate_quality_high_safety = ModelRegistryServiceV2.score_candidate(quality_score=0.75, perf_fps=30.0, safety_score=0.95)
    assert moderate_quality_high_safety > high_quality_low_safety
