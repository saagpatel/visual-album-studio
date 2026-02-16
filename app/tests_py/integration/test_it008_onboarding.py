from pathlib import Path

from vas_studio import UxPlatformService


def test_it008_first_run_onboarding_clean_environment(runtime, test_root: Path):
    ux = UxPlatformService(runtime.db)
    out_dir = test_root / "out" / "onboarding"
    report = ux.readiness_report(out_dir)

    assert "checks" in report
    assert "ffmpeg_available" in report["checks"]
    assert report["checks"]["output_writable"]
    assert "issues" in report
