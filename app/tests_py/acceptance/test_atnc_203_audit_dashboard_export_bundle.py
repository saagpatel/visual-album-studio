from pathlib import Path

from vas_studio import AuditDashboardExportServiceV1


def test_atnc_203_audit_dashboard_export_bundle(runtime, test_root):
    now = 1_713_000_000
    project_id = "proj_atnc203"
    for idx in range(3):
        runtime.db.execute(
            "INSERT INTO connector_diagnostics(id, project_id, connector, severity, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (f"diag_atnc203_{idx}", project_id, "youtube", "error", '{"refresh_token":"secret"}', now),
        )
    runtime.db.commit()

    service = AuditDashboardExportServiceV1(runtime.db)
    out_dir = Path(test_root) / "out" / "audit_exports"
    result = service.export_bundle(project_id=project_id, output_dir=out_dir)

    assert result["ok"] is True
    summary_path = Path(result["export_path"]) / "dashboard_summary.json"
    assert summary_path.exists()

    summary = summary_path.read_text(encoding="utf-8")
    assert "[REDACTED]" in summary

    listed = service.list_exports(project_id=project_id)
    assert listed["ok"] is True
    assert len(listed["exports"]) == 1
