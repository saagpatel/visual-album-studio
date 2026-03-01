from vas_studio import PresetExchangeServiceV1


def test_itpv2_002_import_permission_and_signature_paths(runtime):
    service = PresetExchangeServiceV1(runtime.db)
    built = service.build_bundle(
        preset_id="preset_itpv2_002",
        source_project_id="project_source_it",
        owner_user_id="owner_1",
        mode="photo_animator",
        parameters={"ph.kb.start_zoom": 1.0, "ph.kb.end_zoom": 1.2},
        allowed_user_ids=["owner_1", "editor_1"],
    )
    bundle = built["bundle"]

    denied = service.import_bundle(
        bundle_payload=bundle,
        target_project_id="project_target_it",
        actor_user_id="editor_1",
        can_edit_target=False,
    )
    assert denied["ok"] is False
    assert denied["error_code"] == "E_PRESET_PERMISSION_DENIED"

    tampered = dict(bundle)
    tampered["parameters"] = dict(bundle["parameters"])
    tampered["parameters"]["ph.kb.end_zoom"] = 2.5
    invalid = service.import_bundle(
        bundle_payload=tampered,
        target_project_id="project_target_it",
        actor_user_id="editor_1",
        can_edit_target=True,
    )
    assert invalid["ok"] is False
    assert invalid["error_code"] == "E_PRESET_SIGNATURE_INVALID"

    imported = service.import_bundle(
        bundle_payload=bundle,
        target_project_id="project_target_it",
        actor_user_id="editor_1",
        can_edit_target=True,
    )
    assert imported["ok"] is True
    assert imported["status"] == "imported"

    counts = runtime.db.execute(
        """
        SELECT
          SUM(CASE WHEN status = 'imported' THEN 1 ELSE 0 END) AS imported_count,
          SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_count
        FROM preset_exchange_events
        WHERE target_project_id = 'project_target_it'
        """
    ).fetchone()
    assert int(counts["imported_count"]) == 1
    assert int(counts["failed_count"]) == 2
