from pathlib import Path

from vas_studio import AuditDashboardExportServiceV1


def test_itnc_203_export_generates_files_and_db_row(runtime, test_root):
    now = 1_712_000_000
    project_id = "proj_itnc203"
    runtime.db.execute(
        "INSERT INTO connector_diagnostics(id, project_id, connector, severity, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("diag_itnc203", project_id, "x", "error", '{"access_token":"abc"}', now),
    )
    runtime.db.execute(
        "INSERT INTO connector_diagnostics(id, project_id, connector, severity, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("diag_itnc203_other", "proj_other", "youtube", "error", '{"access_token":"zzz"}', now),
    )
    runtime.db.commit()

    service = AuditDashboardExportServiceV1(runtime.db)
    out_dir = Path(test_root) / "out" / "audit_exports"
    result = service.export_bundle(project_id=project_id, output_dir=out_dir, include_raw=True)

    assert result["ok"] is True
    manifest = result["manifest"]
    assert any(path.endswith("manifest.json") for path in manifest["files"])

    row = runtime.db.execute("SELECT COUNT(*) AS c FROM audit_dashboard_exports WHERE project_id = ?", (project_id,)).fetchone()
    assert int(row["c"]) == 1

    raw_path = Path(result["export_path"]) / "dashboard_raw.json"
    raw = raw_path.read_text(encoding="utf-8")
    assert "[REDACTED]" in raw
    assert "access_token" in raw
    assert '"abc"' not in raw

    summary_path = Path(result["export_path"]) / "dashboard_summary.json"
    summary = summary_path.read_text(encoding="utf-8")
    assert "proj_other" not in summary
