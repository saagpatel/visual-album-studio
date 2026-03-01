from vas_studio import UxPlatformService


def test_tsv2_510_accessibility_tokens_cover_required_state_roles():
    service = UxPlatformService()
    tokens = service.get_tokens()
    roles = tokens["state_roles"]

    assert "loading" in roles
    assert "disabled" in roles
    assert "error" in roles
    assert "success" in roles


def test_tsv2_510_accessibility_validation_requires_focus_and_reduced_motion():
    service = UxPlatformService()
    report = service.validate_accessibility(
        "screen_publish",
        {
            "focus_order": ["provider", "title", "submit"],
            "has_focus_indicators": True,
            "reduced_motion_supported": True,
            "contrast_checks": [{"name": "body_text", "ratio": 7.0}],
        },
    )
    assert report["ok"] is True
    assert report["violations"] == []
