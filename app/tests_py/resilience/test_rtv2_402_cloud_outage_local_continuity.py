from vas_studio import CollaborationService, InMemoryCloudSyncAdapter


def test_rtv2_402_cloud_outage_local_continuity(runtime):
    adapter = InMemoryCloudSyncAdapter(available=False)
    service = CollaborationService(runtime.db, sync_adapter=adapter)
    project_id = "project_rtv2_402"
    service.set_member_role(project_id=project_id, user_id="editor_1", role="editor")

    for index in range(6):
        queued = service.queue_local_edit(
            project_id=project_id,
            user_id="editor_1",
            device_id="device_editor",
            operation="add_marker",
            payload={"marker": index},
        )
        assert queued["ok"] is True
        assert queued["mode"] == "local_only"

    offline = service.replay_queued(project_id=project_id)
    assert offline["mode"] == "local_only"
    assert offline["queued"] == 6

    adapter.set_available(True)
    online = service.replay_queued(project_id=project_id)
    updates = adapter.fetch_updates(project_id=project_id, since_sequence=0)

    assert online["ok"] is True
    assert online["replayed"] == 6
    assert len(updates) == 6
