from vas_studio import QuotaBudget


def test_ts010_quota_budgeting():
    q = QuotaBudget(daily_budget=200)
    est = q.estimate_publish(with_thumbnail=True, with_playlist=False)
    assert est == 150
    assert q.can_run(est)
    q.consume(est)
    assert not q.can_run(est)
