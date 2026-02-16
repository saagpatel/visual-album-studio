from vas_studio import UxPlatformService


def test_ts013_command_dispatch_and_history(runtime):
    ux = UxPlatformService(runtime.db)
    ux.register_command(
        {
            "id": "export.retry_last",
            "label": "Retry Last Export",
            "description": "Retry the latest failed export",
            "idempotent": True,
        }
    )

    result = ux.run_command("export.retry_last", {"job_id": "job_123"})
    assert result["ok"]
    assert result["data"]["args"]["job_id"] == "job_123"

    missing = ux.run_command("not.real")
    assert not missing["ok"]

    rows = runtime.db.execute("SELECT COUNT(*) AS c FROM command_history").fetchone()
    assert int(rows["c"]) >= 1

    hits = ux.search_commands("retry")
    assert len(hits) == 1
    assert hits[0]["id"] == "export.retry_last"
