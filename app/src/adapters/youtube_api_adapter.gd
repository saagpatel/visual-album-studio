extends RefCounted
class_name YouTubeApiAdapter

func start_resumable_upload(_file_path: String, _metadata: Dictionary) -> Dictionary:
	return {
		"ok": true,
		"session_url": "mock://resumable/session",
		"bytes_total": 0,
	}

func resume_upload(_session_url: String, _file_path: String, _bytes_uploaded: int) -> Dictionary:
	return {
		"ok": true,
		"bytes_uploaded": _bytes_uploaded,
	}

func apply_metadata(_video_id: String, _metadata: Dictionary) -> Dictionary:
	return {"ok": true}

func upload_thumbnail(_video_id: String, _thumbnail_path: String) -> Dictionary:
	return {"ok": true}
