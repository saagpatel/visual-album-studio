from vas_studio import PresetExchangeServiceV1, PresetTrustUxServiceV1


def test_itnc_101_record_state_persists(runtime):
    exchange = PresetExchangeServiceV1(runtime.db)
    ux = PresetTrustUxServiceV1(runtime.db, exchange_service=exchange)

    bundle = exchange.build_bundle(
        preset_id="preset_itnc101",
        source_project_id="src_it",
        owner_user_id="owner",
        mode="photo_animator",
        parameters={"ph.parallax.amount": 0.4},
        allowed_user_ids=["owner", "editor"],
    )["bundle"]

    state = ux.state_matrix(bundle_payload=bundle)
    recorded = ux.record_state(preset_id="preset_itnc101", actor_id="editor", state_payload=state["state"])

    assert recorded["ok"] is True
    row = runtime.db.execute(
        "SELECT state, signature_valid FROM preset_trust_ui_events WHERE id = ?",
        (recorded["event_id"],),
    ).fetchone()
    assert row["state"] == "success"
    assert int(row["signature_valid"]) == 1
