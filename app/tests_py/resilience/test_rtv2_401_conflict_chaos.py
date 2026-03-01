from vas_studio import CollaborationService


def test_rtv2_401_conflict_chaos_remains_deterministic(runtime):
    service = CollaborationService(runtime.db)
    project_id = "project_rtv2_401"

    for seq in range(1, 25):
        local = service.build_envelope(
            project_id=project_id,
            actor_id=f"local_{seq % 3}",
            device_id="device_local",
            operation="set_param",
            payload={"value": seq},
            sequence=seq,
        )
        remote = service.build_envelope(
            project_id=project_id,
            actor_id=f"remote_{seq % 5}",
            device_id="device_remote",
            operation="set_param",
            payload={"value": seq + 1},
            sequence=seq + (1 if seq % 2 == 0 else 0),
        )

        first = service.resolve_conflict(
            project_id=project_id,
            resource_id=f"resource_{seq}",
            local_envelope=local,
            remote_envelope=remote,
        )
        second = service.resolve_conflict(
            project_id=project_id,
            resource_id=f"resource_{seq}",
            local_envelope=local,
            remote_envelope=remote,
        )

        assert first["conflict"]["winner_actor_id"] == second["conflict"]["winner_actor_id"]
        assert first["conflict"]["winner_sequence"] == second["conflict"]["winner_sequence"]
