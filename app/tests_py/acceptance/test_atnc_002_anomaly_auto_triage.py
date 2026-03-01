from vas_studio import AnomalyTriageServiceV1


def test_atnc_002_anomaly_auto_triage(runtime):
    now = 1_711_000_000
    project_id = "proj_atnc2"
    for idx in range(3):
        runtime.db.execute(
            "INSERT INTO connector_diagnostics(id, project_id, connector, severity, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (f"diag_atnc2_{idx}", project_id, "x", "error", "{}", now),
        )
    runtime.db.execute(
        "INSERT INTO cloud_sync_queue(id, project_id, envelope_json, status, error_code, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("q_atnc2", project_id, "{}", "failed", "E_FAIL", now, now),
    )
    runtime.db.execute(
        "INSERT INTO cloud_sync_replay_log(id, project_id, queue_id, sequence, status, detail_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("r_atnc2", project_id, "q_atnc2", 1, "failed", "{}", now),
    )
    runtime.db.commit()

    service = AnomalyTriageServiceV1(runtime.db)
    enriched = service.enrich(project_id=project_id, since_epoch=now - 1)

    assert enriched["ok"] is True
    assert len(enriched["triaged"]) >= 1
    first = enriched["triaged"][0]
    assert first["project_id"] == project_id
    assert len(first["recommendations"]) >= 1
