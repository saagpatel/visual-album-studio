extends RefCounted
class_name UxPlatformService

const VasIds = preload("res://src/shared/ids.gd")
const UxTypes = preload("res://src/shared/ux_types.gd")

var db
var _commands: Dictionary = {}
var _tokens := UxTypes.UxTokenSet.new(
	[4, 8, 12, 16, 24, 32],
	{
		"xs": 12,
		"sm": 14,
		"md": 16,
		"lg": 20,
		"xl": 24,
	},
	{
		"background": "#121212",
		"surface": "#1f1f1f",
		"text": "#f5f5f5",
		"muted_text": "#c0c0c0",
		"accent": "#2f7ed8",
		"danger": "#c94848",
	},
	{
		"loading": "spinner",
		"disabled": "opacity_50",
		"error": "inline_banner",
		"warning": "inline_banner",
		"success": "toast",
	}
)

func _init(p_db = null) -> void:
	db = p_db

func get_tokens() -> Dictionary:
	return _tokens.to_dict()

func resolve_component(component_id: String, variant: String = "default", state: String = "default") -> Dictionary:
	return {
		"id": component_id,
		"variant": variant,
		"state": state,
		"tokens": _tokens.to_dict(),
	}

func register_command(command_spec: Dictionary) -> void:
	var command_id = String(command_spec.get("id", "")).strip_edges()
	if command_id == "":
		return
	_commands[command_id] = command_spec.duplicate(true)

func run_command(command_id: String, args: Dictionary = {}) -> Dictionary:
	if not _commands.has(command_id):
		return UxTypes.CommandResult.new(command_id, false, "command not found", {}).to_dict()

	var spec: Dictionary = _commands[command_id]
	var result = UxTypes.CommandResult.new(command_id, true, "ok", {
		"args": args.duplicate(true),
		"idempotent": bool(spec.get("idempotent", true)),
	}).to_dict()

	if db != null:
		var now = int(Time.get_unix_time_from_system())
		db.exec("""
			INSERT INTO command_history(id, command_id, args_json, result_json, created_at)
			VALUES (%s, %s, %s, %s, %d);
		""" % [
			db.quote(VasIds.new_id("cmd")),
			db.quote(command_id),
			db.quote(JSON.stringify(args)),
			db.quote(JSON.stringify(result)),
			now,
		])
	return result

func search_commands(query: String) -> Array:
	var q = query.to_lower().strip_edges()
	var hits: Array = []
	var sortable_ids: Array = []
	var by_id: Dictionary = {}
	for key in _commands.keys():
		var spec: Dictionary = _commands[key]
		var label = String(spec.get("label", ""))
		var haystack = ("%s %s" % [key, label]).to_lower()
		if q == "" or haystack.find(q) != -1:
			var id = String(spec.get("id", key))
			sortable_ids.append(id)
			by_id[id] = spec.duplicate(true)
	sortable_ids.sort()
	for id in sortable_ids:
		hits.append(by_id[id])
	return hits

func validate_accessibility(screen_id: String, screen: Dictionary) -> Dictionary:
	var focus_order: Array = screen.get("focus_order", [])
	var has_focus_indicators = bool(screen.get("has_focus_indicators", false))
	var reduced_motion_supported = bool(screen.get("reduced_motion_supported", false))
	var contrast_checks: Array = screen.get("contrast_checks", [])
	var violations: Array = []

	if focus_order.is_empty():
		violations.append("focus_order_empty")
	else:
		var seen := {}
		for id in focus_order:
			var key = String(id)
			if seen.has(key):
				violations.append("focus_order_duplicate:%s" % key)
			seen[key] = true

	if not has_focus_indicators:
		violations.append("focus_indicators_missing")

	if not reduced_motion_supported:
		violations.append("reduced_motion_missing")

	for item in contrast_checks:
		if typeof(item) != TYPE_DICTIONARY:
			continue
		var ratio = float(item.get("ratio", 0.0))
		var name = String(item.get("name", "contrast_item"))
		if ratio < 4.5:
			violations.append("contrast_low:%s" % name)

	var report = UxTypes.AccessibilityReport.new(
		screen_id,
		violations.is_empty(),
		violations,
		{
			"focus_count": focus_order.size(),
			"has_focus_indicators": has_focus_indicators,
			"reduced_motion_supported": reduced_motion_supported,
			"contrast_check_count": contrast_checks.size(),
		}
	)
	return report.to_dict()

