from vas_studio import PresetExchangeServiceV1, PresetTrustUxServiceV1


def _bundle(runtime):
    exchange = PresetExchangeServiceV1(runtime.db)
    return exchange.build_bundle(
        preset_id="preset_tsnc101",
        source_project_id="src",
        owner_user_id="owner",
        mode="photo_animator",
        parameters={"ph.kb.end_zoom": 1.2},
        allowed_user_ids=["owner", "editor"],
    )["bundle"]


def test_tsnc_101_loading_and_empty_states(runtime):
    ux = PresetTrustUxServiceV1(runtime.db)
    loading = ux.state_matrix(bundle_payload=None, is_loading=True)
    empty = ux.state_matrix(bundle_payload=None, is_loading=False)

    assert loading["state"]["view_state"] == "loading"
    assert empty["state"]["view_state"] == "empty"


def test_tsnc_101_success_and_disabled_states(runtime):
    ux = PresetTrustUxServiceV1(runtime.db)
    bundle = _bundle(runtime)

    success = ux.state_matrix(bundle_payload=bundle)
    disabled = ux.state_matrix(bundle_payload=bundle, disabled=True)

    assert success["state"]["view_state"] == "success"
    assert success["state"]["signature_state"] == "valid"
    assert disabled["state"]["view_state"] == "disabled"


def test_tsnc_101_error_state_for_tampered_bundle(runtime):
    ux = PresetTrustUxServiceV1(runtime.db)
    bundle = _bundle(runtime)
    bundle["parameters"]["ph.kb.end_zoom"] = 9.9

    state = ux.state_matrix(bundle_payload=bundle)

    assert state["state"]["view_state"] == "error"
    assert state["state"]["signature_state"] == "invalid"
