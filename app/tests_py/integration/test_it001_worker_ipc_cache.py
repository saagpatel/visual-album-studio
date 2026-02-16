from conftest import generate_wav


def test_it001_worker_ipc_and_cache(runtime, test_root):
    audio = test_root / "fixtures" / "tone.wav"
    generate_wav(audio, duration_sec=1.0)
    asset_id = runtime.assets.import_asset(audio)

    cache_id = runtime.analysis.request_analysis(
        audio_asset_id=asset_id,
        analysis_profile_id="analysis_default",
        analysis_version="phase1-v1",
        audio_path=runtime.paths.out_dir / runtime.db.execute("SELECT library_relpath FROM assets WHERE id = ?", (asset_id,)).fetchone()["library_relpath"],
    )
    row = runtime.db.execute("SELECT id, tempo_bpm FROM analysis_cache WHERE id = ?", (cache_id,)).fetchone()
    assert row is not None
    assert float(row["tempo_bpm"]) > 0
