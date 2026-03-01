from vas_studio import CollaborationService, InMemoryCloudSyncAdapter


def test_itv2_402_collaboration_rbac_denies_viewer_edits(runtime):
    service = CollaborationService(runtime.db, sync_adapter=InMemoryCloudSyncAdapter(available=True))
    project_id = "project_rbac_it_402"
    service.set_member_role(project_id=project_id, user_id="viewer_1", role="viewer")
    service.set_member_role(project_id=project_id, user_id="editor_1", role="editor")

    denied = service.queue_local_edit(
        project_id=project_id,
        user_id="viewer_1",
        device_id="device_viewer",
        operation="set_caption",
        payload={"caption": "viewer"},
    )
    allowed = service.queue_local_edit(
        project_id=project_id,
        user_id="editor_1",
        device_id="device_editor",
        operation="set_caption",
        payload={"caption": "editor"},
    )

    assert denied["ok"] is False
    assert denied["error_code"] == "E_COLLAB_FORBIDDEN"
    assert allowed["ok"] is True
    assert allowed["mode"] == "cloud_online"


def test_itv2_402_collaboration_rbac_persists_role_changes(runtime):
    service = CollaborationService(runtime.db)
    project_id = "project_rbac_persist_402"

    service.set_member_role(project_id=project_id, user_id="member_1", role="viewer")
    assert service.get_member_role(project_id=project_id, user_id="member_1") == "viewer"
    service.set_member_role(project_id=project_id, user_id="member_1", role="owner")
    assert service.get_member_role(project_id=project_id, user_id="member_1") == "owner"
