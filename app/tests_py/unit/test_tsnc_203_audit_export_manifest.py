from pathlib import Path

from vas_studio import AuditDashboardExportServiceV1


def test_tsnc_203_export_manifest_contains_files(runtime, test_root):
    service = AuditDashboardExportServiceV1(runtime.db)
    out_dir = Path(test_root) / "out" / "audit_exports"

    result = service.export_bundle(project_id="proj_tsnc203", output_dir=out_dir)

    assert result["ok"] is True
    assert result["manifest"]["project_id"] == "proj_tsnc203"
    assert len(result["manifest"]["files"]) >= 3


def test_tsnc_203_list_exports_empty_then_nonempty(runtime, test_root):
    service = AuditDashboardExportServiceV1(runtime.db)
    out_dir = Path(test_root) / "out" / "audit_exports"

    before = service.list_exports(project_id="proj_none")
    assert before["ok"] is True
    assert before["exports"] == []

    service.export_bundle(project_id="proj_none", output_dir=out_dir)
    after = service.list_exports(project_id="proj_none")
    assert len(after["exports"]) == 1
