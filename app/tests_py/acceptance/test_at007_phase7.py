import json
from pathlib import Path

from vas_studio import ProductizationService, UxPlatformService


def test_at007_phase7_ux_and_productization(runtime, test_root: Path):
    ux = UxPlatformService(runtime.db)
    productization = ProductizationService(runtime.db, out_dir=test_root / "out")

    # Onboarding/readiness baseline
    readiness = ux.readiness_report(test_root / "out" / "phase7_onboarding")
    assert "checks" in readiness
    assert readiness["checks"]["output_writable"]

    # Guided flow to queue-ready state
    flow = ux.guided_workflow_status(
        {
            "assets_imported": True,
            "preset_selected": True,
            "provenance_complete": True,
            "export_queued": False,
        }
    )
    assert flow["next_step"] == "queue_export"
    assert flow["can_queue_export"]

    # Command center recoverability
    center = ux.build_export_command_center(
        [{"id": "job_a", "status": "failed"}, {"id": "job_b", "status": "running"}]
    )
    assert len(center["recovery_actions"]) == 1
    assert "resume" in center["recovery_actions"][0]["actions"]

    # Accessibility critical path
    accessibility = ux.validate_accessibility(
        "phase7_acceptance",
        {
            "focus_order": ["onboard", "guided", "command_center", "diagnostics"],
            "has_focus_indicators": True,
            "reduced_motion_supported": True,
            "contrast_checks": [{"name": "phase7_primary", "ratio": 6.2}],
        },
    )
    assert accessibility["ok"]

    # Diagnostics redaction
    logs_dir = test_root / "out" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    test_log = logs_dir / "phase7_acceptance.log"
    test_log.write_text("ok\nrefresh_token=secret\n", encoding="utf-8")
    diag = productization.export_diagnostics({"log_paths": [str(test_log)], "scope_id": "at007"})
    assert diag["ok"]
    diag_payload = json.loads(Path(diag["diagnostics"]["output_path"]).read_text(encoding="utf-8"))
    assert diag_payload["payload"]["redaction_summary"]["lines_redacted"] >= 1

    # Packaging determinism
    pack_a = productization.run_packaging_dry_run("phase7_profile", channel="stable")
    pack_b = productization.run_packaging_dry_run("phase7_profile", channel="stable")
    assert pack_a["ok"] and pack_b["ok"]
    manifest_a = json.loads(Path(pack_a["package"]["manifest_path"]).read_text(encoding="utf-8"))
    manifest_b = json.loads(Path(pack_b["package"]["manifest_path"]).read_text(encoding="utf-8"))
    assert manifest_a["artifacts"] == manifest_b["artifacts"]
