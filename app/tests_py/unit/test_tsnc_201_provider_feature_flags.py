from vas_studio import ProviderFeatureFlagServiceV1


def test_tsnc_201_defaults_include_stable_providers(runtime):
    service = ProviderFeatureFlagServiceV1(runtime.db)

    assert service.is_enabled("youtube") is True
    assert service.is_enabled("linkedin") is False


def test_tsnc_201_set_flag_updates_state(runtime):
    service = ProviderFeatureFlagServiceV1(runtime.db)
    updated = service.set_flag(provider="linkedin", enabled=True, rollout_stage="beta", candidate=True)

    assert updated["ok"] is True
    assert service.is_enabled("linkedin") is True


def test_tsnc_201_filter_enabled(runtime):
    service = ProviderFeatureFlagServiceV1(runtime.db)
    service.set_flag(provider="linkedin", enabled=False, rollout_stage="canary", candidate=True)
    filtered = service.filter_enabled(["youtube", "linkedin", "x"])

    assert filtered == ["youtube", "x"]
