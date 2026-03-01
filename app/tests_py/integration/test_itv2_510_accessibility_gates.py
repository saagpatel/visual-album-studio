from vas_studio import UxPlatformService


def test_itv2_510_accessibility_gates_pass_for_critical_keyboard_path(runtime):
    service = UxPlatformService(runtime.db)
    report = service.validate_accessibility(
        "publish_and_collab_flow",
        {
            "focus_order": [
                "provider_selector",
                "metadata_title",
                "policy_preflight",
                "submit_publish",
                "conflict_resolution_modal",
                "outage_banner_retry",
            ],
            "has_focus_indicators": True,
            "reduced_motion_supported": True,
            "contrast_checks": [
                {"name": "surface_text", "ratio": 7.2},
                {"name": "status_badge", "ratio": 5.1},
            ],
        },
    )
    assert report["ok"] is True
    assert report["checks"]["focus_count"] >= 6
    assert report["checks"]["has_focus_indicators"] is True


def test_itv2_510_accessibility_gates_fail_on_missing_focus_and_contrast(runtime):
    service = UxPlatformService(runtime.db)
    report = service.validate_accessibility(
        "invalid_flow",
        {
            "focus_order": [],
            "has_focus_indicators": False,
            "reduced_motion_supported": False,
            "contrast_checks": [{"name": "bad", "ratio": 3.0}],
        },
    )
    assert report["ok"] is False
    assert "focus_order_empty" in report["violations"]
    assert "focus_indicators_missing" in report["violations"]
    assert "reduced_motion_missing" in report["violations"]
    assert "contrast_low:bad" in report["violations"]
