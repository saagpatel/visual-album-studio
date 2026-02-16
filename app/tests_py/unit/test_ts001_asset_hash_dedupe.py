from pathlib import Path

from conftest import generate_wav


def test_ts001_asset_hashing_and_dedupe(runtime, test_root):
    audio = test_root / "fixtures" / "tone.wav"
    generate_wav(audio, duration_sec=1.0)

    first = runtime.assets.import_asset(audio)
    second = runtime.assets.import_asset(audio)

    assert first == second
    assert runtime.assets.verify_integrity(first)
