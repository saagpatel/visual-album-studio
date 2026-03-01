from vas_studio import CollaborationService


def test_itv2_403_conflict_resolution_determinism(runtime):
    service = CollaborationService(runtime.db)
    project_id = "project_conflict_it_403"

    local = service.build_envelope(
        project_id=project_id,
        actor_id="editor_local",
        device_id="device_local",
        operation="set_effect",
        payload={"effect": "grain"},
        sequence=8,
    )
    remote = service.build_envelope(
        project_id=project_id,
        actor_id="editor_remote",
        device_id="device_remote",
        operation="set_effect",
        payload={"effect": "blur"},
        sequence=8,
    )

    first = service.resolve_conflict(
        project_id=project_id,
        resource_id="track:1",
        local_envelope=local,
        remote_envelope=remote,
    )
    second = service.resolve_conflict(
        project_id=project_id,
        resource_id="track:1",
        local_envelope=local,
        remote_envelope=remote,
    )
    rows = runtime.db.execute(
        "SELECT winner_actor_id, winner_sequence FROM collaboration_conflicts WHERE project_id = ?",
        (project_id,),
    ).fetchall()

    assert first["ok"] is True
    assert second["ok"] is True
    assert first["conflict"]["winner_actor_id"] == second["conflict"]["winner_actor_id"]
    assert len(rows) == 2
    assert rows[0]["winner_actor_id"] == rows[1]["winner_actor_id"]


def test_itv2_403_conflict_resolution_audit_payload(runtime):
    service = CollaborationService(runtime.db)
    project_id = "project_conflict_audit_403"
    local = service.build_envelope(
        project_id=project_id,
        actor_id="a",
        device_id="d1",
        operation="trim",
        payload={"start": 1},
        sequence=1,
    )
    remote = service.build_envelope(
        project_id=project_id,
        actor_id="b",
        device_id="d2",
        operation="trim",
        payload={"start": 2},
        sequence=2,
    )
    resolved = service.resolve_conflict(
        project_id=project_id,
        resource_id="clip:3",
        local_envelope=local,
        remote_envelope=remote,
    )
    assert resolved["ok"] is True
    assert resolved["conflict"]["details"]["winner_payload"] == {"start": 2}
    assert resolved["conflict"]["details"]["loser_payload"] == {"start": 1}
