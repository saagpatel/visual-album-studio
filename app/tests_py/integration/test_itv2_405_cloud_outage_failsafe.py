from vas_studio import CollaborationService, InMemoryCloudSyncAdapter


def test_itv2_405_cloud_outage_failsafe_preserves_local_continuity(runtime):
    adapter = InMemoryCloudSyncAdapter(available=False)
    service = CollaborationService(runtime.db, sync_adapter=adapter)
    project_id = "project_outage_it_405"
    service.set_member_role(project_id=project_id, user_id="editor_1", role="editor")

    first = service.queue_local_edit(
        project_id=project_id,
        user_id="editor_1",
        device_id="device_1",
        operation="insert_track",
        payload={"track": 1},
    )
    second = service.queue_local_edit(
        project_id=project_id,
        user_id="editor_1",
        device_id="device_1",
        operation="insert_track",
        payload={"track": 2},
    )
    replay_offline = service.replay_queued(project_id=project_id)

    assert first["ok"] is True
    assert second["ok"] is True
    assert first["mode"] == "local_only"
    assert second["mode"] == "local_only"
    assert replay_offline["mode"] == "local_only"
    assert replay_offline["queued"] == 2

    adapter.set_available(True)
    replay_online = service.replay_queued(project_id=project_id)
    updates = adapter.fetch_updates(project_id)

    assert replay_online["ok"] is True
    assert replay_online["replayed"] == 2
    assert len(updates) == 2
