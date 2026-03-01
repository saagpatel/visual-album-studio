from pathlib import Path

from vas_studio import AuditDashboardExportServiceV1


def test_itnc_203_export_generates_files_and_db_row(runtime, test_root):
    now = 1_712_000_000
    runtime.db.execute(
        "INSERT INTO connector_diagnostics(id, connector, severity, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
        ("diag_itnc203", "x", "error", '{"access_token":"abc"}', now),
    )
    runtime.db.commit()

    service = AuditDashboardExportServiceV1(runtime.db)
    out_dir = Path(test_root) / "out" / "audit_exports"
    result = service.export_bundle(project_id="proj_itnc203", output_dir=out_dir, include_raw=True)

    assert result["ok"] is True
    manifest = result["manifest"]
    assert any(path.endswith("manifest.json") for path in manifest["files"])

    row = runtime.db.execute("SELECT COUNT(*) AS c FROM audit_dashboard_exports WHERE project_id = 'proj_itnc203'").fetchone()
    assert int(row["c"]) == 1
