from vas_studio import DRRehearsalRunnerV1


def test_itnc_001_rehearsal_persists_run_and_steps(runtime):
    runner = DRRehearsalRunnerV1(runtime.db)
    result = runner.run_quarterly_rehearsal(project_id="proj_itnc001", sequence_start=900)
    report = result["report"]

    run_row = runtime.db.execute("SELECT status, quarter_label FROM dr_rehearsal_runs WHERE id = ?", (report["run_id"],)).fetchone()
    step_rows = runtime.db.execute("SELECT COUNT(*) AS c FROM dr_rehearsal_steps WHERE run_id = ?", (report["run_id"],)).fetchone()

    assert run_row is not None
    assert run_row["status"] == "passed"
    assert "-Q" in run_row["quarter_label"]
    assert int(step_rows["c"]) == 4

    latest = runner.latest_report(project_id="proj_itnc001")
    assert latest["ok"] is True
    assert latest["report"]["run_id"] == report["run_id"]
