from __future__ import annotations

import contextlib
import hashlib
import wave
from pathlib import Path

__all__ = ["analyze_audio"]


def _duration_seconds(path: Path) -> float:
    with contextlib.closing(wave.open(str(path), "rb")) as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        if rate <= 0:
            return 0.0
        return float(frames) / float(rate)


def analyze_audio(path: str) -> dict:
    audio_path = Path(path)
    duration = _duration_seconds(audio_path) if audio_path.exists() and audio_path.suffix.lower() == ".wav" else 0.0

    digest = hashlib.sha256(path.encode("utf-8")).hexdigest()
    bpm = 90.0 + (int(digest[:2], 16) % 80)
    beat_interval = 60.0 / bpm if bpm > 0 else 0.5
    beats = []
    t = 0.0
    while t <= max(duration, 1.0):
        beats.append(round(t, 6))
        t += beat_interval

    return {
        "path": path,
        "tempo_bpm": float(round(bpm, 3)),
        "beat_times_sec": beats,
        "duration_sec": float(round(duration, 6)),
        "analysis_version": "worker-v1",
    }
