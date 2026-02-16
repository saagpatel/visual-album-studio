extends RefCounted
class_name ProductizationService

const VasIds = preload("res://src/shared/ids.gd")
const SupportTypes = preload("res://src/shared/support_types.gd")
const DiagnosticsAdapter = preload("res://src/adapters/diagnostics_adapter.gd")
const PackagingAdapter = preload("res://src/adapters/packaging_adapter.gd")
const SECRET_KEY_HINTS = [
	"refresh_token",
	"access_token",
	"client_secret",
	"authorization",
	"api_key",
	"password",
	"secret",
]

var db
var diagnostics
var packaging
var paths: Dictionary = {}

func _init(
	p_db = null,
	p_diagnostics = null,
	p_packaging = null,
	p_paths: Dictionary = {}
) -> void:
	db = p_db
	diagnostics = p_diagnostics if p_diagnostics != null else DiagnosticsAdapter.new()
	packaging = p_packaging if p_packaging != null else PackagingAdapter.new()
	paths = p_paths.duplicate(true)

func run_packaging_dry_run(profile_id: String) -> Dictionary:
	var channel = _release_channel_for_profile(profile_id)
	var out_root = _path_or_default("out_dir", "out")
	var pkg_dir = out_root.path_join("productization").path_join("packaging").path_join(profile_id)
	var manifest_path = pkg_dir.path_join("manifest.json")

	var artifacts: Array = [
		{"name": "app_bundle_stub", "path": "app/"},
		{"name": "worker_package_stub", "path": "worker/"},
		{"name": "native_keyring_stub", "path": "native/vas_keyring/"},
	]
	var manifest = packaging.generate_manifest(
		profile_id,
		channel,
		artifacts,
		{
			"godot": "4.4.x",
			"ffmpeg": "managed",
			"python": "3.11+",
			"rust": "stable",
		},
		"phase7-dry-run"
	)
	var write_res = packaging.write_manifest(manifest_path, manifest)
	if not bool(write_res.get("ok", false)):
		return {
			"ok": false,
			"error": "E_PACKAGING_FAILED",
			"path": manifest_path,
		}

	var now = int(Time.get_unix_time_from_system())
	var manifest_hash = String(write_res.get("sha256", ""))
	manifest["content_sha256"] = manifest_hash
	if db != null:
		var sql = """
			INSERT OR REPLACE INTO release_profiles(id, channel, manifest_json, created_at, updated_at)
			VALUES (%s, %s, %s, COALESCE((SELECT created_at FROM release_profiles WHERE id = %s), %d), %d);
		""" % [
			db.quote(profile_id),
			db.quote(channel),
			db.quote(JSON.stringify(manifest)),
			db.quote(profile_id),
			now,
			now,
		]
		db.exec(sql)

	var package_info = SupportTypes.PackageManifest.new(
		profile_id,
		manifest_path,
		manifest_hash,
		now
	)
	return {
		"ok": true,
		"manifest": manifest,
		"package": package_info.to_dict(),
	}

func export_diagnostics(scope: Dictionary) -> Dictionary:
	var out_root = _path_or_default("out_dir", "out")
	var logs_dir = out_root.path_join("logs")
	var output_dir = out_root.path_join("diagnostics")
	var log_paths: Array = scope.get("log_paths", [])
	if log_paths.is_empty():
		log_paths = _discover_log_paths(logs_dir)

	var safe_scope: Dictionary = _redact_variant(scope)
	var summaries = diagnostics.collect_log_summaries(log_paths)
	var payload = {
		"log_summary": summaries,
		"scope": safe_scope.duplicate(true),
		"toolchain": {
			"godot": "4.4.x",
			"ffmpeg": "managed",
		},
		"generated_at": int(Time.get_unix_time_from_system()),
	}
	var exported = diagnostics.export_bundle(output_dir, safe_scope, payload)
	if not bool(exported.get("ok", false)):
		return {
			"ok": false,
			"error": "E_DIAGNOSTICS_EXPORT_FAILED",
			"details": exported,
		}

	var bundle_id = String(exported.get("id", ""))
	var out_path = String(exported.get("path", ""))
	var redaction_summary = summaries.get("redaction_summary", {})
	var now = int(Time.get_unix_time_from_system())
	if db != null:
		var sql = """
			INSERT OR REPLACE INTO diagnostics_exports(id, scope_json, output_relpath, redaction_summary_json, created_at)
			VALUES (%s, %s, %s, %s, %d);
		""" % [
			db.quote(bundle_id),
			db.quote(JSON.stringify(safe_scope)),
			db.quote(_relative_to_root(out_path)),
			db.quote(JSON.stringify(redaction_summary)),
			now,
		]
		db.exec(sql)

	var info = SupportTypes.DiagnosticsBundleInfo.new(
		bundle_id,
		out_path,
		redaction_summary,
		now
	)
	return {
		"ok": true,
		"diagnostics": info.to_dict(),
		"bundle": exported.get("bundle", {}),
	}

