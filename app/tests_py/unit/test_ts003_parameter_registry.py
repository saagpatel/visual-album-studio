from vas_studio import ParameterDef, ParameterRegistry


def test_ts003_parameter_registry_validation_and_migration(runtime):
    registry = ParameterRegistry(runtime.db)
    registry.register(
        "motion_poster",
        [
            ParameterDef("mp.motion.float_amp", "float", 0.0, 80.0),
            ParameterDef("mp.beat.pulse_amount", "float", 0.0, 1.0),
        ],
    )

    ok, _ = registry.validate_overrides("motion_poster", {"mp.motion.float_amp": 22.0})
    assert ok

    bad, reason = registry.validate_overrides("motion_poster", {"mp.unknown": 1.0})
    assert not bad
    assert "unknown" in reason

    migrated_id = registry.migrate_preset("mp_preset_01", 2)
    assert migrated_id.endswith("_v2")
