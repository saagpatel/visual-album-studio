from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from .ffmpeg_adapter import FFmpegAdapter
from .ids import new_id


@dataclass
class Track:
    track_id: str
    wav_path: Path
    volume_db: float = 0.0
    pan: float = 0.0
    start_offset_ms: int = 0
    loop_enabled: bool = False
    loop_start_ms: int | None = None
    loop_end_ms: int | None = None
    fade_in_ms: int = 0
    fade_out_ms: int = 0


@dataclass
class MixerProject:
    project_id: str
    tracks: list[Track] = field(default_factory=list)


class MixerService:
    def __init__(self, ffmpeg: FFmpegAdapter):
        self.ffmpeg = ffmpeg
        self.projects: dict[str, MixerProject] = {}

    def add_track(self, project_id: str, wav_path: Path) -> str:
        project = self.projects.setdefault(project_id, MixerProject(project_id))
        track_id = new_id("track")
        project.tracks.append(Track(track_id=track_id, wav_path=wav_path))
        return track_id

    def set_track_params(self, project_id: str, track_id: str, **params) -> None:
        project = self.projects[project_id]
        for t in project.tracks:
            if t.track_id == track_id:
                for k, v in params.items():
                    setattr(t, k, v)
                return
        raise KeyError(track_id)

    def bounce(self, project_id: str, out_wav: Path) -> dict:
        project = self.projects[project_id]
        inputs = []
        filters = []
        mix_inputs = []

        for i, t in enumerate(project.tracks):
            inputs.extend(["-i", str(t.wav_path)])
            filters.append(f"[{i}:a]volume={t.volume_db}dB[a{i}]")
            mix_inputs.append(f"[a{i}]")

        filter_complex = ";".join(filters) + ";" + "".join(mix_inputs) + f"amix=inputs={len(project.tracks)}:normalize=0[m]"

        args = [
            "-y",
            *inputs,
            "-filter_complex",
            filter_complex,
            "-map",
            "[m]",
            "-ac",
            "2",
            "-ar",
            "48000",
            "-sample_fmt",
            "s16",
            str(out_wav),
        ]
        self.ffmpeg.run(args)

        digest = hashlib.sha256(out_wav.read_bytes()).hexdigest()
        return {
            "bounce_id": new_id("bounce"),
            "sha256": digest,
            "created_at": int(time.time()),
            "manifest": {
                "project_id": project_id,
                "tracks": [t.track_id for t in project.tracks],
            },
        }

    @staticmethod
    def loop_boundary_diff(samples_a: bytes, samples_b: bytes) -> float:
        if not samples_a or not samples_b:
            return 0.0
        length = min(len(samples_a), len(samples_b))
        diffs = [abs(samples_a[i] - samples_b[i]) for i in range(length)]
        return sum(diffs) / max(len(diffs), 1)