func get_release_channels() -> Array:
	var selected = "stable"
	if db != null:
		var rows = db.query("SELECT value_json FROM app_kv WHERE key = 'release_channel' LIMIT 1;")
		if not rows.is_empty():
			var raw = String(rows[0].get("value_json", ""))
			if ["stable", "beta", "dev"].has(raw):
				selected = raw
			elif raw.begins_with("{\""):
				var parsed: Variant = JSON.parse_string(raw)
				if typeof(parsed) == TYPE_DICTIONARY:
					selected = String(parsed.get("channel", "stable"))
			elif raw.find("channel:") != -1:
				if raw.find("beta") != -1:
					selected = "beta"
				elif raw.find("dev") != -1:
					selected = "dev"
				else:
					selected = "stable"

	var channels = ["stable", "beta", "dev"]
	var out: Array = []
	for channel in channels:
		out.append({
			"id": channel,
			"selected": channel == selected,
		})
	return out

func set_release_channel(channel_id: String) -> Dictionary:
	if not ["stable", "beta", "dev"].has(channel_id):
		return {
			"ok": false,
			"error": "E_CHANNEL_INVALID",
			"message": "Unsupported release channel: %s" % channel_id,
		}
	if db != null:
		var now = int(Time.get_unix_time_from_system())
		var payload = "{\"channel\":\"%s\"}" % channel_id
		db.exec("""
			INSERT OR REPLACE INTO app_kv(key, value_json, updated_at)
			VALUES ('release_channel', %s, %d);
		""" % [
			db.quote(payload),
			now,
		])
	return {"ok": true, "channel": channel_id}

func generate_support_report(context: Dictionary) -> Dictionary:
	var safe_context: Dictionary = _redact_variant(context)
	var code = String(safe_context.get("error_code", "E_UNKNOWN"))
	var runbook = _runbook_for_error(code)
	var report_id = VasIds.new_id("support")
	var details = {
		"context": safe_context.duplicate(true),
		"runbook": runbook,
		"classification": _classify_severity(code),
	}
	var now = int(Time.get_unix_time_from_system())
	if db != null:
		var sql = """
			INSERT OR REPLACE INTO support_reports(id, context_json, report_json, created_at)
			VALUES (%s, %s, %s, %d);
		""" % [
			db.quote(report_id),
			db.quote(JSON.stringify(safe_context)),
			db.quote(JSON.stringify(details)),
			now,
		]
		db.exec(sql)

	var report = SupportTypes.SupportReport.new(
		report_id,
		String(details.get("classification", "info")),
		"Troubleshooting guidance generated for %s" % code,
		details
	)
	return report.to_dict()

func _release_channel_for_profile(profile_id: String) -> String:
	if db == null:
		return "stable"
	var rows = db.query("SELECT channel FROM release_profiles WHERE id = %s LIMIT 1;" % db.quote(profile_id))
	if rows.is_empty():
		return "stable"
	return String(rows[0].get("channel", "stable"))

func _runbook_for_error(code: String) -> String:
	if code.begins_with("E_FFMPEG") or code == "E_DISK_FULL":
		return "disk-full-or-ffmpeg"
	if code.begins_with("E_KEYRING"):
		return "keyring-unavailable"
	if code.begins_with("E_YT_") or code == "E_CHANNEL_INVALID":
		return "youtube-auth-or-quota"
	if code.begins_with("E_LICENSE"):
		return "provenance-remediation"
	return "general-troubleshooting"

func _classify_severity(code: String) -> String:
	if code == "E_DISK_FULL" or code.begins_with("E_FFMPEG"):
		return "high"
	if code.begins_with("E_YT_") or code.begins_with("E_KEYRING"):
		return "medium"
	return "info"

func _discover_log_paths(logs_dir: String) -> Array:
	var paths_out: Array = []
	var dir = DirAccess.open(logs_dir)
	if dir == null:
		return paths_out
	for file_name in dir.get_files():
		if file_name.ends_with(".log"):
			paths_out.append(logs_dir.path_join(file_name))
	paths_out.sort()
	return paths_out

func _relative_to_root(abs_path: String) -> String:
	var root = _path_or_default("root", "")
	if root == "":
		return abs_path
	if not root.ends_with("/"):
		root += "/"
	if abs_path.begins_with(root):
		return abs_path.substr(root.length())
	return abs_path

func _path_or_default(key: String, fallback: String) -> String:
	if paths.has(key):
		return String(paths[key])
	return fallback

func _redact_variant(value: Variant) -> Variant:
	match typeof(value):
		TYPE_DICTIONARY:
			var input: Dictionary = value
			var out: Dictionary = {}
			for key in input.keys():
				var key_str = String(key)
				if _key_looks_secret(key_str):
					out[key_str] = "[REDACTED]"
				else:
					out[key_str] = _redact_variant(input[key])
			return out
		TYPE_ARRAY:
			var input_array: Array = value
			var out_array: Array = []
			for item in input_array:
				out_array.append(_redact_variant(item))
			return out_array
		TYPE_STRING:
			return diagnostics.redact_text(String(value))
		_:
			return value

func _key_looks_secret(key_name: String) -> bool:
	var lowered = key_name.to_lower()
	for marker in SECRET_KEY_HINTS:
		if lowered.find(marker) != -1:
			return true
	return false
