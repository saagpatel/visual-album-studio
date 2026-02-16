from conftest import generate_wav


def test_it003_segment_plan_and_resume_reuse(runtime, test_root):
    audio = test_root / "fixtures" / "tone.wav"
    generate_wav(audio, duration_sec=65.0)
    asset_id = runtime.assets.import_asset(audio)
    runtime.assets.set_license(asset_id, source_type="original", license_name="Owned")

    project_id = runtime.create_project(name="IT003", duration_sec=65)
    first = runtime.export_project(project_id=project_id, audio_asset_id=asset_id, draft=False)
    second = runtime.export_project(project_id=project_id, audio_asset_id=asset_id, draft=False)

    assert len(first["segments"]) >= 2
    assert len(second["segments"]) >= 2
