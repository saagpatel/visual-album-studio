from vas_studio import CollaborationService, CollaborationTimelineServiceV1, InMemoryCloudSyncAdapter


def test_itnc_103_timeline_contains_queue_replay_conflict(runtime):
    adapter = InMemoryCloudSyncAdapter(available=True)
    collab = CollaborationService(runtime.db, sync_adapter=adapter)
    project_id = "proj_itnc103"

    collab.set_member_role(project_id=project_id, user_id="editor_1", role="editor")
    queued = collab.queue_local_edit(
        project_id=project_id,
        user_id="editor_1",
        device_id="device_1",
        operation="set_title",
        payload={"title": "A"},
    )
    collab.replay_queued(project_id=project_id)

    local = collab.build_envelope(project_id=project_id, actor_id="editor_1", device_id="device_1", operation="set_title", payload={"title": "L"}, sequence=3)
    remote = collab.build_envelope(project_id=project_id, actor_id="editor_2", device_id="device_2", operation="set_title", payload={"title": "R"}, sequence=3)
    collab.resolve_conflict(project_id=project_id, resource_id="title", local_envelope=local, remote_envelope=remote)

    timeline = CollaborationTimelineServiceV1(runtime.db).build_timeline(project_id=project_id)

    assert queued["ok"] is True
    assert timeline["ok"] is True
    kinds = {event["event_type"] for event in timeline["events"]}
    assert "sync_queue" in kinds
    assert "sync_replay" in kinds
    assert "conflict" in kinds


def test_itnc_103_timeline_actor_filter_applies_to_replay(runtime):
    adapter = InMemoryCloudSyncAdapter(available=True)
    collab = CollaborationService(runtime.db, sync_adapter=adapter)
    project_id = "proj_itnc103_filter"

    collab.set_member_role(project_id=project_id, user_id="editor_1", role="editor")
    collab.set_member_role(project_id=project_id, user_id="editor_2", role="editor")
    collab.queue_local_edit(
        project_id=project_id,
        user_id="editor_1",
        device_id="device_1",
        operation="set_title",
        payload={"title": "A"},
    )
    collab.queue_local_edit(
        project_id=project_id,
        user_id="editor_2",
        device_id="device_2",
        operation="set_title",
        payload={"title": "B"},
    )
    collab.replay_queued(project_id=project_id)

    timeline = CollaborationTimelineServiceV1(runtime.db).build_timeline(project_id=project_id, actor_id="editor_1")

    assert timeline["ok"] is True
    assert len(timeline["events"]) >= 1
    assert all(event["actor_id"] == "editor_1" for event in timeline["events"])
