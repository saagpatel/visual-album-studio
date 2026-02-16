extends RefCounted
class_name AssetService

const VasIds = preload("res://src/shared/ids.gd")

var db
var ffmpeg
var library_dir: String
var out_root: String

func _init(p_db = null, p_ffmpeg = null, p_library_dir: String = "", p_out_root: String = "") -> void:
	db = p_db
	ffmpeg = p_ffmpeg
	library_dir = p_library_dir
	out_root = p_out_root
	if library_dir != "":
		DirAccess.make_dir_recursive_absolute(library_dir)

func import_asset(src_path: String, kind: String = "") -> String:
	if not FileAccess.file_exists(src_path):
		push_error("E_ASSET_NOT_FOUND: %s" % src_path)
		return ""

	var resolved_kind = kind if kind != "" else _kind_from_path(src_path)
	var source_digest = _sha256_file(src_path)
	var stored_digest = source_digest

	if resolved_kind == "audio":
		var canonical = _canonical_audio_path(source_digest)
		if not FileAccess.file_exists(canonical):
			var decode = ffmpeg.run(PackedStringArray([
				"-y",
				"-i", src_path,
				"-vn",
				"-ac", "2",
				"-ar", "48000",
				"-sample_fmt", "s16",
				canonical,
			]))
			if not decode["ok"]:
				push_error("E_FFMPEG_FAILED: %s" % decode["output"])
				return ""
		stored_digest = _sha256_file(canonical)

	var existing = db.query(
		"SELECT id FROM assets WHERE sha256 = %s AND kind = %s LIMIT 1;" % [db.quote(stored_digest), db.quote(resolved_kind)]
	)
	if not existing.is_empty():
		return str(existing[0].get("id", ""))

	var source_target = _target_path(resolved_kind, source_digest, src_path)
	if not FileAccess.file_exists(source_target):
		DirAccess.make_dir_recursive_absolute(source_target.get_base_dir())
		DirAccess.copy_absolute(src_path, source_target)

	var library_path = source_target
	if resolved_kind == "audio":
		library_path = _canonical_audio_path(source_digest)

	var asset_id = VasIds.new_id("asset")
	var now = int(Time.get_unix_time_from_system())
	var file_size = _file_size(src_path)
	var relpath = _relative_to(out_root, library_path)
	var original_relpath = _relative_to(out_root, source_target)

	var insert_asset = """
		INSERT INTO assets(
			id, kind, sha256, size_bytes, original_path, library_relpath,
			mime_type, created_at, imported_at, metadata_json
		) VALUES (
			%s, %s, %s, %d, %s, %s,
			'', %d, %d, '{}'
		);
	""" % [
		db.quote(asset_id),
		db.quote(resolved_kind),
		db.quote(stored_digest),
		file_size,
		db.quote(src_path),
		db.quote(relpath),
		now,
		now,
	]
	var res_asset = db.exec(insert_asset)
	if not res_asset["ok"]:
		push_error("Failed to insert asset: %s" % res_asset["output"])
		return ""

	var insert_license = """
		INSERT INTO asset_license(asset_id, source_type, is_production_allowed, updated_at, proof_relpath)
		VALUES (%s, 'unknown', 0, %d, %s);
	""" % [db.quote(asset_id), now, db.quote(original_relpath)]
	var res_license = db.exec(insert_license)
	if not res_license["ok"]:
		push_error("Failed to insert license metadata: %s" % res_license["output"])
		return ""

	return asset_id

func set_license(
	asset_id: String,
	source_type: String,
	license_name: String = "",
	license_url: String = "",
	attribution_text: String = "",
	proof_relpath: String = "",
	notes: String = ""
) -> void:
	var now = int(Time.get_unix_time_from_system())
	var allowed = source_type != "unknown" and (license_name != "" or license_url != "")
	var sql = """
		UPDATE asset_license
		SET source_type = %s,
			license_name = %s,
			license_url = %s,
			attribution_text = %s,
			proof_relpath = %s,
			notes = %s,
			is_production_allowed = %d,
			updated_at = %d
		WHERE asset_id = %s;
	""" % [
		db.quote(source_type),
		db.quote(license_name if license_name != "" else null),
		db.quote(license_url if license_url != "" else null),
		db.quote(attribution_text if attribution_text != "" else null),
		db.quote(proof_relpath if proof_relpath != "" else null),
		db.quote(notes if notes != "" else null),
		1 if allowed else 0,
		now,
		db.quote(asset_id),
	]
	db.exec(sql)

