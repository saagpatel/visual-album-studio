from pathlib import Path

from conftest import generate_wav
from vas_studio import UxPlatformService


def test_it010_relink_and_provenance_remediation(runtime, test_root: Path):
    audio = test_root / "fixtures" / "tone.wav"
    generate_wav(audio, duration_sec=1.0)
    asset_id = runtime.assets.import_asset(audio)

    ux = UxPlatformService(runtime.db)
    remediation = ux.relink_remediation(
        asset_id=asset_id,
        integrity_ok=False,
        provenance_ok=False,
        candidates=[str(audio), str(test_root / "fixtures" / "alt_tone.wav")],
    )

    assert remediation["asset_id"] == asset_id
    assert "relink_asset" in remediation["actions"]
    assert "complete_provenance" in remediation["actions"]
    assert len(remediation["candidates"]) >= 1
