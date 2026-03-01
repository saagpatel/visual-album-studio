from vas_studio import CollaborationService, CollaborationTimelineServiceV1, InMemoryCloudSyncAdapter


def test_atnc_103_collab_timeline_visualizer(runtime):
    adapter = InMemoryCloudSyncAdapter(available=False)
    collab = CollaborationService(runtime.db, sync_adapter=adapter)
    project_id = "proj_atnc103"

    collab.set_member_role(project_id=project_id, user_id="editor_1", role="editor")
    collab.queue_local_edit(
        project_id=project_id,
        user_id="editor_1",
        device_id="device_1",
        operation="set_title",
        payload={"title": "offline"},
    )

    timeline_service = CollaborationTimelineServiceV1(runtime.db)
    timeline = timeline_service.build_timeline(project_id=project_id, actor_id="editor_1")

    assert timeline["ok"] is True
    assert timeline["event_count"] >= 1
    assert len(timeline["keyboard_path"]) >= 1
