extends RefCounted
class_name MappingService

func validate_mapping(mapping_dsl: String) -> bool:
	for raw in mapping_dsl.split("\n"):
		var line := raw.strip_edges()
		if line == "" or line.begins_with("#"):
			continue
		if line.find("=") == -1:
			push_error("E_MAPPING_PARSE_ERROR: Invalid mapping line '%s'" % line)
			return false
		var parts := line.split("=", false, 1)
		if parts.size() != 2:
			push_error("E_MAPPING_PARSE_ERROR: Invalid mapping assignment '%s'" % line)
			return false
		var expr_text := String(parts[1]).strip_edges()
		if not _validate_expr(expr_text):
			return false
	return true

func evaluate(mapping_dsl: String, ctx: Dictionary) -> Dictionary:
	var values := {
		"time_sec": float(ctx.get("time_sec", 0.0)),
		"beat_phase": float(ctx.get("beat_phase", 0.0)),
		"tempo_bpm": float(ctx.get("tempo_bpm", 0.0)),
	}

	var out := {}
	for raw in mapping_dsl.split("\n"):
		var line := raw.strip_edges()
		if line == "" or line.begins_with("#"):
			continue
		var parts := line.split("=", false, 1)
		if parts.size() != 2:
			continue
		var param_id := String(parts[0]).strip_edges()
		var expr_text := String(parts[1]).strip_edges()
		var expr := Expression.new()
		var err := expr.parse(expr_text, PackedStringArray(["time_sec", "beat_phase", "tempo_bpm"]))
		if err != OK:
			push_error("E_MAPPING_PARSE_ERROR: %s" % expr.get_error_text())
			continue
		var result := expr.execute([values["time_sec"], values["beat_phase"], values["tempo_bpm"]], self, false)
		if expr.has_execute_failed():
			push_error("E_MAPPING_PARSE_ERROR: execute failed for '%s'" % param_id)
			continue
		out[param_id] = float(result)

	var sorted_keys := out.keys()
	sorted_keys.sort()
	var sorted_out := {}
	for key in sorted_keys:
		sorted_out[key] = out[key]
	return sorted_out

func _validate_expr(expr_text: String) -> bool:
	var expr := Expression.new()
	var err := expr.parse(expr_text, PackedStringArray(["time_sec", "beat_phase", "tempo_bpm"]))
	if err != OK:
		push_error("E_MAPPING_PARSE_ERROR: %s" % expr.get_error_text())
		return false
	return true
