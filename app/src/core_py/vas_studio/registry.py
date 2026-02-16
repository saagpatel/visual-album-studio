import json
from dataclasses import dataclass
from typing import Dict, Tuple

from .errors import VasError


@dataclass
class ParameterDef:
    param_id: str
    type_name: str
    min_value: float | None = None
    max_value: float | None = None


class ParameterRegistry:
    def __init__(self, db):
        self.db = db

    def register(self, mode_id: str, defs: list[ParameterDef], schema_version: int = 1) -> None:
        for d in defs:
            self.db.execute(
                """
                INSERT OR REPLACE INTO parameter_registry(
                  id, mode_id, type, default_json, range_json, description,
                  introduced_in_schema, deprecated_in_schema, extra_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, '{}')
                """,
                (
                    d.param_id,
                    mode_id,
                    d.type_name,
                    json.dumps(0),
                    json.dumps({"min": d.min_value, "max": d.max_value}),
                    "",
                    schema_version,
                ),
            )
        self.db.commit()

    def validate_overrides(self, mode_id: str, overrides: Dict[str, float]) -> Tuple[bool, str]:
        rows = self.db.execute("SELECT id, range_json FROM parameter_registry WHERE mode_id = ?", (mode_id,)).fetchall()
        ranges = {r["id"]: json.loads(r["range_json"]) for r in rows}

        for key, value in overrides.items():
            if key not in ranges:
                return False, f"unknown parameter: {key}"
            r = ranges[key]
            lo = r.get("min")
            hi = r.get("max")
            if lo is not None and value < lo:
                return False, f"{key} below minimum"
            if hi is not None and value > hi:
                return False, f"{key} above maximum"
        return True, "ok"

    def migrate_preset(self, preset_id: str, target_schema_version: int) -> str:
        row = self.db.execute("SELECT * FROM presets WHERE id = ?", (preset_id,)).fetchone()
        if not row:
            raise VasError("E_PRESET_NOT_FOUND", f"Preset not found: {preset_id}")

        new_id = f"{preset_id}_v{target_schema_version}"
        self.db.execute(
            """
            INSERT OR REPLACE INTO presets(
              id, mode_id, name, schema_version, mapping_id, seed, overrides_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id,
                row["mode_id"],
                row["name"],
                target_schema_version,
                row["mapping_id"],
                row["seed"],
                row["overrides_json"],
                row["created_at"],
                row["updated_at"],
            ),
        )
        self.db.commit()
        return new_id
