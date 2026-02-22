from __future__ import annotations

import json
import shutil
import subprocess  # nosec B404
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class UxTokenSet:
    spacing_scale: list[int] = field(default_factory=lambda: [4, 8, 12, 16, 24, 32])
    typography_scale: dict = field(
        default_factory=lambda: {"xs": 12, "sm": 14, "md": 16, "lg": 20, "xl": 24}
    )
    color_roles: dict = field(
        default_factory=lambda: {
            "background": "#121212",
            "surface": "#1f1f1f",
            "text": "#f5f5f5",
            "muted_text": "#c0c0c0",
            "accent": "#2f7ed8",
            "danger": "#c94848",
        }
    )
    state_roles: dict = field(
        default_factory=lambda: {
            "loading": "spinner",
            "disabled": "opacity_50",
            "error": "inline_banner",
            "warning": "inline_banner",
            "success": "toast",
        }
    )

    def to_dict(self) -> dict:
        return {
            "spacing_scale": list(self.spacing_scale),
            "typography_scale": dict(self.typography_scale),
            "color_roles": dict(self.color_roles),
            "state_roles": dict(self.state_roles),
        }


@dataclass
class AccessibilityReport:
    screen_id: str
    ok: bool
    violations: list[str]
    checks: dict

    def to_dict(self) -> dict:
        return {
            "screen_id": self.screen_id,
            "ok": self.ok,
            "violations": list(self.violations),
            "checks": dict(self.checks),
        }


@dataclass
class CommandResult:
    command_id: str
    ok: bool
    message: str
    data: dict

    def to_dict(self) -> dict:
        return {
            "command_id": self.command_id,
            "ok": self.ok,
            "message": self.message,
            "data": dict(self.data),
        }


