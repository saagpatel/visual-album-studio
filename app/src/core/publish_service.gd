extends RefCounted
class_name PublishService

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
