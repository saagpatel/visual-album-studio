from vas_studio import AuditDashboardServiceV1


def test_atpv2_202_audit_dashboard_anomaly(runtime):
    now = 1_700_000_456
    project_id = "project_atpv2_202"

    runtime.db.execute(
        "INSERT INTO connector_diagnostics(id, project_id, connector, severity, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("diag_at1", project_id, "x", "error", "{}", now),
    )
    runtime.db.execute(
        "INSERT INTO connector_diagnostics(id, project_id, connector, severity, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("diag_at2", project_id, "x", "error", "{}", now),
    )
    runtime.db.execute(
        "INSERT INTO connector_diagnostics(id, project_id, connector, severity, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("diag_at3", project_id, "x", "error", "{}", now),
    )
    runtime.db.execute(
        "INSERT INTO connector_diagnostics(id, project_id, connector, severity, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("diag_at4", project_id, "instagram", "warn", "{}", now),
    )
    runtime.db.execute(
        "INSERT INTO cloud_sync_queue(id, project_id, envelope_json, status, error_code, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("q_at1", project_id, "{}", "failed", "E_FAIL", now, now),
    )
    runtime.db.execute(
        "INSERT INTO cloud_sync_replay_log(id, project_id, queue_id, sequence, status, detail_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("r_at1", project_id, "q_at1", 1, "failed", "{}", now),
    )
    runtime.db.execute(
        "INSERT INTO cloud_sync_replay_log(id, project_id, queue_id, sequence, status, detail_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("r_at2", project_id, "q_at1", 2, "failed", "{}", now),
    )
    runtime.db.execute(
        "INSERT INTO collaboration_conflicts(id, project_id, resource_id, winner_actor_id, winner_sequence, resolution_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("c_at1", project_id, "clip_1", "user_1", 2, "{}", now),
    )
    runtime.db.execute(
        "INSERT INTO collaboration_conflicts(id, project_id, resource_id, winner_actor_id, winner_sequence, resolution_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("c_at2", project_id, "clip_2", "user_2", 3, "{}", now),
    )
    runtime.db.commit()

    service = AuditDashboardServiceV1(runtime.db)
    dashboard = service.dashboard(project_id=project_id, since_epoch=now - 1)

    assert dashboard["ok"] is True
    assert dashboard["aggregate"]["error_events"] >= 3
    assert dashboard["aggregate"]["failed_sync_replays"] >= 2
    assert dashboard["aggregate"]["conflict_count"] >= 2
    assert len(dashboard["signals"]) >= 3
    assert len(dashboard["escalations"]) == len(dashboard["signals"])
    assert len(dashboard["open_events"]) == len(dashboard["signals"])
