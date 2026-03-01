from pathlib import Path

from vas_studio import CollaborationService, LocalObjectStorageAdapter


def test_itv2_404_storage_reference_versioning(runtime, test_root):
    storage = LocalObjectStorageAdapter(test_root / "out" / "storage_v2")
    service = CollaborationService(runtime.db, storage_adapter=storage)
    project_id = "project_storage_it_404"

    v1 = service.store_object_reference(
        project_id=project_id,
        object_key="renders/final.mp4",
        data=b"video-v1",
        schema_version=1,
    )
    v2 = service.store_object_reference(
        project_id=project_id,
        object_key="renders/final.mp4",
        data=b"video-v2",
        schema_version=2,
    )
    row = service.object_reference(project_id=project_id, object_key="renders/final.mp4")
    metadata = storage.get_metadata(project_id=project_id, object_key="renders/final.mp4")

    assert v1["ok"] is True
    assert v2["ok"] is True
    assert row is not None
    assert int(row["schema_version"]) == 2
    assert "schema_version=2" in row["storage_ref"]
    assert metadata is not None
    assert metadata["size_bytes"] == len(b"video-v2")
    assert Path(metadata["path"]).exists()


def test_itv2_404_storage_reference_versioning_handles_storage_outage(runtime, test_root):
    storage = LocalObjectStorageAdapter(test_root / "out" / "storage_v2", available=False)
    service = CollaborationService(runtime.db, storage_adapter=storage)

    fail = service.store_object_reference(
        project_id="project_storage_it_404_outage",
        object_key="renders/final.mp4",
        data=b"video",
        schema_version=1,
    )

    assert fail["ok"] is False
    assert fail["error_code"] == "E_CLOUD_STORAGE_UNAVAILABLE"
