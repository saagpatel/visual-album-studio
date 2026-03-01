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
    project_id = "project_audit_counts"
    runtime.db.execute(
        "INSERT INTO connector_diagnostics(id, project_id, connector, severity, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("diag_a1", project_id, "x", "error", "{}", now),
    )
    runtime.db.execute(
        "INSERT INTO connector_diagnostics(id, project_id, connector, severity, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("diag_a2", project_id, "x", "warn", "{}", now),
    )
    runtime.db.execute(
        "INSERT INTO cloud_sync_queue(id, project_id, envelope_json, status, error_code, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("q_a1", project_id, "{}", "failed", "E_FAIL", now, now),
    )
    runtime.db.execute(
        "INSERT INTO cloud_sync_replay_log(id, project_id, queue_id, sequence, status, detail_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("r_a1", project_id, "q_a1", 1, "failed", "{}", now),
    )
    runtime.db.execute(
        "INSERT INTO collaboration_conflicts(id, project_id, resource_id, winner_actor_id, winner_sequence, resolution_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("c_a1", project_id, "res_1", "user_1", 2, "{}", now),
    )
    runtime.db.commit()

    service = AuditDashboardServiceV1(runtime.db)
    result = service.aggregate(project_id=project_id, since_epoch=now - 1)
    aggregate = result["aggregate"]

    assert aggregate["total_events"] == 2
    assert aggregate["error_events"] == 1
    assert aggregate["warn_events"] == 1
    assert aggregate["failed_sync_replays"] == 1
    assert aggregate["conflict_count"] == 1
    assert aggregate["connector_breakdown"]["x"] == 2


def test_tspv2_202_audit_aggregate_isolates_by_project(runtime):
    now = 1_700_000_100
    runtime.db.execute(
        "INSERT INTO connector_diagnostics(id, project_id, connector, severity, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("diag_iso_a", "project_a", "x", "error", "{}", now),
    )
    runtime.db.execute(
        "INSERT INTO connector_diagnostics(id, project_id, connector, severity, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("diag_iso_b", "project_b", "x", "error", "{}", now),
    )
    runtime.db.commit()

    service = AuditDashboardServiceV1(runtime.db)
    result_a = service.aggregate(project_id="project_a", since_epoch=now - 1)
    result_b = service.aggregate(project_id="project_b", since_epoch=now - 1)

    assert result_a["aggregate"]["total_events"] == 1
    assert result_b["aggregate"]["total_events"] == 1
