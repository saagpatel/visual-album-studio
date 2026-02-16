import hashlib
from pathlib import Path

from conftest import generate_wav
from vas_studio import FFmpegAdapter, MixerService


def test_at003_mixer_bounce_deterministic(tmp_path: Path):
    ff = FFmpegAdapter("ffmpeg")
    mixer = MixerService(ff)

    a = tmp_path / "a.wav"
    b = tmp_path / "b.wav"
    generate_wav(a, duration_sec=2.0, freq=220.0)
    generate_wav(b, duration_sec=2.0, freq=440.0)

    pid = "project_mix"
    t1 = mixer.add_track(pid, a)
    t2 = mixer.add_track(pid, b)
    mixer.set_track_params(pid, t1, volume_db=-1.0)
    mixer.set_track_params(pid, t2, volume_db=-2.0)

    out1 = tmp_path / "mix1.wav"
    out2 = tmp_path / "mix2.wav"
    r1 = mixer.bounce(pid, out1)
    r2 = mixer.bounce(pid, out2)

    h1 = hashlib.sha256(out1.read_bytes()).hexdigest()
    h2 = hashlib.sha256(out2.read_bytes()).hexdigest()

    assert r1["sha256"] == h1
    assert r2["sha256"] == h2
    assert h1 == h2
