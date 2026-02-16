extends RefCounted
class_name DiagnosticsAdapter

const VasIds = preload("res://src/shared/ids.gd")

var secret_patterns: Array = [
	"VAS_YT_CLIENT_SECRET",
	"VAS_YT_REFRESH_TOKEN",
	"Authorization: Bearer",
	"refresh_token",
	"access_token",
	"client_secret",
]

func _init(p_secret_patterns: Array = []) -> void:
	if not p_secret_patterns.is_empty():
		secret_patterns = p_secret_patterns.duplicate()

func collect_log_summaries(log_paths: Array, max_lines_per_file: int = 200) -> Dictionary:
	var files: Array = []
	var redactions = {
		"lines_scanned": 0,
		"lines_redacted": 0,
		"matches": {},
	}

	for raw_path in log_paths:
		var path = String(raw_path)
		if path == "" or not FileAccess.file_exists(path):
			continue
		var lines = FileAccess.get_file_as_string(path).split("\n")
		var limited = lines.slice(0, min(lines.size(), max_lines_per_file))
		var sanitized: Array = []
		for raw_line in limited:
			redactions["lines_scanned"] = int(redactions["lines_scanned"]) + 1
			var clean = redact_text(String(raw_line), redactions)
			sanitized.append(clean)
		files.append({
			"path": path,
			"line_count": sanitized.size(),
			"content": "\n".join(sanitized),
		})

	return {
		"files": files,
		"redaction_summary": redactions,
	}

func redact_text(input: String, redactions: Dictionary = {}) -> String:
	var line = input
	for pattern in secret_patterns:
		if line.to_lower().find(String(pattern).to_lower()) != -1:
			if redactions.has("lines_redacted"):
				redactions["lines_redacted"] = int(redactions["lines_redacted"]) + 1
			if redactions.has("matches"):
				var matches: Dictionary = redactions["matches"]
				matches[pattern] = int(matches.get(pattern, 0)) + 1
				redactions["matches"] = matches
			line = "[REDACTED]"
			break
	return line

func export_bundle(output_dir: String, scope: Dictionary, payload: Dictionary) -> Dictionary:
	DirAccess.make_dir_recursive_absolute(output_dir)
	var bundle_id = VasIds.new_id("diag")
	var out_path = output_dir.path_join("%s.json" % bundle_id)
	var bundle = {
		"id": bundle_id,
		"schema_version": 1,
		"scope": scope.duplicate(true),
		"payload": payload.duplicate(true),
		"created_at": int(Time.get_unix_time_from_system()),
	}
	var file = FileAccess.open(out_path, FileAccess.WRITE)
	if file == null:
		return {"ok": false, "error": "E_DIAGNOSTICS_EXPORT_FAILED", "path": out_path}
	file.store_string(JSON.stringify(bundle, "\t"))
	file.close()

	return {
		"ok": true,
		"id": bundle_id,
		"path": out_path,
		"bundle": bundle,
	}