func readiness_report(output_dir: String) -> Dictionary:
	DirAccess.make_dir_recursive_absolute(output_dir)
	var ffmpeg_out: Array = []
	var ffmpeg_code = OS.execute("ffmpeg", PackedStringArray(["-version"]), ffmpeg_out, true)
	var writable_path = output_dir.path_join("readiness_probe.txt")
	var writable = false
	var file = FileAccess.open(writable_path, FileAccess.WRITE)
	if file != null:
		file.store_string("ok")
		file.close()
		writable = true
		DirAccess.remove_absolute(writable_path)

	var drive_status = 1
	var disk_code = OS.execute("sh", PackedStringArray(["-lc", "df -Pk " + _shell_escape(output_dir)]), [], true)
	if disk_code == 0:
		drive_status = 1
	else:
		drive_status = 0

	var issues: Array = []
	if ffmpeg_code != 0:
		issues.append("ffmpeg_missing")
	if not writable:
		issues.append("output_not_writable")
	if drive_status == 0:
		issues.append("disk_check_unavailable")

	return {
		"ok": issues.is_empty(),
		"issues": issues,
		"checks": {
			"ffmpeg_available": ffmpeg_code == 0,
			"output_writable": writable,
			"disk_check_available": drive_status == 1,
		},
	}

func guided_workflow_status(input_state: Dictionary) -> Dictionary:
	var imported = bool(input_state.get("assets_imported", false))
	var preset = bool(input_state.get("preset_selected", false))
	var provenance = bool(input_state.get("provenance_complete", false))
	var queued = bool(input_state.get("export_queued", false))

	var step = "import_assets"
	if imported and not preset:
		step = "select_preset"
	elif imported and preset and not provenance:
		step = "fix_provenance"
	elif imported and preset and provenance and not queued:
		step = "queue_export"
	elif imported and preset and provenance and queued:
		step = "complete"

	return {
		"next_step": step,
		"can_queue_export": imported and preset and provenance,
		"is_complete": step == "complete",
	}

func build_export_command_center(jobs: Array) -> Dictionary:
	var buckets = {
		"queued": [],
		"running": [],
		"paused": [],
		"failed": [],
		"succeeded": [],
		"canceled": [],
	}
	for job in jobs:
		if typeof(job) != TYPE_DICTIONARY:
			continue
		var status = String(job.get("status", "queued")).to_lower()
		if not buckets.has(status):
			status = "queued"
		buckets[status].append(job)

	var recovery_actions: Array = []
	for failed in buckets["failed"]:
		recovery_actions.append({
			"job_id": failed.get("id", ""),
			"actions": ["resume", "retry", "cleanup"],
		})

	return {
		"buckets": buckets,
		"recovery_actions": recovery_actions,
	}

func relink_remediation(asset_id: String, integrity_ok: bool, provenance_ok: bool, candidates: Array) -> Dictionary:
	var actions: Array = []
	if not integrity_ok:
		actions.append("relink_asset")
	if not provenance_ok:
		actions.append("complete_provenance")
	return {
		"asset_id": asset_id,
		"actions": actions,
		"candidates": candidates.duplicate(true),
	}

func preset_migration_advice(presets: Array, target_schema: int) -> Dictionary:
	var warnings: Array = []
	for raw in presets:
		if typeof(raw) != TYPE_DICTIONARY:
			continue
		var preset: Dictionary = raw
		var schema = int(preset.get("schema_version", 0))
		if schema < target_schema:
			warnings.append({
				"preset_id": String(preset.get("id", "")),
				"from_schema": schema,
				"to_schema": target_schema,
				"action": "migrate",
			})
	return {
		"target_schema": target_schema,
		"warnings": warnings,
	}

func _shell_escape(value: String) -> String:
	return "'" + value.replace("'", "'\"'\"'") + "'"
