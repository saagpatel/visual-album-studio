import pytest

from conftest import generate_wav
from vas_studio import VasError


def test_ts006_provenance_gating_blocks_production_export(runtime, test_root):
    audio = test_root / "fixtures" / "tone.wav"
    generate_wav(audio, duration_sec=1.0)
    asset_id = runtime.assets.import_asset(audio)

    project_id = runtime.create_project(name="TS006", duration_sec=1)

    with pytest.raises(VasError):
        runtime.export_project(project_id=project_id, audio_asset_id=asset_id, draft=False)

    result = runtime.export_project(project_id=project_id, audio_asset_id=asset_id, draft=True, simulate_only=True)
    assert "export_id" in result
