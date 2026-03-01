from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .errors import VasError


@dataclass
class ParallaxFrame:
    t: float
    x: float
    y: float
    zoom: float


class PhotoAnimator:
    def tier0_path(self, duration_sec: float, fps: int, pan_x: float, pan_y: float, start_zoom: float, end_zoom: float):
        frames = []
        total = int(duration_sec * fps)
        if total <= 0:
            return frames
        for i in range(total):
            t = i / fps
            alpha = i / max(total - 1, 1)
            frames.append(
                ParallaxFrame(
                    t=t,
                    x=pan_x * alpha,
                    y=pan_y * alpha,
                    zoom=start_zoom + (end_zoom - start_zoom) * alpha,
                )
            )
        return frames

    def resolve_model_or_fallback(self, *, model_id: str, registry=None) -> dict:
        if not model_id:
            return {"mode": "tier0", "reason": "E_MODEL_NOT_SPECIFIED", "model_path": None}
        if registry is None:
            return {"mode": "tier0", "reason": "E_MODEL_NOT_INSTALLED", "model_path": None}

        model = registry.get_model(model_id) if hasattr(registry, "get_model") else None
        if not model:
            return {"mode": "tier0", "reason": "E_MODEL_NOT_INSTALLED", "model_path": None}
        if str(model.get("status", "candidate")) in {"blocked", "deprecated"}:
            return {"mode": "tier0", "reason": "E_MODEL_UNAVAILABLE", "model_path": None}

        model_path = registry.resolve_model_path(model_id) if hasattr(registry, "resolve_model_path") else None
        if model_path is None:
            return {"mode": "tier0", "reason": "E_MODEL_NOT_INSTALLED", "model_path": None}
        return {"mode": "model", "reason": "", "model_path": str(model_path)}

    def resolve_auto_model_or_fallback(self, *, model_family: str, hardware_profile, registry=None) -> dict:
        if registry is None or not hasattr(registry, "recommend_model_for_hardware"):
            return {"mode": "tier0", "reason": "E_MODEL_NOT_INSTALLED", "model_id": None, "model_path": None}

        recommendation = registry.recommend_model_for_hardware(
            model_family=model_family,
            hardware_profile=hardware_profile,
        )
        profile_class = ""
        if hasattr(registry, "classify_hardware_profile"):
            profile_class = registry.classify_hardware_profile(hardware_profile)
        if not recommendation.get("ok"):
            if hasattr(registry, "record_selection_event") and profile_class:
                registry.record_selection_event(
                    model_family=model_family,
                    selected_model_id=None,
                    profile_class=profile_class,
                    hardware_profile=hardware_profile,
                    candidates=list(recommendation.get("candidates", [])),
                    outcome="fallback",
                    reason=str(recommendation.get("error", "E_MODEL_NO_COMPATIBLE")),
                )
            return {
                "mode": "tier0",
                "reason": recommendation.get("error", "E_MODEL_NO_COMPATIBLE"),
                "model_id": None,
                "model_path": None,
            }

        model_id = str(recommendation.get("model_id", ""))
        resolved = self.resolve_model_or_fallback(model_id=model_id, registry=registry)
        if hasattr(registry, "record_selection_event") and profile_class:
            selection_outcome = "selected" if resolved.get("mode") == "model" else "fallback"
            selection_reason = "" if selection_outcome == "selected" else str(resolved.get("reason", "E_MODEL_NO_COMPATIBLE"))
            registry.record_selection_event(
                model_family=model_family,
                selected_model_id=model_id if selection_outcome == "selected" else None,
                profile_class=profile_class,
                hardware_profile=hardware_profile,
                candidates=list(recommendation.get("candidates", [])),
                outcome=selection_outcome,
                reason=selection_reason,
            )
        resolved["model_id"] = model_id if resolved["mode"] == "model" else None
        return resolved


class ModelManager:
    def __init__(self, models_dir: Path):
        self.models_dir = models_dir
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def install_from_file(self, src: Path, *, model_id: str, expected_sha256: str) -> Path:
        if not src.exists():
            raise VasError("E_MODEL_NOT_INSTALLED", f"Model source missing: {src}")
        digest = hashlib.sha256(src.read_bytes()).hexdigest()
        if digest != expected_sha256:
            raise VasError("E_MODEL_LICENSE_UNKNOWN", "Checksum mismatch for model", details={"expected": expected_sha256, "actual": digest})
        target = self.models_dir / model_id
        target.mkdir(parents=True, exist_ok=True)
        dst = target / src.name
        dst.write_bytes(src.read_bytes())
        (target / "provenance.json").write_text(json.dumps({"sha256": digest, "source": str(src)}, indent=2), encoding="utf-8")
        return dst
