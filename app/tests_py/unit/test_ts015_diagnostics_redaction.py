import json
from pathlib import Path

from vas_studio import ProductizationService


def test_ts015_diagnostics_redaction_and_schema(runtime, test_root: Path):
    logs_dir = test_root / "out" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "phase7.log"
    log_path.write_text(
        "\n".join(
            [
                "normal line",
                "Authorization: Bearer abc123",
                "refresh_token=def456",
            ]
        ),
        encoding="utf-8",
    )

    svc = ProductizationService(runtime.db, out_dir=test_root / "out")
    result = svc.export_diagnostics({"log_paths": [str(log_path)], "scope_id": "ts015"})
    assert result["ok"]
    diag = result["diagnostics"]
    assert diag["id"].startswith("diag_")
    assert diag["redaction_summary"]["lines_redacted"] >= 2

    payload = json.loads(Path(diag["output_path"]).read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["payload"]["redaction_summary"]["lines_redacted"] >= 2
    file_block = payload["payload"]["files"][0]
    assert "[REDACTED]" in file_block["content"]
