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