func validate_production_allowed(asset_id: String) -> Dictionary:
	var rows = db.query(
		"SELECT source_type, license_name, license_url, is_production_allowed FROM asset_license WHERE asset_id = %s LIMIT 1;" % db.quote(asset_id)
	)
	if rows.is_empty():
		return {"allowed": false, "reason": "Missing license metadata"}
	var row: Dictionary = rows[0]
	if str(row.get("source_type", "unknown")) == "unknown":
		return {"allowed": false, "reason": "Audio source_type is unknown"}
	if str(row.get("license_name", "")) == "" and str(row.get("license_url", "")) == "":
		return {"allowed": false, "reason": "Audio license_name or license_url is required"}
	if int(row.get("is_production_allowed", 0)) != 1:
		return {"allowed": false, "reason": "Audio not marked production allowed"}
	return {"allowed": true, "reason": "ok"}

func verify_integrity(asset_id: String) -> bool:
	var rows = db.query("SELECT sha256, library_relpath FROM assets WHERE id = %s LIMIT 1;" % db.quote(asset_id))
	if rows.is_empty():
		return false
	var row: Dictionary = rows[0]
	var rel = str(row.get("library_relpath", ""))
	if rel == "":
		return false
	var path = out_root.path_join(rel)
	if not FileAccess.file_exists(path):
		return false
	return _sha256_file(path) == str(row.get("sha256", ""))

func provenance_json(asset_id: String, template_id: String, preset_id: String, mapping_id: String, seed: int) -> Dictionary:
	var asset_rows = db.query("SELECT id, sha256 FROM assets WHERE id = %s LIMIT 1;" % db.quote(asset_id))
	var lic_rows = db.query(
		"SELECT source_type, license_name, license_url, attribution_text, proof_relpath, notes FROM asset_license WHERE asset_id = %s LIMIT 1;" % db.quote(asset_id)
	)

	var asset: Dictionary = asset_rows[0] if not asset_rows.is_empty() else {}
	var lic: Dictionary = lic_rows[0] if not lic_rows.is_empty() else {}

	var proof: Array = []
	var proof_rel = str(lic.get("proof_relpath", ""))
	if proof_rel != "":
		proof.append({"type": "file", "value": proof_rel})

	var attribution = str(lic.get("attribution_text", ""))
	return {
		"schema_version": 1,
		"audio": {
			"asset_id": str(asset.get("id", asset_id)),
			"sha256": str(asset.get("sha256", "")),
			"source_type": str(lic.get("source_type", "unknown")),
			"license_name": lic.get("license_name"),
			"license_url": lic.get("license_url"),
			"attribution_text": lic.get("attribution_text"),
			"proof": proof,
			"notes": lic.get("notes"),
		},
		"originality_ledger": {
			"template_id": template_id,
			"preset_id": preset_id,
			"mapping_id": mapping_id,
			"seed": seed,
			"notable_changes": [],
			"user_notes": null,
		},
		"attribution_block": attribution,
	}

func _kind_from_path(path: String) -> String:
	var ext = path.get_extension().to_lower()
	if ext in ["wav", "mp3", "flac", "m4a", "aac", "aiff", "aif"]:
		return "audio"
	if ext in ["png", "jpg", "jpeg", "webp"]:
		return "image"
	if ext in ["ttf", "otf"]:
		return "font"
	return "other"

func _target_path(kind: String, sha256: String, src_path: String) -> String:
	var subdir = "other"
	match kind:
		"audio":
			subdir = "audio_src"
		"image":
			subdir = "images"
		"font":
			subdir = "fonts"
		_:
			subdir = "other"
	var parent = library_dir.path_join(subdir).path_join(sha256.substr(0, 2))
	DirAccess.make_dir_recursive_absolute(parent)
	var ext = src_path.get_extension().to_lower()
	if ext == "":
		ext = "bin"
	return parent.path_join("%s.%s" % [sha256, ext])

func _canonical_audio_path(sha256: String) -> String:
	var parent = library_dir.path_join("audio").path_join(sha256.substr(0, 2))
	DirAccess.make_dir_recursive_absolute(parent)
	return parent.path_join("%s.wav" % sha256)

func _sha256_file(path: String) -> String:
	var file = FileAccess.open(path, FileAccess.READ)
	if file == null:
		return ""
	var hash = HashingContext.new()
	hash.start(HashingContext.HASH_SHA256)
	while not file.eof_reached():
		hash.update(file.get_buffer(1024 * 1024))
	file.close()
	return hash.finish().hex_encode()

func _file_size(path: String) -> int:
	var file = FileAccess.open(path, FileAccess.READ)
	if file == null:
		return 0
	var size = int(file.get_length())
	file.close()
	return size

func _relative_to(root: String, abs_path: String) -> String:
	var normalized_root = root
	if not normalized_root.ends_with("/"):
		normalized_root += "/"
	if abs_path.begins_with(normalized_root):
		return abs_path.substr(normalized_root.length())
	return abs_path
