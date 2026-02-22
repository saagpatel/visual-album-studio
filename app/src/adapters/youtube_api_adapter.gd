extends RefCounted
class_name YouTubeApiAdapter

const DEFAULT_SCRIPT_PATH = "scripts/youtube_adapter.py"

var python_bin: String = "python3"
var script_path: String = DEFAULT_SCRIPT_PATH
var access_token: String = ""
var use_mock: bool = false

func _init(
	p_python_bin: String = "python3",
	p_script_path: String = DEFAULT_SCRIPT_PATH,
	p_access_token: String = "",
	p_use_mock: bool = false
) -> void:
	python_bin = p_python_bin
	script_path = p_script_path
	access_token = p_access_token
	use_mock = p_use_mock

func set_access_token(token: String) -> void:
	access_token = token.strip_edges()

func list_channels() -> Dictionary:
	return _call("list_channels", {})

func start_resumable_upload(file_path: String, metadata: Dictionary) -> Dictionary:
	if use_mock:
		var mock_size = 0
		if FileAccess.file_exists(file_path):
			mock_size = int(FileAccess.get_file_as_bytes(file_path).size())
		return _ok({
			"session_url": "mock://resumable/session",
			"bytes_total": mock_size,
			"bytes_uploaded": 0,
		}, 200)

	return _call("start_resumable_upload", {
		"file_path": file_path,
		"metadata": metadata.duplicate(true),
	})

func resume_upload(session_url: String, file_path: String, bytes_uploaded: int, chunk_size: int = 8 * 1024 * 1024) -> Dictionary:
	if use_mock:
		var total = 0
		if FileAccess.file_exists(file_path):
			total = int(FileAccess.get_file_as_bytes(file_path).size())
		var uploaded = min(total, max(bytes_uploaded, 0) + max(chunk_size, 1))
		return _ok({
			"session_url": session_url,
			"bytes_total": total,
			"bytes_uploaded": uploaded,
			"complete": uploaded >= total,
			"video_id": "mock-video-id" if uploaded >= total else "",
		}, 308 if uploaded < total else 200)

	return _call("resume_upload", {
		"session_url": session_url,
		"file_path": file_path,
		"bytes_uploaded": bytes_uploaded,
		"chunk_size": chunk_size,
	})

func apply_metadata(video_id: String, metadata: Dictionary) -> Dictionary:
	if use_mock:
		return _ok({"video_id": video_id}, 200)
	return _call("apply_metadata", {
		"video_id": video_id,
		"metadata": metadata.duplicate(true),
	})

func upload_thumbnail(video_id: String, thumbnail_path: String) -> Dictionary:
	if use_mock:
		return _ok({"video_id": video_id, "thumbnail_path": thumbnail_path}, 200)
	return _call("upload_thumbnail", {
		"video_id": video_id,
		"thumbnail_path": thumbnail_path,
	})

func _call(command: String, payload: Dictionary) -> Dictionary:
	var token = access_token.strip_edges()
	if token == "":
		return _err("E_YT_AUTH_REQUIRED", 401, false, {"message": "access_token is required"})

	var resolved_script = _resolve_script_path()
	if not FileAccess.file_exists(resolved_script):
		return _err("E_YT_ADAPTER_SCRIPT_MISSING", 0, false, {"script_path": resolved_script})

	var full_payload = payload.duplicate(true)
	full_payload["access_token"] = token
	var stdout_lines: Array = []
	var cmd = PackedStringArray([resolved_script, command, JSON.stringify(full_payload)])
	var code = OS.execute(python_bin, cmd, stdout_lines, true)
	if code != 0:
		return _err("E_YT_ADAPTER_EXEC_FAILED", 0, true, {"exit_code": code, "output": stdout_lines})

	var raw = "\n".join(stdout_lines).strip_edges()
	if raw == "":
		return _err("E_YT_ADAPTER_EMPTY_RESPONSE", 0, true, {})

	var parsed: Variant = JSON.parse_string(raw)
	if typeof(parsed) != TYPE_DICTIONARY:
		return _err("E_YT_ADAPTER_INVALID_RESPONSE", 0, true, {"raw": raw})

	var response: Dictionary = parsed
	if not response.has("ok") or not response.has("error_code") or not response.has("http_status") or not response.has("retryable") or not response.has("data"):
		return _err("E_YT_ADAPTER_INVALID_ENVELOPE", 0, true, {"raw": response})
	return response

func _resolve_script_path() -> String:
	if script_path.is_absolute_path():
		return script_path
	var repo_root = OS.get_environment("VAS_REPO_ROOT").strip_edges()
	if repo_root != "":
		return repo_root.path_join(script_path)
	return script_path

func _ok(data: Dictionary, http_status: int = 200) -> Dictionary:
	return {
		"ok": true,
		"error_code": "",
		"http_status": http_status,
		"retryable": false,
		"data": data,
	}

func _err(error_code: String, http_status: int, retryable: bool, data: Dictionary) -> Dictionary:
	return {
		"ok": false,
		"error_code": error_code,
		"http_status": http_status,
		"retryable": retryable,
		"data": data,
	}
