from vas_studio import DRRehearsalRunnerV1


def test_tsnc_001_quarterly_rehearsal_has_expected_scenarios(runtime):
    runner = DRRehearsalRunnerV1(runtime.db)
    result = runner.run_quarterly_rehearsal(project_id="proj_tsnc001", sequence_start=700)

    assert result["ok"] is True
    report = result["report"]
    assert report["status"] == "passed"
    assert len(report["steps"]) == 4
    assert [step["sequence"] for step in report["steps"]] == [700, 701, 702, 703]


def test_tsnc_001_global_outage_records_local_only_failure_path(runtime):
    runner = DRRehearsalRunnerV1(runtime.db)
    result = runner.run_quarterly_rehearsal(project_id="proj_tsnc001_fail", sequence_start=800)
    global_step = next(step for step in result["report"]["steps"] if step["step_name"] == "global_outage_local_only")

    assert global_step["status"] == "passed"
    assert global_step["details"]["route"]["ok"] is False
    assert global_step["details"]["route"]["error_code"] == "E_REGION_UNAVAILABLE"


def test_tsnc_001_latest_report_not_found_error(runtime):
    runner = DRRehearsalRunnerV1(runtime.db)
    latest = runner.latest_report(project_id="missing_project")

    assert latest["ok"] is False
    assert latest["error_code"] == "E_DR_REPORT_NOT_FOUND"
