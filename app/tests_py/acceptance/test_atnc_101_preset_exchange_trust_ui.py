from vas_studio import PresetExchangeServiceV1, PresetTrustUxServiceV1


def test_atnc_101_preset_exchange_trust_ui(runtime):
    exchange = PresetExchangeServiceV1(runtime.db)
    ux = PresetTrustUxServiceV1(runtime.db, exchange_service=exchange)

    bundle = exchange.build_bundle(
        preset_id="preset_atnc101",
        source_project_id="src_at",
        owner_user_id="owner",
        mode="photo_animator",
        parameters={"ph.parallax.amount": 0.45, "ph.parallax.layer_count": 4},
        allowed_user_ids=["owner", "editor"],
    )["bundle"]

    success = ux.state_matrix(bundle_payload=bundle, keyboard_only=True)
    assert success["state"]["view_state"] == "success"
    assert len(success["state"]["focus_order"]) >= 3

    tampered = dict(bundle)
    tampered["parameters"] = dict(bundle["parameters"])
    tampered["parameters"]["ph.parallax.amount"] = 9.0
    error = ux.state_matrix(bundle_payload=tampered)
    assert error["state"]["view_state"] == "error"

    rec = ux.record_state(preset_id="preset_atnc101", actor_id="editor", state_payload=success["state"])
    assert rec["ok"] is True
