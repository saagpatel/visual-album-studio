from vas_studio import UxPlatformService


def test_ts014_accessibility_keyboard_focus_contrast(runtime):
    ux = UxPlatformService(runtime.db)
    report = ux.validate_accessibility(
        "guided_flow",
        {
            "focus_order": ["import_button", "preset_picker", "queue_export"],
            "has_focus_indicators": True,
            "reduced_motion_supported": True,
            "contrast_checks": [
                {"name": "primary_text", "ratio": 7.1},
                {"name": "status_badge", "ratio": 4.8},
            ],
        },
    )
    assert report["ok"]
    assert report["violations"] == []

    bad = ux.validate_accessibility(
        "bad_screen",
        {
            "focus_order": ["a", "a"],
            "has_focus_indicators": False,
            "reduced_motion_supported": False,
            "contrast_checks": [{"name": "muted", "ratio": 3.2}],
        },
    )
    assert not bad["ok"]
    assert any(v.startswith("focus_order_duplicate") for v in bad["violations"])
    assert any(v.startswith("contrast_low") for v in bad["violations"])
