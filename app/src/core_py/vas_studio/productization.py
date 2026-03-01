from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DiagnosticsBundleInfo:
    bundle_id: str
    output_path: Path
    redaction_summary: dict
    created_at: int

    def to_dict(self) -> dict:
        return {
            "id": self.bundle_id,
            "output_path": str(self.output_path),
            "redaction_summary": dict(self.redaction_summary),
            "created_at": self.created_at,
        }


@dataclass
class PackageManifest:
    profile_id: str
    manifest_path: Path
    content_sha256: str
    created_at: int

    def to_dict(self) -> dict:
        return {
            "profile_id": self.profile_id,
            "manifest_path": str(self.manifest_path),
            "content_sha256": self.content_sha256,
            "created_at": self.created_at,
        }


@dataclass
class SupportReport:
    report_id: str
    severity: str
    summary: str
    details: dict

    def to_dict(self) -> dict:
        return {
            "id": self.report_id,
            "severity": self.severity,
            "summary": self.summary,
            "details": dict(self.details),
        }


class ProductizationService:
    def __init__(self, db=None, out_dir: Path | str = "out"):
        self.db = db
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.secret_patterns = [
            "VAS_YT_CLIENT_SECRET",
            "VAS_YT_REFRESH_TOKEN",
            "Authorization: Bearer",
            "refresh_token",
            "access_token",
            "client_secret",
        ]

    def run_packaging_dry_run(self, profile_id: str, channel: str = "stable") -> dict:
        if channel not in {"stable", "beta", "dev"}:
            return {"ok": False, "error": "E_CHANNEL_INVALID", "channel": channel}

        now = int(time.time())
        manifest_dir = self.out_dir / "productization" / "packaging" / profile_id
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "manifest.json"
        artifacts = [
            {"name": "app_bundle_stub", "path": "app/"},
            {"name": "native_keyring_stub", "path": "native/vas_keyring/"},
            {"name": "worker_package_stub", "path": "worker/"},
        ]
        payload = {
            "schema_version": 1,
            "profile_id": profile_id,
            "channel": channel,
            "version": "phase7-dry-run",
            "toolchain": {
                "ffmpeg": "managed",
                "godot": "4.4.x",
                "python": "3.11+",
                "rust": "stable",
            },
            "artifacts": sorted(artifacts, key=lambda item: (item["name"], item["path"])),
        }
        content = json.dumps(payload, sort_keys=True, indent=2)
        manifest_path.write_text(content, encoding="utf-8")
        sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

        if self.db:
            self.db.execute(
                """
                INSERT OR REPLACE INTO release_profiles(id, channel, manifest_json, created_at, updated_at)
                VALUES (?, ?, ?, COALESCE((SELECT created_at FROM release_profiles WHERE id = ?), ?), ?)
                """,
                (profile_id, channel, content, profile_id, now, now),
            )
            self.db.commit()

        return {
            "ok": True,
            "manifest": payload,
            "package": PackageManifest(profile_id, manifest_path, sha, now).to_dict(),
        }

    def sign_release_manifest(self, profile_id: str, channel: str = "stable", signer_id: str = "vas-local") -> dict:
        package_result = self.run_packaging_dry_run(profile_id, channel=channel)
        if not package_result.get("ok"):
            return {"ok": False, "error": "E_PACKAGING_FAILED", "details": package_result}

        key = self._signing_key()
        if not key:
            return {"ok": False, "error": "E_SIGNING_KEY_MISSING"}

        manifest_path = Path(package_result["package"]["manifest_path"])
        manifest_content = manifest_path.read_text(encoding="utf-8")
        manifest_sha = hashlib.sha256(manifest_content.encode("utf-8")).hexdigest()
        signature = hmac.new(key.encode("utf-8"), manifest_content.encode("utf-8"), hashlib.sha256).hexdigest()
        now = int(time.time())

        signature_payload = {
            "schema_version": 1,
            "profile_id": profile_id,
            "channel": channel,
            "manifest_path": str(manifest_path),
            "manifest_sha256": manifest_sha,
            "signature": {
                "algorithm": "HMAC-SHA256",
                "signer_id": signer_id,
                "value": signature,
            },
            "created_at": now,
        }
        signature_path = manifest_path.with_name("manifest.sig.json")
        signature_path.write_text(json.dumps(signature_payload, sort_keys=True, indent=2), encoding="utf-8")

        return {
            "ok": True,
            "signature_path": str(signature_path),
            "signature": signature_payload,
            "package": package_result["package"],
        }

    def verify_release_manifest_signature(self, profile_id: str, channel: str = "stable") -> dict:
        key = self._signing_key()
        if not key:
            return {"ok": False, "error": "E_SIGNING_KEY_MISSING"}

        manifest_path = self.out_dir / "productization" / "packaging" / profile_id / "manifest.json"
        if not manifest_path.exists():
            package_result = self.run_packaging_dry_run(profile_id, channel=channel)
            if not package_result.get("ok"):
                return {"ok": False, "error": "E_PACKAGING_FAILED", "details": package_result}
            manifest_path = Path(package_result["package"]["manifest_path"])

        signature_path = manifest_path.with_name("manifest.sig.json")
        if not signature_path.exists():
            return {"ok": False, "error": "E_SIGNATURE_NOT_FOUND", "path": str(signature_path)}

        manifest_content = manifest_path.read_text(encoding="utf-8")
        payload = json.loads(signature_path.read_text(encoding="utf-8"))
        expected = hmac.new(key.encode("utf-8"), manifest_content.encode("utf-8"), hashlib.sha256).hexdigest()
        actual = str(payload.get("signature", {}).get("value", ""))

        return {
            "ok": True,
            "valid": expected == actual,
            "expected": expected,
            "actual": actual,
            "signature_path": str(signature_path),
        }

    def export_diagnostics(self, scope: dict) -> dict:
        now = int(time.time())
        safe_scope = self._redact_value(dict(scope))
        log_paths = [Path(p) for p in safe_scope.get("log_paths", [])]
        if not log_paths:
            logs_dir = self.out_dir / "logs"
            if logs_dir.exists():
                log_paths = sorted(path for path in logs_dir.iterdir() if path.suffix == ".log")

        redaction_summary = {"lines_scanned": 0, "lines_redacted": 0, "matches": {}}
        files = []
        for path in log_paths:
            if not path.exists():
                continue
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[:200]
            sanitized = []
            for line in lines:
                redaction_summary["lines_scanned"] += 1
                sanitized.append(self._redact_line(line, redaction_summary))
            files.append({"path": str(path), "line_count": len(sanitized), "content": "\n".join(sanitized)})

        bundle = {
            "id": f"diag_{uuid.uuid4().hex}",
            "schema_version": 1,
            "scope": dict(safe_scope),
            "payload": {
                "files": files,
                "redaction_summary": redaction_summary,
                "toolchain": {"godot": "4.4.x", "ffmpeg": "managed"},
                "generated_at": now,
            },
            "created_at": now,
        }
        output_dir = self.out_dir / "diagnostics"
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / f"{bundle['id']}.json"
        out_path.write_text(json.dumps(bundle, sort_keys=True, indent=2), encoding="utf-8")

        if self.db:
            self.db.execute(
                """
                INSERT OR REPLACE INTO diagnostics_exports(id, scope_json, output_relpath, redaction_summary_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    bundle["id"],
                    json.dumps(safe_scope, sort_keys=True),
                    str(out_path),
                    json.dumps(redaction_summary, sort_keys=True),
                    now,
                ),
            )
            self.db.commit()

        return {
            "ok": True,
            "diagnostics": DiagnosticsBundleInfo(bundle["id"], out_path, redaction_summary, now).to_dict(),
            "bundle": bundle,
        }

    def get_release_channels(self) -> list[dict]:
        selected = "stable"
        if self.db:
            row = self.db.execute("SELECT value_json FROM app_kv WHERE key = 'release_channel'").fetchone()
            if row and row["value_json"]:
                try:
                    selected = json.loads(row["value_json"]).get("channel", "stable")
                except json.JSONDecodeError:
                    selected = "stable"
        return [{"id": c, "selected": c == selected} for c in ["stable", "beta", "dev"]]

    def set_release_channel(self, channel_id: str) -> dict:
        if channel_id not in {"stable", "beta", "dev"}:
            return {"ok": False, "error": "E_CHANNEL_INVALID", "channel": channel_id}
        if self.db:
            self.db.execute(
                "INSERT OR REPLACE INTO app_kv(key, value_json, updated_at) VALUES ('release_channel', ?, ?)",
                (json.dumps({"channel": channel_id}), int(time.time())),
            )
            self.db.commit()
        return {"ok": True, "channel": channel_id}

    def generate_support_report(self, context: dict) -> dict:
        safe_context = self._redact_value(dict(context))
        code = str(safe_context.get("error_code", "E_UNKNOWN"))
        runbook = self._runbook_for_error(code)
        severity = self._severity_for_error(code)
        report = SupportReport(
            report_id=f"support_{uuid.uuid4().hex}",
            severity=severity,
            summary=f"Troubleshooting guidance generated for {code}",
            details={"context": dict(safe_context), "runbook": runbook, "classification": severity},
        )
        if self.db:
            self.db.execute(
                "INSERT OR REPLACE INTO support_reports(id, context_json, report_json, created_at) VALUES (?, ?, ?, ?)",
                (
                    report.report_id,
                    json.dumps(safe_context, sort_keys=True),
                    json.dumps(report.details, sort_keys=True),
                    int(time.time()),
                ),
            )
            self.db.commit()
        return report.to_dict()

    def _redact_line(self, line: str, summary: dict) -> str:
        lowered = line.lower()
        for pattern in self.secret_patterns:
            if pattern.lower() in lowered:
                summary["lines_redacted"] += 1
                summary["matches"][pattern] = int(summary["matches"].get(pattern, 0)) + 1
                return "[REDACTED]"
        return line

    def _redact_value(self, value):
        if isinstance(value, dict):
            redacted = {}
            for key, item in value.items():
                key_str = str(key)
                if self._key_looks_secret(key_str):
                    redacted[key_str] = "[REDACTED]"
                else:
                    redacted[key_str] = self._redact_value(item)
            return redacted
        if isinstance(value, list):
            return [self._redact_value(item) for item in value]
        if isinstance(value, str):
            summary = {"lines_redacted": 0, "matches": {}}
            return self._redact_line(value, summary)
        return value

    @staticmethod
    def _key_looks_secret(key_name: str) -> bool:
        lowered = key_name.lower()
        for marker in ["refresh_token", "access_token", "client_secret", "authorization", "api_key", "password", "secret"]:
            if marker in lowered:
                return True
        return False

    @staticmethod
    def _runbook_for_error(code: str) -> str:
        if code.startswith("E_FFMPEG") or code == "E_DISK_FULL":
            return "disk-full-or-ffmpeg"
        if code.startswith("E_KEYRING"):
            return "keyring-unavailable"
        if code.startswith("E_YT_") or code == "E_CHANNEL_INVALID":
            return "youtube-auth-or-quota"
        if code.startswith("E_LICENSE"):
            return "provenance-remediation"
        return "general-troubleshooting"

    @staticmethod
    def _severity_for_error(code: str) -> str:
        if code == "E_DISK_FULL" or code.startswith("E_FFMPEG"):
            return "high"
        if code.startswith("E_YT_") or code.startswith("E_KEYRING"):
            return "medium"
        return "info"

    @staticmethod
    def _signing_key() -> str:
        return os.environ.get("VAS_RELEASE_SIGNING_KEY", "").strip()
