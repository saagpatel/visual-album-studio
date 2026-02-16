from vas_studio import UxPlatformService


def test_it012_accessibility_smoke_across_critical_flows(runtime):
    ux = UxPlatformService(runtime.db)
    screens = {
        "onboarding": {
            "focus_order": ["ffmpeg_check", "output_check", "continue_button"],
            "has_focus_indicators": True,
            "reduced_motion_supported": True,
            "contrast_checks": [{"name": "onboarding_text", "ratio": 7.0}],
        },
        "guided_workflow": {
            "focus_order": ["import", "preset", "provenance", "queue"],
            "has_focus_indicators": True,
            "reduced_motion_supported": True,
            "contrast_checks": [{"name": "guided_status", "ratio": 5.5}],
        },
        "command_center": {
            "focus_order": ["queue_filter", "job_list", "resume_button"],
            "has_focus_indicators": True,
            "reduced_motion_supported": True,
            "contrast_checks": [{"name": "job_error_badge", "ratio": 4.6}],
        },
    }

    for screen_id, screen in screens.items():
        report = ux.validate_accessibility(screen_id, screen)
        assert report["ok"], f"{screen_id} accessibility violations: {report['violations']}"
