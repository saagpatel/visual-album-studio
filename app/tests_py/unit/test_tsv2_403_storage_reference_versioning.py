from pathlib import Path

from vas_studio import LocalObjectStorageAdapter


def test_tsv2_403_storage_reference_versioning_metadata(test_root):
    adapter = LocalObjectStorageAdapter(test_root / "out" / "cloud_store")
    stored = adapter.put_object(
        project_id="project_storage_403",
        object_key="renders/clip.mp4",
        data=b"video-v1",
        schema_version=1,
    )
    metadata = adapter.get_metadata(project_id="project_storage_403", object_key="renders/clip.mp4")

    assert stored["ok"] is True
    assert "schema_version=1" in stored["storage_ref"]
    assert metadata is not None
    assert metadata["size_bytes"] == len(b"video-v1")
    assert Path(metadata["path"]).exists()


def test_tsv2_403_storage_reference_versioning_unavailable(test_root):
    adapter = LocalObjectStorageAdapter(test_root / "out" / "cloud_store", available=False)
    result = adapter.put_object(
        project_id="project_storage_403",
        object_key="renders/clip.mp4",
        data=b"video-v2",
        schema_version=2,
    )
    assert result["ok"] is False
    assert result["error_code"] == "E_CLOUD_STORAGE_UNAVAILABLE"
