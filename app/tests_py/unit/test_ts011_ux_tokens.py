from vas_studio import UxPlatformService


def test_ts011_ux_token_and_component_state_validation(runtime):
    ux = UxPlatformService(runtime.db)
    tokens = ux.get_tokens()
    assert "spacing_scale" in tokens
    assert len(tokens["spacing_scale"]) >= 4
    assert tokens["color_roles"]["accent"].startswith("#")

    spec = ux.resolve_component("button.primary", "primary", "loading")
    assert spec["id"] == "button.primary"
    assert spec["state"] == "loading"
    assert "tokens" in spec
