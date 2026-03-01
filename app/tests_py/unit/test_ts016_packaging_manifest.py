import hashlib
import json
import time
from pathlib import Path

from vas_studio import ProductizationService


def _stable_hash(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    normalized = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def test_ts016_packaging_manifest_determinism(runtime, test_root: Path):
    svc = ProductizationService(runtime.db, out_dir=test_root / "out")
    a = svc.run_packaging_dry_run("profile_ts016", channel="beta")
    time.sleep(2)
    b = svc.run_packaging_dry_run("profile_ts016", channel="beta")
    assert a["ok"] and b["ok"]

    path = Path(a["package"]["manifest_path"])
    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 2
    assert payload["channel"] == "beta"
    assert payload["manifest_type"] == "release_manifest_v2"
    assert payload["provenance"]["signature_algorithm"] == "HMAC-SHA256"
    assert payload["artifacts"] == sorted(payload["artifacts"], key=lambda item: (item["name"], item["path"]))
    assert "created_at" not in payload

    hash_a = _stable_hash(Path(a["package"]["manifest_path"]))
    hash_b = _stable_hash(Path(b["package"]["manifest_path"]))
    assert hash_a == hash_b
    assert a["package"]["content_sha256"] == b["package"]["content_sha256"]
