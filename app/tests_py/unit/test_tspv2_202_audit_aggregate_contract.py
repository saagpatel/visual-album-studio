from vas_studio import AuditDashboardServiceV1


def test_tspv2_202_audit_aggregate_empty_contract(runtime):
    service = AuditDashboardServiceV1(runtime.db)
    result = service.aggregate(project_id="project_audit_empty")

    assert result["ok"] is True
    aggregate = result["aggregate"]
    assert aggregate["total_events"] == 0
    assert aggregate["error_events"] == 0
    assert aggregate["failed_sync_replays"] == 0
    assert aggregate["conflict_count"] == 0


def test_tspv2_202_audit_aggregate_counts(runtime):
    now = 1_700_000_000
    runtime.db.execute(
        "INSERT INTO connector_diagnostics(id, connector, severity, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
        ("diag_a1", "x", "error", "{}", now),
    )
    runtime.db.execute(
        "INSERT INTO connector_diagnostics(id, connector, severity, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
        ("diag_a2", "x", "warn", "{}", now),
    )
    runtime.db.execute(
        "INSERT INTO cloud_sync_queue(id, project_id, envelope_json, status, error_code, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("q_a1", "project_audit_counts", "{}", "failed", "E_FAIL", now, now),
    )
    runtime.db.execute(
        "INSERT INTO cloud_sync_replay_log(id, project_id, queue_id, sequence, status, detail_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("r_a1", "project_audit_counts", "q_a1", 1, "failed", "{}", now),
    )
    runtime.db.execute(
        "INSERT INTO collaboration_conflicts(id, project_id, resource_id, winner_actor_id, winner_sequence, resolution_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("c_a1", "project_audit_counts", "res_1", "user_1", 2, "{}", now),
    )
    runtime.db.commit()

    service = AuditDashboardServiceV1(runtime.db)
    result = service.aggregate(project_id="project_audit_counts", since_epoch=now - 1)
    aggregate = result["aggregate"]

    assert aggregate["total_events"] == 2
    assert aggregate["error_events"] == 1
    assert aggregate["warn_events"] == 1
    assert aggregate["failed_sync_replays"] == 1
    assert aggregate["conflict_count"] == 1
    assert aggregate["connector_breakdown"]["x"] == 2
