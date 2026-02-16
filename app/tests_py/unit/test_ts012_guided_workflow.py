from vas_studio import UxPlatformService


def test_ts012_guided_workflow_state_transitions(runtime):
    ux = UxPlatformService(runtime.db)

    s0 = ux.guided_workflow_status({})
    assert s0["next_step"] == "import_assets"
    assert not s0["can_queue_export"]

    s1 = ux.guided_workflow_status({"assets_imported": True})
    assert s1["next_step"] == "select_preset"

    s2 = ux.guided_workflow_status({"assets_imported": True, "preset_selected": True})
    assert s2["next_step"] == "fix_provenance"

    s3 = ux.guided_workflow_status(
        {"assets_imported": True, "preset_selected": True, "provenance_complete": True}
    )
    assert s3["next_step"] == "queue_export"
    assert s3["can_queue_export"]

    s4 = ux.guided_workflow_status(
        {
            "assets_imported": True,
            "preset_selected": True,
            "provenance_complete": True,
            "export_queued": True,
        }
    )
    assert s4["is_complete"]
