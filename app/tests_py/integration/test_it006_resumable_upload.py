from pathlib import Path

from vas_studio import ResumableUploadStore, UploadSession


def test_it006_resumable_upload_store(tmp_path: Path):
    state = tmp_path / "upload_state.json"
    store = ResumableUploadStore(state)

    session = UploadSession(
        session_id="sess1",
        file_path=tmp_path / "video.mp4",
        bytes_total=1000,
        bytes_uploaded=350,
        etag="etag-it006",
    )
    store.save(session)

    loaded = store.load()
    assert loaded is not None
    assert loaded.session_id == "sess1"
    assert loaded.bytes_uploaded == 350
    assert loaded.etag == "etag-it006"
