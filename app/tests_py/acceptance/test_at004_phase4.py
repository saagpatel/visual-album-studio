from vas_studio import BatchPlanner, RemixEngine


def test_at004_batch_and_guardrails():
    remix = RemixEngine()
    planner = BatchPlanner()
    variants = remix.generate_variants(
        base_seed=1000,
        count=100,
        rule_spec={"duration_cycle_sec": [10, 30, 600, 7200], "audio_swap_ids": ["", "mix_alt"]},
    )
    assert len(variants) == 100

    base = variants[0]
    valid_count = 0
    for v in variants[1:]:
        result = remix.validate_variant(base, v, min_changed=5, threshold=0.8)
        if result["ok"]:
            valid_count += 1
        else:
            assert result["rejection_code"] != ""

    assert valid_count >= 50

    plan = planner.create_plan(
        variants,
        max_concurrent=4,
        options={"window_start": "22:00", "window_end": "06:00", "retry_limit": 2, "disk_free_bytes": 20 * 1024 * 1024 * 1024},
    )
    assert len(plan["items"]) == 100
    assert plan["status"] == "planned"
    assert plan["window_start"] == "22:00"
    assert plan["window_end"] == "06:00"
    assert "backoff_policy" in plan
    assert "circuit_breaker" in plan

    report = planner.reviewer_report(variants, remix, near_duplicate_threshold=0.8)
    assert report["summary"]["count"] == 100
    assert "flagged_near_duplicates" in report
    assert report["variants"][0]["variant_spec_id"].startswith("spec_")
