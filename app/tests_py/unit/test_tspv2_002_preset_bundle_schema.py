from vas_studio import PresetExchangeServiceV1


def test_tspv2_002_bundle_schema_and_signature(runtime):
    service = PresetExchangeServiceV1(runtime.db)
    built = service.build_bundle(
        preset_id="pv2preset_002",
        source_project_id="project_src",
        owner_user_id="owner_1",
        mode="photo_animator",
        parameters={"ph.kb.end_zoom": 1.2},
        allowed_user_ids=["owner_1", "editor_1"],
    )
    assert built["ok"] is True

    bundle = built["bundle"]
    report = service.compatibility_report(bundle)
    verify = service.verify_signature(bundle)

    assert report["ok"] is True
    assert report["normalized_parameters"]["ph.kb.end_zoom"] == 1.2
    assert verify["ok"] is True


def test_tspv2_002_schema_incompatible_and_missing_fields(runtime):
    service = PresetExchangeServiceV1(runtime.db)

    incompatible = {
        "schema_version": 2,
        "preset_id": "bad",
        "source_project_id": "project_src",
        "owner_user_id": "owner_1",
        "mode": "",
        "parameters": {},
        "sharing": {"allowed_user_ids": ["owner_1"]},
        "signature": {},
    }
    report = service.compatibility_report(incompatible)

    assert report["ok"] is False
    assert "E_PRESET_SCHEMA_INCOMPATIBLE" in report["issues"]
    assert "E_PRESET_MODE_REQUIRED" in report["issues"]
    assert "E_PRESET_PARAMETERS_REQUIRED" in report["issues"]


def test_tspv2_002_signature_mismatch_detected(runtime):
    service = PresetExchangeServiceV1(runtime.db)
    built = service.build_bundle(
        preset_id="pv2preset_sig",
        source_project_id="project_src",
        owner_user_id="owner_1",
        mode="photo_animator",
        parameters={"ph.parallax.amount": 0.4},
        allowed_user_ids=["owner_1"],
    )
    bundle = built["bundle"]
    bundle["parameters"]["ph.parallax.amount"] = 9.9

    verify = service.verify_signature(bundle)

    assert verify["ok"] is False
    assert verify["error_code"] == "E_PRESET_SIGNATURE_INVALID"
