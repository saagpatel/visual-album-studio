extends RefCounted
class_name PackagingAdapter

func generate_manifest(
	profile_id: String,
	channel: String,
	artifacts: Array,
	toolchain: Dictionary,
	version: String
) -> Dictionary:
	var normalized_artifacts: Array = []
	var by_key: Dictionary = {}
	var keys: Array = []
	for artifact in artifacts:
		if typeof(artifact) == TYPE_DICTIONARY:
			var item: Dictionary = artifact.duplicate(true)
			var key = "%s|%s" % [String(item.get("name", "")), String(item.get("path", ""))]
			if not by_key.has(key):
				keys.append(key)
				by_key[key] = []
			var bucket: Array = by_key[key]
			bucket.append(item)
			by_key[key] = bucket
	keys.sort()
	for key in keys:
		var bucket: Array = by_key[key]
		for item in bucket:
			normalized_artifacts.append(item)

	var sorted_toolchain: Dictionary = {}
	var toolchain_keys = toolchain.keys()
	toolchain_keys.sort()
	for key in toolchain_keys:
		sorted_toolchain[key] = toolchain[key]

	return {
		"schema_version": 1,
		"profile_id": profile_id,
		"channel": channel,
		"version": version,
		"toolchain": sorted_toolchain,
		"artifacts": normalized_artifacts,
	}

func content_hash(payload: Dictionary) -> String:
	var hash = HashingContext.new()
	hash.start(HashingContext.HASH_SHA256)
	hash.update(JSON.stringify(payload).to_utf8_buffer())
	return hash.finish().hex_encode()

func write_manifest(path: String, payload: Dictionary) -> Dictionary:
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var file = FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return {"ok": false, "error": "E_PACKAGING_FAILED", "path": path}
	file.store_string(JSON.stringify(payload, "\t"))
	file.close()
	return {
		"ok": true,
		"path": path,
		"sha256": content_hash(payload),
	}
