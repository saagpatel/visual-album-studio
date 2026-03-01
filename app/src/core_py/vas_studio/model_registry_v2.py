from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import VasError
from .ids import new_id


@dataclass
class ModelProvenanceRecordV1:
    schema_version: int
    source_url: str
    sha256: str
    license: str
    license_spdx: str
    recorded_at: int
    details: dict[str, Any]

    def to_json(self) -> str:
        return json.dumps(
            {
                "schema_version": self.schema_version,
                "source_url": self.source_url,
                "sha256": self.sha256,
                "license": self.license,
                "license_spdx": self.license_spdx,
                "recorded_at": self.recorded_at,
                "details": self.details,
            },
            sort_keys=True,
        )


class ModelRegistryServiceV2:
    def __init__(self, db, models_dir: Path):
        self.db = db
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._columns = self._load_columns()

    def _load_columns(self) -> set[str]:
        rows = self.db.execute("PRAGMA table_info(model_registry)").fetchall()
        return {str(row["name"]) for row in rows}

    def _has_column(self, name: str) -> bool:
        return name in self._columns

    def verify_checksum(self, src: Path, expected_sha256: str) -> dict[str, Any]:
        if not src.exists():
            return {"ok": False, "error": "E_MODEL_NOT_INSTALLED", "path": str(src)}
        digest = hashlib.sha256(src.read_bytes()).hexdigest()
        return {"ok": digest == expected_sha256, "actual_sha256": digest, "expected_sha256": expected_sha256}

    def enforce_license_policy(self, *, license_name: str, license_spdx: str = "") -> dict[str, Any]:
        if not license_name.strip():
            raise VasError("E_MODEL_LICENSE_UNKNOWN", "Model license is required")

        blocked = {"proprietary-unknown", "unknown", "unspecified"}
        if license_spdx.strip().lower() in blocked:
            raise VasError(
                "E_MODEL_LICENSE_UNKNOWN",
                "Model SPDX license is blocked by policy",
                details={"license_spdx": license_spdx},
            )
        return {"ok": True}

    def register_candidate(
        self,
        *,
        model_id: str,
        name: str,
        version: str,
        license_name: str,
        source_url: str,
        sha256: str,
        relpath: str,
        size_bytes: int,
        license_spdx: str = "",
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.enforce_license_policy(license_name=license_name, license_spdx=license_spdx)

        now = int(time.time())
        provenance = ModelProvenanceRecordV1(
            schema_version=1,
            source_url=source_url,
            sha256=sha256,
            license=license_name,
            license_spdx=license_spdx,
            recorded_at=now,
            details=details or {},
        )

        columns = [
            "id",
            "name",
            "version",
            "license",
            "source_url",
            "sha256",
            "relpath",
            "size_bytes",
            "installed_at",
        ]
        values: list[Any] = [model_id, name, version, license_name, source_url, sha256, relpath, size_bytes, now]

        if self._has_column("license_spdx"):
            columns.append("license_spdx")
            values.append(license_spdx)
        if self._has_column("provenance_json"):
            columns.append("provenance_json")
            values.append(provenance.to_json())
        if self._has_column("status"):
            columns.append("status")
            values.append("candidate")
        if self._has_column("updated_at"):
            columns.append("updated_at")
            values.append(now)

        placeholders = ", ".join(["?"] * len(columns))
        sql = f"INSERT OR REPLACE INTO model_registry({', '.join(columns)}) VALUES ({placeholders})"
        self.db.execute(sql, tuple(values))
        self.db.commit()
        return {"ok": True, "model_id": model_id, "status": "candidate"}

    def get_model(self, model_id: str) -> dict[str, Any] | None:
        row = self.db.execute("SELECT * FROM model_registry WHERE id = ?", (model_id,)).fetchone()
        if not row:
            return None
        model = dict(row)
        model.setdefault("license_spdx", "")
        model.setdefault("provenance_json", "{}")
        model.setdefault("status", "candidate")
        model.setdefault("replaced_by_model_id", None)
        model.setdefault("updated_at", int(model.get("installed_at", 0)))
        return model

    def promote_model(self, model_id: str, *, replaced_by_model_id: str | None = None) -> dict[str, Any]:
        if not self._has_column("status"):
            return {"ok": False, "error": "E_MODEL_REGISTRY_SCHEMA_UNSUPPORTED"}
        if not self.get_model(model_id):
            return {"ok": False, "error": "E_MODEL_NOT_INSTALLED", "model_id": model_id}

        now = int(time.time())
        if replaced_by_model_id:
            self.db.execute(
                "UPDATE model_registry SET status = 'deprecated', replaced_by_model_id = ?, updated_at = ? WHERE id = ?",
                (model_id, now, replaced_by_model_id),
            )
        self.db.execute("UPDATE model_registry SET status = 'active', updated_at = ? WHERE id = ?", (now, model_id))
        self.db.commit()
        return {"ok": True, "model_id": model_id, "status": "active"}

    def rollback_model(self, model_id: str) -> dict[str, Any]:
        if not self._has_column("status"):
            return {"ok": False, "error": "E_MODEL_REGISTRY_SCHEMA_UNSUPPORTED"}
        if not self.get_model(model_id):
            return {"ok": False, "error": "E_MODEL_NOT_INSTALLED", "model_id": model_id}

        now = int(time.time())
        self.db.execute(
            "UPDATE model_registry SET status = 'active', replaced_by_model_id = NULL, updated_at = ? WHERE id = ?",
            (now, model_id),
        )
        self.db.commit()
        return {"ok": True, "model_id": model_id, "status": "active"}

    def resolve_model_path(self, model_id: str) -> Path | None:
        model = self.get_model(model_id)
        if not model:
            return None
        relpath = str(model.get("relpath", "")).strip()
        if not relpath:
            return None
        path = self.models_dir / relpath
        if path.exists():
            return path
        return None

    def record_evaluation(
        self,
        *,
        model_id: str,
        fixture_id: str,
        quality_score: float,
        perf_fps: float,
        safety_score: float,
        notes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.get_model(model_id):
            return {"ok": False, "error": "E_MODEL_NOT_INSTALLED", "model_id": model_id}
        eval_id = new_id("model_eval")
        now = int(time.time())
        self.db.execute(
            """
            INSERT INTO model_eval_runs(id, model_id, fixture_id, quality_score, perf_fps, safety_score, notes_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                eval_id,
                model_id,
                fixture_id,
                float(quality_score),
                float(perf_fps),
                float(safety_score),
                json.dumps(notes or {}, sort_keys=True),
                now,
            ),
        )
        self.db.commit()
        return {"ok": True, "id": eval_id}
