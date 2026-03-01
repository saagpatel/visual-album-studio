from vas_studio import DRRehearsalRunnerV1


def test_atnc_001_dr_rehearsal_runner(runtime):
    runner = DRRehearsalRunnerV1(runtime.db)
    result = runner.run_quarterly_rehearsal(project_id="proj_atnc001", sequence_start=1000)

    assert result["ok"] is True
    report = result["report"]
    assert report["status"] == "passed"

    step_names = [step["step_name"] for step in report["steps"]]
    assert step_names == [
        "active_active_healthy",
        "primary_outage_failover",
        "active_outage_dr_only",
        "global_outage_local_only",
    ]

    failover = next(step for step in report["steps"] if step["step_name"] == "primary_outage_failover")
    assert failover["details"]["route"]["region"] == "us-east-1"

    rows = runtime.db.execute("SELECT COUNT(*) AS c FROM dr_rehearsal_runs WHERE project_id = 'proj_atnc001'").fetchone()
    assert int(rows["c"]) == 1
