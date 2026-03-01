from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .ids import new_id


@dataclass
class PresetSignatureV1:
    algorithm: str
    digest: str
    signed_by: str
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": int(self.schema_version),
            "algorithm": self.algorithm,
            "digest": self.digest,
            "signed_by": self.signed_by,
        }


@dataclass
class StylePresetBundleV1:
    preset_id: str
    source_project_id: str
    owner_user_id: str
    mode: str
    parameters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    sharing: dict[str, Any] = field(default_factory=dict)
    signature: PresetSignatureV1 | None = None
    schema_version: int = 1

    def unsigned_payload(self) -> dict[str, Any]:
        return {
            "schema_version": int(self.schema_version),
            "preset_id": self.preset_id,
            "source_project_id": self.source_project_id,
            "owner_user_id": self.owner_user_id,
            "mode": self.mode,
            "parameters": dict(self.parameters),
            "metadata": dict(self.metadata),
            "sharing": dict(self.sharing),
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.unsigned_payload()
        payload["signature"] = self.signature.to_dict() if self.signature else {}
        return payload


@dataclass
class PresetCompatibilityReportV1:
    ok: bool
    issues: list[str] = field(default_factory=list)
    normalized_parameters: dict[str, Any] = field(default_factory=dict)
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": int(self.schema_version),
            "ok": bool(self.ok),
            "issues": list(self.issues),
            "normalized_parameters": dict(self.normalized_parameters),
        }


class PresetExchangeServiceV1:
    def __init__(self, db, *, signing_secret: str = "vas-preset-signing-v1", signer: str = "vas-studio"):
        self.db = db
        self.signing_secret = str(signing_secret)
        self.signer = str(signer)

    @staticmethod
    def _canonical(payload: dict[str, Any]) -> str:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    def _sign_payload(self, payload: dict[str, Any]) -> PresetSignatureV1:
        digest = hashlib.sha256((self.signing_secret + self._canonical(payload)).encode("utf-8")).hexdigest()
        return PresetSignatureV1(algorithm="sha256", digest=digest, signed_by=self.signer)

    def build_bundle(
        self,
        *,
        preset_id: str,
        source_project_id: str,
        owner_user_id: str,
        mode: str,
        parameters: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        allowed_user_ids: list[str] | None = None,
        schema_version: int = 1,
    ) -> dict[str, Any]:
        bundle = StylePresetBundleV1(
            preset_id=preset_id,
            source_project_id=source_project_id,
            owner_user_id=owner_user_id,
            mode=mode,
            parameters=dict(parameters),
            metadata=dict(metadata or {}),
            sharing={"allowed_user_ids": list(allowed_user_ids or [owner_user_id])},
            schema_version=int(schema_version),
        )
        bundle.signature = self._sign_payload(bundle.unsigned_payload())
        return {"ok": True, "bundle": bundle.to_dict()}

    def compatibility_report(self, bundle_payload: dict[str, Any], *, supported_schema_version: int = 1) -> dict[str, Any]:
        issues: list[str] = []
        schema_version = int(bundle_payload.get("schema_version", 0))
        if schema_version != int(supported_schema_version):
            issues.append("E_PRESET_SCHEMA_INCOMPATIBLE")
        mode = str(bundle_payload.get("mode", "")).strip()
        if not mode:
            issues.append("E_PRESET_MODE_REQUIRED")
        parameters = bundle_payload.get("parameters", {})
        if not isinstance(parameters, dict) or len(parameters) == 0:
            issues.append("E_PRESET_PARAMETERS_REQUIRED")

        normalized = {str(k): v for k, v in dict(parameters or {}).items()}
        report = PresetCompatibilityReportV1(ok=len(issues) == 0, issues=issues, normalized_parameters=normalized)
        return report.to_dict()

    def verify_signature(self, bundle_payload: dict[str, Any]) -> dict[str, Any]:
        signature = dict(bundle_payload.get("signature", {}))
        provided = str(signature.get("digest", ""))
        unsigned = dict(bundle_payload)
        unsigned.pop("signature", None)
        expected = self._sign_payload(unsigned)
        if provided != expected.digest:
            return {"ok": False, "error_code": "E_PRESET_SIGNATURE_INVALID", "expected": expected.digest}
        return {"ok": True}

    @staticmethod
    def write_bundle(bundle_payload: dict[str, Any], output_path: Path | str) -> dict[str, Any]:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(bundle_payload, indent=2, sort_keys=True), encoding="utf-8")
        return {"ok": True, "path": str(output)}

    @staticmethod
    def read_bundle(input_path: Path | str) -> dict[str, Any]:
        payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
        return {"ok": True, "bundle": payload}

    def import_bundle(
        self,
        *,
        bundle_payload: dict[str, Any],
        target_project_id: str,
        actor_user_id: str,
        can_edit_target: bool,
    ) -> dict[str, Any]:
        report = self.compatibility_report(bundle_payload)
        if not report["ok"]:
            return self._record_event(
                bundle_payload=bundle_payload,
                target_project_id=target_project_id,
                actor_user_id=actor_user_id,
                status="failed",
                error_code=report["issues"][0],
            )

        verified = self.verify_signature(bundle_payload)
        if not verified["ok"]:
            return self._record_event(
                bundle_payload=bundle_payload,
                target_project_id=target_project_id,
                actor_user_id=actor_user_id,
                status="failed",
                error_code=str(verified["error_code"]),
            )

        if not bool(can_edit_target):
            return self._record_event(
                bundle_payload=bundle_payload,
                target_project_id=target_project_id,
                actor_user_id=actor_user_id,
                status="failed",
                error_code="E_PRESET_PERMISSION_DENIED",
            )

        sharing = dict(bundle_payload.get("sharing", {}))
        allowed = set(str(v) for v in list(sharing.get("allowed_user_ids", [])))
        owner = str(bundle_payload.get("owner_user_id", ""))
        if actor_user_id not in allowed and actor_user_id != owner:
            return self._record_event(
                bundle_payload=bundle_payload,
                target_project_id=target_project_id,
                actor_user_id=actor_user_id,
                status="failed",
                error_code="E_PRESET_PERMISSION_DENIED",
            )

        return self._record_event(
            bundle_payload=bundle_payload,
            target_project_id=target_project_id,
            actor_user_id=actor_user_id,
            status="imported",
            error_code="",
        )

    def _record_event(
        self,
        *,
        bundle_payload: dict[str, Any],
        target_project_id: str,
        actor_user_id: str,
        status: str,
        error_code: str,
    ) -> dict[str, Any]:
        event_id = new_id("preset_exchange")
        now = int(time.time())
        source_project = str(bundle_payload.get("source_project_id", ""))
        preset_id = str(bundle_payload.get("preset_id", ""))
        self.db.execute(
            """
            INSERT INTO preset_exchange_events(id, source_project_id, target_project_id, preset_id, actor_user_id, status, error_code, bundle_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                source_project,
                target_project_id,
                preset_id,
                actor_user_id,
                status,
                error_code,
                json.dumps(bundle_payload, sort_keys=True),
                now,
            ),
        )
        self.db.commit()
        return {
            "ok": status == "imported",
            "event_id": event_id,
            "status": status,
            "error_code": error_code,
            "target_project_id": target_project_id,
            "preset_id": preset_id,
        }
