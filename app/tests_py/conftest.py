from __future__ import annotations

import math
import struct
import sys
import wave
from pathlib import Path

import pytest

from vas_studio.phase1 import Phase1Runtime


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture
def test_root(tmp_path: Path, repo_root: Path) -> Path:
    root = tmp_path / "vas"
    root.mkdir(parents=True, exist_ok=True)
    (root / "migrations").mkdir(parents=True, exist_ok=True)
    for sql in (repo_root / "migrations").glob("*.sql"):
        (root / "migrations" / sql.name).write_text(sql.read_text(encoding="utf-8"), encoding="utf-8")
    return root


@pytest.fixture
def runtime(test_root: Path) -> Phase1Runtime:
    rt = Phase1Runtime(test_root, worker_cmd=[sys.executable, "-m", "vas_audio_worker.cli"])
    rt.setup()
    return rt


def generate_wav(path: Path, duration_sec: float = 2.0, sample_rate: int = 48000, freq: float = 440.0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = int(duration_sec * sample_rate)
    with wave.open(str(path), "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        for n in range(frames):
            value = int(32767 * 0.2 * math.sin(2 * math.pi * freq * (n / sample_rate)))
            packed = struct.pack("<hh", value, value)
            f.writeframesraw(packed)
