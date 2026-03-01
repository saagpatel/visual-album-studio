from vas_studio import AnomalyTriageServiceV1


def test_itnc_002_triage_enrichment_persists_reports(runtime):
    now = 1_710_000_000
    runtime.db.execute(
        "INSERT INTO connector_diagnostics(id, connector, severity, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
        ("diag_nc2_1", "youtube", "error", "{}", now),
    )
    runtime.db.execute(
        "INSERT INTO connector_diagnostics(id, connector, severity, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
        ("diag_nc2_2", "youtube", "error", "{}", now),
    )
    runtime.db.execute(
        "INSERT INTO connector_diagnostics(id, connector, severity, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
        ("diag_nc2_3", "youtube", "error", "{}", now),
    )
    runtime.db.commit()

    service = AnomalyTriageServiceV1(runtime.db)
    result = service.enrich(project_id="proj_nc2", since_epoch=now - 1)

    assert result["ok"] is True
    assert len(result["triaged"]) >= 1
    assert all("recommendations" in row for row in result["triaged"])

    rows = runtime.db.execute("SELECT COUNT(*) AS c FROM anomaly_triage_reports WHERE project_id = 'proj_nc2'").fetchone()
    assert int(rows["c"]) == len(result["triaged"])

    recent = service.recent_reports(project_id="proj_nc2")
    assert recent["ok"] is True
    assert len(recent["reports"]) == len(result["triaged"])
