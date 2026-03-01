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


@dataclass
class HardwareProfileV1:
    cpu_cores: int
    ram_gb: float
    gpu_vendor: str = ""
    gpu_tier: str = "integrated"
    vram_gb: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "cpu_cores": int(self.cpu_cores),
            "ram_gb": float(self.ram_gb),
            "gpu_vendor": self.gpu_vendor,
            "gpu_tier": self.gpu_tier,
            "vram_gb": float(self.vram_gb),
        }


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

    def _has_table(self, name: str) -> bool:
        row = self.db.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (name,),
        ).fetchone()
        return row is not None

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

    def record_hardware_benchmark(
        self,
        *,
        model_id: str,
        profile_class: str,
        avg_fps: float,
        p95_latency_ms: float,
        memory_mb: float,
        success_rate: float,
        notes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self._has_table("model_hw_benchmarks"):
            return {"ok": False, "error": "E_MODEL_BENCHMARK_SCHEMA_UNSUPPORTED"}
        if not self.get_model(model_id):
            return {"ok": False, "error": "E_MODEL_NOT_INSTALLED", "model_id": model_id}
        if profile_class not in {"low", "mid", "high"}:
            return {"ok": False, "error": "E_PROFILE_CLASS_INVALID", "profile_class": profile_class}

        benchmark_id = new_id("model_bench")
        now = int(time.time())
        self.db.execute(
            """
            INSERT INTO model_hw_benchmarks(
              id, model_id, profile_class, avg_fps, p95_latency_ms, memory_mb, success_rate, notes_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                benchmark_id,
                model_id,
                profile_class,
                float(avg_fps),
                float(p95_latency_ms),
                float(memory_mb),
                float(success_rate),
                json.dumps(notes or {}, sort_keys=True),
                now,
            ),
        )
        self.db.commit()
        return {"ok": True, "id": benchmark_id}

    @staticmethod
    def score_candidate(*, quality_score: float, perf_fps: float, safety_score: float) -> float:
        quality = max(0.0, min(1.0, float(quality_score)))
        safety = max(0.0, min(1.0, float(safety_score)))
        perf = max(0.0, float(perf_fps))
        # Weighted toward safety/reproducibility, then quality, with bounded perf contribution.
        perf_component = min(perf / 120.0, 1.0)
        return round((safety * 0.45) + (quality * 0.4) + (perf_component * 0.15), 6)

    @staticmethod
    def classify_hardware_profile(profile: HardwareProfileV1) -> str:
        if profile.ram_gb < 12 or profile.cpu_cores < 6 or profile.vram_gb < 2:
            return "low"
        if profile.ram_gb >= 24 and profile.cpu_cores >= 8 and profile.vram_gb >= 6:
            return "high"
        return "mid"

    @staticmethod
    def _parse_details(model: dict[str, Any]) -> dict[str, Any]:
        details = {}
        provenance_raw = str(model.get("provenance_json", "{}"))
        try:
            provenance = json.loads(provenance_raw)
            details = dict(provenance.get("details", {}))
        except (json.JSONDecodeError, TypeError, ValueError):
            details = {}
        return details

    @staticmethod
    def _is_compatible(details: dict[str, Any], profile: HardwareProfileV1) -> bool:
        min_ram = float(details.get("min_ram_gb", 0.0))
        min_vram = float(details.get("min_vram_gb", 0.0))
        min_cpu = int(details.get("min_cpu_cores", 0))
        return profile.ram_gb >= min_ram and profile.vram_gb >= min_vram and profile.cpu_cores >= min_cpu

    def _benchmark_summary(self, *, model_id: str, profile_class: str) -> dict[str, float] | None:
        if not self._has_table("model_hw_benchmarks"):
            return None
        row = self.db.execute(
            """
            SELECT
              AVG(avg_fps) AS avg_fps,
              AVG(p95_latency_ms) AS p95_latency_ms,
              AVG(memory_mb) AS memory_mb,
              AVG(success_rate) AS success_rate
            FROM model_hw_benchmarks
            WHERE model_id = ? AND profile_class = ?
            """,
            (model_id, profile_class),
        ).fetchone()
        if row is None or row["avg_fps"] is None:
            return None
        return {
            "avg_fps": float(row["avg_fps"]),
            "p95_latency_ms": float(row["p95_latency_ms"]),
            "memory_mb": float(row["memory_mb"]),
            "success_rate": float(row["success_rate"]),
        }

    def record_selection_event(
        self,
        *,
        model_family: str,
        selected_model_id: str | None,
        profile_class: str,
        hardware_profile: HardwareProfileV1,
        candidates: list[dict[str, Any]],
        outcome: str,
        reason: str = "",
    ) -> dict[str, Any]:
        if not self._has_table("model_selection_events"):
            return {"ok": False, "error": "E_MODEL_SELECTION_SCHEMA_UNSUPPORTED"}
        if profile_class not in {"low", "mid", "high"}:
            return {"ok": False, "error": "E_PROFILE_CLASS_INVALID", "profile_class": profile_class}
        if outcome not in {"selected", "fallback"}:
            return {"ok": False, "error": "E_SELECTION_OUTCOME_INVALID", "outcome": outcome}

        event_id = new_id("model_pick")
        now = int(time.time())
        self.db.execute(
            """
            INSERT INTO model_selection_events(
              id, model_family, selected_model_id, profile_class, hardware_json, candidates_json, outcome, reason, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                model_family,
                selected_model_id,
                profile_class,
                json.dumps(hardware_profile.to_dict(), sort_keys=True),
                json.dumps(candidates, sort_keys=True),
                outcome,
                reason,
                now,
            ),
        )
        self.db.commit()
        return {"ok": True, "id": event_id}

    def recommend_model_for_hardware(
        self,
        *,
        model_family: str,
        hardware_profile: HardwareProfileV1,
        min_safety_score: float = 0.9,
    ) -> dict[str, Any]:
        if not self._has_column("status"):
            return {"ok": False, "error": "E_MODEL_REGISTRY_SCHEMA_UNSUPPORTED"}

        rows = self.db.execute("SELECT * FROM model_registry WHERE status = 'active'").fetchall()
        profile_class = self.classify_hardware_profile(hardware_profile)
        candidates: list[dict[str, Any]] = []
        for row in rows:
            model = dict(row)
            details = self._parse_details(model)
            family = str(details.get("family", "")).strip()
            if model_family and family and family != model_family:
                continue
            model_path = self.resolve_model_path(str(model["id"]))

            eval_row = self.db.execute(
                """
                SELECT
                  AVG(quality_score) AS quality,
                  AVG(perf_fps) AS perf,
                  AVG(safety_score) AS safety
                FROM model_eval_runs
                WHERE model_id = ?
                """,
                (model["id"],),
            ).fetchone()
            quality = float(eval_row["quality"] or 0.0)
            perf = float(eval_row["perf"] or 0.0)
            safety = float(eval_row["safety"] or 0.0)
            compat = self._is_compatible(details, hardware_profile) and model_path is not None
            bench = self._benchmark_summary(model_id=model["id"], profile_class=profile_class)
            bench_perf = perf if bench is None else float(bench["avg_fps"])
            bench_latency = 0.0 if bench is None else float(bench["p95_latency_ms"])
            bench_success = 1.0 if bench is None else float(bench["success_rate"])

            performance_floor = 24.0 if profile_class == "low" else 18.0
            if bench_perf < performance_floor:
                compat = False
            if safety < min_safety_score:
                compat = False
            if bench_success < 0.9:
                compat = False

            base_score = self.score_candidate(quality_score=quality, perf_fps=bench_perf, safety_score=safety)
            candidate = {
                "model_id": model["id"],
                "family": family,
                "compatible": compat,
                "quality_score": quality,
                "perf_fps": bench_perf,
                "safety_score": safety,
                "success_rate": bench_success,
                "p95_latency_ms": bench_latency,
                "base_score": base_score,
                "details": details,
                "installed": model_path is not None,
            }
            if compat:
                bonus = 0.0
                tier = str(details.get("quality_tier", ""))
                if profile_class == "high" and tier == "high":
                    bonus += 0.08
                if profile_class == "low" and bench_perf >= 40.0:
                    bonus += 0.05
                latency_penalty = 0.0
                if bench_latency > 0:
                    latency_penalty = min(max((bench_latency - 45.0) / 200.0, 0.0), 0.2)
                reliability_bonus = min(max((bench_success - 0.9) * 0.3, 0.0), 0.05)
                candidate["rank_score"] = round(base_score + bonus + reliability_bonus - latency_penalty, 6)
            else:
                candidate["rank_score"] = 0.0
            candidates.append(candidate)

        compatible = [item for item in candidates if item["compatible"]]
        compatible.sort(key=lambda item: (item["rank_score"], item["perf_fps"], item["quality_score"]), reverse=True)
        if not compatible:
            return {
                "ok": False,
                "error": "E_MODEL_NO_COMPATIBLE",
                "model_family": model_family,
                "profile_class": profile_class,
                "hardware_profile": hardware_profile.to_dict(),
                "candidates": candidates,
            }

        best = compatible[0]
        return {
            "ok": True,
            "model_id": best["model_id"],
            "model_family": model_family,
            "profile_class": profile_class,
            "hardware_profile": hardware_profile.to_dict(),
            "candidates": compatible,
        }
