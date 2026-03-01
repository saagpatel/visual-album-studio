from pathlib import Path

from vas_studio import CollaborationService, InMemoryCloudSyncAdapter, LocalObjectStorageAdapter


def test_atv2401_train4_cloud_sync_collaboration_and_outage_failsafe(runtime, test_root):
    adapter = InMemoryCloudSyncAdapter(available=False)
    storage = LocalObjectStorageAdapter(test_root / "out" / "cloud_storage")
    service = CollaborationService(runtime.db, sync_adapter=adapter, storage_adapter=storage)
    project_id = "atv2401_project"

    service.set_member_role(project_id=project_id, user_id="owner_1", role="owner")
    service.set_member_role(project_id=project_id, user_id="editor_1", role="editor")
    service.set_member_role(project_id=project_id, user_id="viewer_1", role="viewer")

    denied = service.queue_local_edit(
        project_id=project_id,
        user_id="viewer_1",
        device_id="device_viewer",
        operation="set_title",
        payload={"title": "blocked"},
    )
    first = service.queue_local_edit(
        project_id=project_id,
        user_id="editor_1",
        device_id="device_editor",
        operation="set_title",
        payload={"title": "offline-a"},
    )
    second = service.queue_local_edit(
        project_id=project_id,
        user_id="editor_1",
        device_id="device_editor",
        operation="set_title",
        payload={"title": "offline-b"},
    )
    replay_offline = service.replay_queued(project_id=project_id)

    assert denied["ok"] is False
    assert denied["error_code"] == "E_COLLAB_FORBIDDEN"
    assert first["ok"] is True
    assert second["ok"] is True
    assert replay_offline["mode"] == "local_only"
    assert replay_offline["queued"] == 2
    assert replay_offline["replayed"] == 0

    adapter.set_available(True)
    replay_online = service.replay_queued(project_id=project_id)
    assert replay_online["ok"] is True
    assert replay_online["replayed"] == 2
    assert len(adapter.fetch_updates(project_id=project_id, since_sequence=0)) == 2

    local = service.build_envelope(
        project_id=project_id,
        actor_id="editor_1",
        device_id="device_editor",
        operation="set_filter",
        payload={"filter": "grain"},
        sequence=10,
    )
    remote = service.build_envelope(
        project_id=project_id,
        actor_id="owner_1",
        device_id="device_owner",
        operation="set_filter",
        payload={"filter": "sharp"},
        sequence=11,
    )
    conflict = service.resolve_conflict(
        project_id=project_id,
        resource_id="timeline:fx:1",
        local_envelope=local,
        remote_envelope=remote,
    )
    assert conflict["ok"] is True
    assert conflict["conflict"]["winner_sequence"] == 11
    assert conflict["conflict"]["rule_id"] == "prefer_newer_sequence_then_actor_then_payload_hash"

    stored = service.store_object_reference(
        project_id=project_id,
        object_key="exports/final.mp4",
        data=b"train4-binary",
        schema_version=1,
    )
    obj = service.object_reference(project_id=project_id, object_key="exports/final.mp4")
    assert stored["ok"] is True
    assert obj is not None
    assert int(obj["schema_version"]) == 1
    assert Path(storage.get_metadata(project_id=project_id, object_key="exports/final.mp4")["path"]).exists()

    adapter.set_available(False)
    outage_edit = service.queue_local_edit(
        project_id=project_id,
        user_id="editor_1",
        device_id="device_editor",
        operation="set_title",
        payload={"title": "offline-c"},
    )
    outage_status = service.replay_queued(project_id=project_id)
    assert outage_edit["ok"] is True
    assert outage_edit["mode"] == "local_only"
    assert outage_status["mode"] == "local_only"
