from vas_studio import RemixEngine


def test_ts007_variant_distance_guardrails():
    remix = RemixEngine()
    variants = remix.generate_variants(base_seed=100, count=3)
    ok, score = remix.validate_variant(variants[0], variants[1], min_changed=5, threshold=0.5)
    assert ok
    assert score > 0
