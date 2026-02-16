from pathlib import Path

from vas_studio import ChannelBindingGuard, QuotaBudget, ResumableUploadStore, UploadSession, pkce_pair


def test_at005_publish_pipeline_safety(tmp_path: Path):
    verifier, challenge = pkce_pair()
    assert len(verifier) > 20
    assert len(challenge) > 20

    store = ResumableUploadStore(tmp_path / "upload_state.json")
    session = UploadSession(session_id="u1", file_path=tmp_path / "video.mp4", bytes_total=2000, bytes_uploaded=1000)
    store.save(session)
    restored = store.load()
    assert restored is not None
    assert restored.bytes_uploaded == 1000

    guard = ChannelBindingGuard()
    assert guard.validate("ch_A", "ch_A")
    assert not guard.validate("ch_A", "ch_B")

    quota = QuotaBudget(500)
    est = quota.estimate_publish(with_thumbnail=True, with_playlist=True)
    assert est == 200
    assert quota.can_run(est)
    quota.consume(est)
    quota.consume(est)
    assert not quota.can_run(est)
