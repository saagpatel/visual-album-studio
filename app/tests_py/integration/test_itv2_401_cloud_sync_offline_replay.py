from vas_studio import CollaborationService, InMemoryCloudSyncAdapter


def test_itv2_401_cloud_sync_offline_replay(runtime):
    adapter = InMemoryCloudSyncAdapter(available=False)
    service = CollaborationService(runtime.db, sync_adapter=adapter)
    project_id = "project_sync_401"

    service.set_member_role(project_id=project_id, user_id="editor_1", role="editor")
    first = service.queue_local_edit(
        project_id=project_id,
        user_id="editor_1",
        device_id="device_1",
        operation="set_title",
        payload={"title": "A"},
    )
    second = service.queue_local_edit(
        project_id=project_id,
        user_id="editor_1",
        device_id="device_1",
        operation="set_title",
        payload={"title": "B"},
    )
    offline = service.replay_queued(project_id=project_id)

    assert first["ok"] is True
    assert second["ok"] is True
    assert offline["mode"] == "local_only"
    assert offline["queued"] == 2
    assert offline["replayed"] == 0

    adapter.set_available(True)
    replay = service.replay_queued(project_id=project_id)
    updates = adapter.fetch_updates(project_id, since_sequence=0)

    assert replay["ok"] is True
    assert replay["mode"] == "cloud_online"
    assert replay["replayed"] == 2
    assert len(updates) == 2
