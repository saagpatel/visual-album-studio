from vas_studio import CollaborationService


def test_tsv2_401_collaboration_rbac_enforces_roles(runtime):
    service = CollaborationService(runtime.db)
    project_id = "project_rbac_401"
    assert service.set_member_role(project_id=project_id, user_id="owner_1", role="owner")["ok"] is True
    assert service.set_member_role(project_id=project_id, user_id="editor_1", role="editor")["ok"] is True
    assert service.set_member_role(project_id=project_id, user_id="viewer_1", role="viewer")["ok"] is True

    assert service.authorize(project_id=project_id, user_id="owner_1", action="edit") is True
    assert service.authorize(project_id=project_id, user_id="editor_1", action="sync") is True
    assert service.authorize(project_id=project_id, user_id="viewer_1", action="edit") is False
    assert service.authorize(project_id=project_id, user_id="viewer_1", action="view") is True


def test_tsv2_401_collaboration_rbac_rejects_invalid_role(runtime):
    service = CollaborationService(runtime.db)
    result = service.set_member_role(project_id="project_rbac_401", user_id="user_1", role="admin")
    assert result["ok"] is False
    assert result["error_code"] == "E_ROLE_INVALID"
