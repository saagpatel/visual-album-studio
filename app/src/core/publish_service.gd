extends RefCounted
class_name PublishService

const YouTubeApiAdapter = preload("res://src/adapters/youtube_api_adapter.gd")

class UploadSession:
	extends RefCounted
	var session_id: String
	var file_path: String
	var bytes_total: int
	var bytes_uploaded: int

	func _init(p_session_id: String, p_file_path: String, p_bytes_total: int, p_bytes_uploaded: int = 0) -> void:
		session_id = p_session_id
		file_path = p_file_path
		bytes_total = p_bytes_total
		bytes_uploaded = p_bytes_uploaded

class ResumableUploadStore:
	extends RefCounted
	var state_path: String

	func _init(p_state_path: String) -> void:
		state_path = p_state_path
		DirAccess.make_dir_recursive_absolute(state_path.get_base_dir())

	func save(session: UploadSession) -> void:
		var file = FileAccess.open(state_path, FileAccess.WRITE)
		if file == null:
			return
		file.store_string(JSON.stringify({
			"session_id": session.session_id,
			"file_path": session.file_path,
			"bytes_total": session.bytes_total,
			"bytes_uploaded": session.bytes_uploaded,
		}, "\t"))
		file.close()

	func load() -> UploadSession:
		if not FileAccess.file_exists(state_path):
			return null
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(state_path))
		if typeof(parsed) != TYPE_DICTIONARY:
			return null
		var d: Dictionary = parsed
		return UploadSession.new(
			String(d.get("session_id", "")),
			String(d.get("file_path", "")),
			int(d.get("bytes_total", 0)),
			int(d.get("bytes_uploaded", 0))
		)

class QuotaBudget:
	extends RefCounted
	var daily_budget: int
	var used: int = 0

	func _init(p_daily_budget: int = 10000) -> void:
		daily_budget = p_daily_budget

	func estimate_publish(with_thumbnail: bool = true, with_playlist: bool = false) -> int:
		var units = 100
		if with_thumbnail:
			units += 50
		if with_playlist:
			units += 50
		return units

	func can_run(estimated: int) -> bool:
		return (used + estimated) <= daily_budget

	func consume(units: int) -> void:
		used += units

class ChannelBindingGuard:
	extends RefCounted
	func validate(selected_channel_id: String, profile_channel_id: String) -> bool:
		return selected_channel_id == profile_channel_id

var youtube_adapter

func _init(p_youtube_adapter = null) -> void:
	youtube_adapter = p_youtube_adapter if p_youtube_adapter != null else YouTubeApiAdapter.new()

func set_access_token(access_token: String) -> void:
	if youtube_adapter != null and youtube_adapter.has_method("set_access_token"):
		youtube_adapter.set_access_token(access_token)

func list_channels() -> Dictionary:
	if youtube_adapter == null:
		return _publish_err("E_YT_ADAPTER_UNAVAILABLE", 0, true, {})
	return _normalize_adapter_result(youtube_adapter.list_channels())

func start_upload_session(
	file_path: String,
	metadata: Dictionary,
	selected_channel_id: String = "",
	profile_channel_id: String = ""
) -> Dictionary:
	var guard = ChannelBindingGuard.new()
	if selected_channel_id != "" and profile_channel_id != "" and not guard.validate(selected_channel_id, profile_channel_id):
		return _publish_err("E_CHANNEL_INVALID", 400, false, {"selected_channel_id": selected_channel_id, "profile_channel_id": profile_channel_id})

	var quota = QuotaBudget.new(int(metadata.get("quota_budget", 10000)))
	quota.used = int(metadata.get("quota_used", 0))
	var with_thumbnail = bool(metadata.get("with_thumbnail", true))
	var with_playlist = bool(metadata.get("with_playlist", false))
	var estimated = quota.estimate_publish(with_thumbnail, with_playlist)
	if not quota.can_run(estimated):
		return _publish_err("E_YT_QUOTA_EXCEEDED", 429, false, {"estimated_units": estimated, "used": quota.used, "budget": quota.daily_budget})

	if youtube_adapter == null:
		return _publish_err("E_YT_ADAPTER_UNAVAILABLE", 0, true, {})
	var started = _normalize_adapter_result(youtube_adapter.start_resumable_upload(file_path, metadata))
	if not bool(started.get("ok", false)):
		return started
	var data: Dictionary = started.get("data", {})
	data["quota_estimate"] = estimated
	started["data"] = data
	return started

func resume_upload_step(
	session_url: String,
	file_path: String,
	bytes_uploaded: int,
	chunk_size: int = 8 * 1024 * 1024
) -> Dictionary:
	if youtube_adapter == null:
		return _publish_err("E_YT_ADAPTER_UNAVAILABLE", 0, true, {})
	return _normalize_adapter_result(
		youtube_adapter.resume_upload(
			session_url,
			file_path,
			bytes_uploaded,
			chunk_size
		)
	)

func finalize_upload(video_id: String, metadata: Dictionary, thumbnail_path: String = "") -> Dictionary:
	if youtube_adapter == null:
		return _publish_err("E_YT_ADAPTER_UNAVAILABLE", 0, true, {})
	var meta_result = _normalize_adapter_result(youtube_adapter.apply_metadata(video_id, metadata))
	if not bool(meta_result.get("ok", false)):
		return meta_result

	if thumbnail_path != "":
		var thumb_result = _normalize_adapter_result(youtube_adapter.upload_thumbnail(video_id, thumbnail_path))
		if not bool(thumb_result.get("ok", false)):
			return thumb_result

	return _publish_ok({
		"video_id": video_id,
		"metadata_applied": true,
		"thumbnail_applied": thumbnail_path != "",
	})

func pkce_pair() -> Dictionary:
	var verifier = _urlsafe_base64(Crypto.new().generate_random_bytes(32))
	var hash = HashingContext.new()
	hash.start(HashingContext.HASH_SHA256)
	hash.update(verifier.to_utf8_buffer())
	var challenge = _urlsafe_base64(hash.finish())
	return {
		"verifier": verifier,
		"challenge": challenge,
	}

func _urlsafe_base64(bytes: PackedByteArray) -> String:
	var encoded = Marshalls.raw_to_base64(bytes)
	encoded = encoded.replace("+", "-").replace("/", "_").replace("=", "")
	return encoded

func _normalize_adapter_result(raw_result: Dictionary) -> Dictionary:
	var ok = bool(raw_result.get("ok", false))
	var error_code = String(raw_result.get("error_code", ""))
	var http_status = int(raw_result.get("http_status", 0))
	var retryable = bool(raw_result.get("retryable", false))
	var data = raw_result.get("data", {})
	if typeof(data) != TYPE_DICTIONARY:
		data = {"raw": data}
	if ok:
		return _publish_ok(data, http_status)
	return _publish_err(error_code if error_code != "" else "E_YT_ADAPTER_FAILED", http_status, retryable, data)

func _publish_ok(data: Dictionary, http_status: int = 200) -> Dictionary:
	return {
		"ok": true,
		"error_code": "",
		"http_status": http_status,
		"retryable": false,
		"data": data,
	}

func _publish_err(error_code: String, http_status: int, retryable: bool, data: Dictionary) -> Dictionary:
	return {
		"ok": false,
		"error_code": error_code,
		"http_status": http_status,
		"retryable": retryable,
		"data": data,
	}