class UxPlatformService:
    def __init__(self, db=None):
        self.db = db
        self.tokens = UxTokenSet()
        self._commands: dict[str, dict] = {}

    def get_tokens(self) -> dict:
        return self.tokens.to_dict()

    def resolve_component(self, component_id: str, variant: str = "default", state: str = "default") -> dict:
        return {
            "id": component_id,
            "variant": variant,
            "state": state,
            "tokens": self.get_tokens(),
        }

    def register_command(self, command_spec: dict) -> None:
        command_id = str(command_spec.get("id", "")).strip()
        if not command_id:
            return
        self._commands[command_id] = dict(command_spec)
        self._commands[command_id]["id"] = command_id

    def run_command(self, command_id: str, args: dict | None = None) -> dict:
        payload = dict(args or {})
        spec = self._commands.get(command_id)
        if not spec:
            return CommandResult(command_id, False, "command not found", {}).to_dict()

        result = CommandResult(
            command_id=command_id,
            ok=True,
            message="ok",
            data={"args": payload, "idempotent": bool(spec.get("idempotent", True))},
        ).to_dict()

        if self.db:
            self.db.execute(
                "INSERT INTO command_history(id, command_id, args_json, result_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (
                    f"cmd_{uuid.uuid4().hex}",
                    command_id,
                    json.dumps(payload, sort_keys=True),
                    json.dumps(result, sort_keys=True),
                    int(time.time()),
                ),
            )
            self.db.commit()
        return result

    def search_commands(self, query: str) -> list[dict]:
        q = (query or "").strip().lower()
        out = []
        for command_id, spec in self._commands.items():
            label = str(spec.get("label", ""))
            haystack = f"{command_id} {label}".lower()
            if not q or q in haystack:
                out.append(dict(spec))
        return sorted(out, key=lambda item: str(item.get("id", "")))

    def validate_accessibility(self, screen_id: str, screen: dict) -> dict:
        focus_order = list(screen.get("focus_order", []))
        has_focus_indicators = bool(screen.get("has_focus_indicators", False))
        reduced_motion_supported = bool(screen.get("reduced_motion_supported", False))
        contrast_checks = list(screen.get("contrast_checks", []))
        violations: list[str] = []

        if not focus_order:
            violations.append("focus_order_empty")
        else:
            seen = set()
            for item in focus_order:
                key = str(item)
                if key in seen:
                    violations.append(f"focus_order_duplicate:{key}")
                seen.add(key)

        if not has_focus_indicators:
            violations.append("focus_indicators_missing")
        if not reduced_motion_supported:
            violations.append("reduced_motion_missing")

        for item in contrast_checks:
            if not isinstance(item, dict):
                continue
            ratio = float(item.get("ratio", 0.0))
            name = str(item.get("name", "contrast_item"))
            if ratio < 4.5:
                violations.append(f"contrast_low:{name}")

        return AccessibilityReport(
            screen_id=screen_id,
            ok=len(violations) == 0,
            violations=violations,
            checks={
                "focus_count": len(focus_order),
                "has_focus_indicators": has_focus_indicators,
                "reduced_motion_supported": reduced_motion_supported,
                "contrast_check_count": len(contrast_checks),
            },
        ).to_dict()

    def readiness_report(self, output_dir: Path | str, ffmpeg_bin: str = "ffmpeg") -> dict:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        issues: list[str] = []

        ffmpeg_exec = shutil.which(ffmpeg_bin) if ffmpeg_bin else None
        ffmpeg_available = ffmpeg_exec is not None
        if ffmpeg_available:
            probe = subprocess.run([str(ffmpeg_exec), "-version"], capture_output=True, text=True, check=False)  # nosec B603
            ffmpeg_available = probe.returncode == 0
        if not ffmpeg_available:
            issues.append("ffmpeg_missing")

        writable = False
        try:
            probe_file = out_dir / "readiness_probe.txt"
            probe_file.write_text("ok", encoding="utf-8")
            probe_file.unlink(missing_ok=True)
            writable = True
        except OSError:
            writable = False
        if not writable:
            issues.append("output_not_writable")

        disk_check_available = True
        try:
            stat = shutil.disk_usage(out_dir)
            # 500MB soft signal for readiness; warning-only behavior.
            if stat.free < 500 * 1024 * 1024:
                issues.append("low_disk_space")
        except OSError:
            disk_check_available = False
            issues.append("disk_check_unavailable")

        return {
            "ok": len([i for i in issues if i not in {"low_disk_space"}]) == 0,
            "issues": issues,
            "checks": {
                "ffmpeg_available": ffmpeg_available,
                "output_writable": writable,
                "disk_check_available": disk_check_available,
            },
        }

    def guided_workflow_status(self, state: dict) -> dict:
        imported = bool(state.get("assets_imported", False))
        preset = bool(state.get("preset_selected", False))
        provenance = bool(state.get("provenance_complete", False))
        queued = bool(state.get("export_queued", False))

        step = "import_assets"
        if imported and not preset:
            step = "select_preset"
        elif imported and preset and not provenance:
            step = "fix_provenance"
        elif imported and preset and provenance and not queued:
            step = "queue_export"
        elif imported and preset and provenance and queued:
            step = "complete"

        return {
            "next_step": step,
            "can_queue_export": imported and preset and provenance,
            "is_complete": step == "complete",
        }

    def build_export_command_center(self, jobs: list[dict]) -> dict:
        buckets = {key: [] for key in ["queued", "running", "paused", "failed", "succeeded", "canceled"]}
        for job in jobs:
            status = str(job.get("status", "queued")).lower()
            if status not in buckets:
                status = "queued"
            buckets[status].append(dict(job))

        recovery_actions = []
        for failed in buckets["failed"]:
            recovery_actions.append(
                {"job_id": str(failed.get("id", "")), "actions": ["resume", "retry", "cleanup"]}
            )

        return {"buckets": buckets, "recovery_actions": recovery_actions}

    def relink_remediation(
        self, asset_id: str, integrity_ok: bool, provenance_ok: bool, candidates: list[str] | None = None
    ) -> dict:
        actions = []
        if not integrity_ok:
            actions.append("relink_asset")
        if not provenance_ok:
            actions.append("complete_provenance")
        return {"asset_id": asset_id, "actions": actions, "candidates": list(candidates or [])}

    def preset_migration_advice(self, presets: list[dict], target_schema: int) -> dict:
        warnings = []
        for preset in presets:
            schema = int(preset.get("schema_version", 0))
            if schema < target_schema:
                warnings.append(
                    {
                        "preset_id": str(preset.get("id", "")),
                        "from_schema": schema,
                        "to_schema": target_schema,
                        "action": "migrate",
                    }
                )
        return {"target_schema": target_schema, "warnings": warnings}
