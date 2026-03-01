from pathlib import Path

from vas_studio import PresetExchangeServiceV1


def test_atpv2_002_style_exchange(runtime, test_root):
    service = PresetExchangeServiceV1(runtime.db)
    export_path = Path(test_root) / "out" / "preset_exchange" / "bundle.json"

    built = service.build_bundle(
        preset_id="preset_atpv2_002",
        source_project_id="project_src_at",
        owner_user_id="owner_at",
        mode="photo_animator",
        parameters={"ph.parallax.layer_count": 4, "ph.parallax.amount": 0.45},
        metadata={"theme": "poster"},
        allowed_user_ids=["owner_at", "editor_at"],
    )
    assert built["ok"] is True

    bundle = built["bundle"]
    assert service.write_bundle(bundle, export_path)["ok"] is True
    loaded = service.read_bundle(export_path)
    assert loaded["ok"] is True

    imported = service.import_bundle(
        bundle_payload=loaded["bundle"],
        target_project_id="project_tgt_at",
        actor_user_id="editor_at",
        can_edit_target=True,
    )
    assert imported["ok"] is True

    incompatible = dict(loaded["bundle"])
    incompatible["schema_version"] = 99
    incompatible_result = service.import_bundle(
        bundle_payload=incompatible,
        target_project_id="project_tgt_at",
        actor_user_id="editor_at",
        can_edit_target=True,
    )
    assert incompatible_result["ok"] is False
    assert incompatible_result["error_code"] == "E_PRESET_SCHEMA_INCOMPATIBLE"

    tampered = dict(loaded["bundle"])
    tampered["parameters"] = dict(loaded["bundle"]["parameters"])
    tampered["parameters"]["ph.parallax.amount"] = 1.5
    tampered_result = service.import_bundle(
        bundle_payload=tampered,
        target_project_id="project_tgt_at",
        actor_user_id="editor_at",
        can_edit_target=True,
    )
    assert tampered_result["ok"] is False
    assert tampered_result["error_code"] == "E_PRESET_SIGNATURE_INVALID"

    denied = service.import_bundle(
        bundle_payload=loaded["bundle"],
        target_project_id="project_tgt_at",
        actor_user_id="viewer_at",
        can_edit_target=True,
    )
    assert denied["ok"] is False
    assert denied["error_code"] == "E_PRESET_PERMISSION_DENIED"

    summary = runtime.db.execute(
        """
        SELECT
          SUM(CASE WHEN status='imported' THEN 1 ELSE 0 END) AS imported_count,
          SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) AS failed_count
        FROM preset_exchange_events
        WHERE target_project_id = 'project_tgt_at'
        """
    ).fetchone()
    assert int(summary["imported_count"]) == 1
    assert int(summary["failed_count"]) == 3
