from vas_studio import RemixEngine


def test_ts007_variant_distance_guardrails():
    remix = RemixEngine()
    variants = remix.generate_variants(base_seed=100, count=3, rule_spec={"duration_cycle_sec": [10, 30]})
    result = remix.validate_variant(variants[0], variants[1], min_changed=5, threshold=0.8)
    assert result["ok"] is True
    assert result["score"] > 0
    assert result["changed_count"] >= 5
    assert result["has_structural_change"] is True
    assert result["rejection_code"] == ""
