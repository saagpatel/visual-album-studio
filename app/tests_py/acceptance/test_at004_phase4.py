from vas_studio import BatchPlanner, RemixEngine


def test_at004_batch_and_guardrails():
    remix = RemixEngine()
    planner = BatchPlanner()
    variants = remix.generate_variants(base_seed=1000, count=100)
    assert len(variants) == 100

    base = variants[0]
    valid_count = 0
    for v in variants[1:]:
        ok, _ = remix.validate_variant(base, v, min_changed=5, threshold=0.5)
        if ok:
            valid_count += 1

    assert valid_count >= 50

    plan = planner.create_plan(variants, max_concurrent=4)
    assert len(plan["items"]) == 100

    report = planner.reviewer_report(variants, remix)
    assert report["summary"]["count"] == 100
