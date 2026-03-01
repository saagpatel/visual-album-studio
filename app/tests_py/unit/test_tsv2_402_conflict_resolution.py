from vas_studio import CollaborationService


def test_tsv2_402_conflict_resolution_is_deterministic(runtime):
    service = CollaborationService(runtime.db)
    project_id = "project_conflict_402"

    local = service.build_envelope(
        project_id=project_id,
        actor_id="editor_a",
        device_id="device_a",
        operation="update_clip",
        payload={"cut": "A"},
        sequence=7,
    )
    remote = service.build_envelope(
        project_id=project_id,
        actor_id="editor_b",
        device_id="device_b",
        operation="update_clip",
        payload={"cut": "B"},
        sequence=9,
    )

    first = service.resolve_conflict(
        project_id=project_id,
        resource_id="timeline:clip:1",
        local_envelope=local,
        remote_envelope=remote,
    )
    second = service.resolve_conflict(
        project_id=project_id,
        resource_id="timeline:clip:1",
        local_envelope=local,
        remote_envelope=remote,
    )

    assert first["ok"] is True
    assert second["ok"] is True
    assert first["conflict"]["winner_actor_id"] == second["conflict"]["winner_actor_id"]
    assert first["conflict"]["winner_sequence"] == second["conflict"]["winner_sequence"]
    assert first["conflict"]["rule_id"] == "prefer_newer_sequence_then_actor_then_payload_hash"


def test_tsv2_402_conflict_resolution_tie_breaks_by_actor_and_payload(runtime):
    service = CollaborationService(runtime.db)
    project_id = "project_conflict_402_tie"

    local = service.build_envelope(
        project_id=project_id,
        actor_id="aaa",
        device_id="device_a",
        operation="update",
        payload={"v": "x"},
        sequence=5,
    )
    remote = service.build_envelope(
        project_id=project_id,
        actor_id="bbb",
        device_id="device_b",
        operation="update",
        payload={"v": "x"},
        sequence=5,
    )

    resolved = service.resolve_conflict(
        project_id=project_id,
        resource_id="timeline:clip:2",
        local_envelope=local,
        remote_envelope=remote,
    )
    assert resolved["ok"] is True
    assert resolved["conflict"]["winner_actor_id"] == "bbb"
    assert resolved["conflict"]["winner_sequence"] == 5
