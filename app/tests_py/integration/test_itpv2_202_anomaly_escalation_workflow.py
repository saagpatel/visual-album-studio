from vas_studio import AuditDashboardServiceV1


def test_itpv2_202_anomaly_escalation_workflow(runtime):
    now = 1_700_000_123

    runtime.db.execute(
        "INSERT INTO connector_diagnostics(id, connector, severity, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
        ("diag_i1", "facebook_reels", "error", "{}", now),
    )
    runtime.db.execute(
        "INSERT INTO connector_diagnostics(id, connector, severity, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
        ("diag_i2", "facebook_reels", "error", "{}", now),
    )
    runtime.db.execute(
        "INSERT INTO connector_diagnostics(id, connector, severity, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
        ("diag_i3", "facebook_reels", "error", "{}", now),
    )
    runtime.db.execute(
        "INSERT INTO cloud_sync_queue(id, project_id, envelope_json, status, error_code, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("q_i1", "project_itpv2_202", "{}", "failed", "E_FAIL", now, now),
    )
    runtime.db.execute(
        "INSERT INTO cloud_sync_replay_log(id, project_id, queue_id, sequence, status, detail_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("r_i1", "project_itpv2_202", "q_i1", 1, "failed", "{}", now),
    )
    runtime.db.execute(
        "INSERT INTO cloud_sync_replay_log(id, project_id, queue_id, sequence, status, detail_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("r_i2", "project_itpv2_202", "q_i1", 2, "failed", "{}", now),
    )
    runtime.db.commit()

    service = AuditDashboardServiceV1(runtime.db)
    result = service.record_and_escalate(project_id="project_itpv2_202", since_epoch=now - 1)

    assert result["ok"] is True
    assert len(result["signals"]) >= 2
    assert len(result["escalations"]) == len(result["signals"])
    assert all(item["owner"] == "saagar210" for item in result["escalations"])

    rows = runtime.db.execute(
        "SELECT COUNT(*) AS c FROM audit_anomaly_events WHERE project_id = ? AND status = 'open'",
        ("project_itpv2_202",),
    ).fetchone()
    assert int(rows["c"]) == len(result["signals"])
