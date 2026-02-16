from vas_studio import UxPlatformService


def test_it011_preset_migration_mixed_schema_behavior(runtime):
    ux = UxPlatformService(runtime.db)
    advice = ux.preset_migration_advice(
        [
            {"id": "preset_old", "schema_version": 1},
            {"id": "preset_current", "schema_version": 2},
            {"id": "preset_legacy", "schema_version": 0},
        ],
        target_schema=2,
    )
    assert advice["target_schema"] == 2
    warning_ids = {item["preset_id"] for item in advice["warnings"]}
    assert "preset_old" in warning_ids
    assert "preset_legacy" in warning_ids
    assert "preset_current" not in warning_ids
