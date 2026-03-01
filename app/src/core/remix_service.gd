extends RefCounted
class_name RemixService

const DEFAULT_RULE_SPEC := {
	"grading_profiles": ["clean", "cinematic", "high_contrast"],
	"thumbnail_layout_rules": ["safe_center", "safe_left", "safe_right"],
	"duration_cycle_sec": [10, 30, 600, 7200],
	"audio_swap_ids": [""],
	"palette_profiles": ["warm", "cool", "mono"],
	"typography_profiles": ["grotesk", "serif", "display"],
}

func generate_variants(base_seed: int, count: int, rule_spec: Dictionary = {}) -> Array:
	var normalized = _normalize_rule_spec(rule_spec)
	var spec_id = _rule_spec_id(normalized)
	var variants: Array = []
	for i in range(count):
		variants.append({
			"variant_id": "variant_%03d" % i,
			"variant_spec_id": spec_id,
			"source_rule_hash": spec_id,
			"seed": base_seed + i,
			"duration_sec": int(normalized["duration_cycle_sec"][i % normalized["duration_cycle_sec"].size()]),
			"params": {
				"mp.motion.float_amp": 10.0 + (i * 0.5),
				"mp.beat.pulse_amount": 0.2 + (i * 0.01),
				"mp.color.grade_amount": 0.05 + (i * 0.005),
				"mp.layout.art_scale": 0.6 + (i * 0.002),
				"mp.motion.zoom_amp": 0.01 + (i * 0.003),
			},
			"structural_change": ["layout", "palette", "typography"][i % 3],
			"grading_profile": String(normalized["grading_profiles"][i % normalized["grading_profiles"].size()]),
			"thumbnail_layout_rule": String(normalized["thumbnail_layout_rules"][i % normalized["thumbnail_layout_rules"].size()]),
			"palette_profile": String(normalized["palette_profiles"][i % normalized["palette_profiles"].size()]),
			"typography_profile": String(normalized["typography_profiles"][i % normalized["typography_profiles"].size()]),
			"audio_swap_id": String(normalized["audio_swap_ids"][i % normalized["audio_swap_ids"].size()]),
		})
	return variants

func distance(a: Dictionary, b: Dictionary) -> float:
	var a_params: Dictionary = a.get("params", {})
	var b_params: Dictionary = b.get("params", {})
	var keys: Array = a_params.keys()
	for key in b_params.keys():
		if not keys.has(key):
			keys.append(key)
	keys.sort()

	var score = 0.0
	for key in keys:
		var av = float(a_params.get(key, 0.0))
		var bv = float(b_params.get(key, 0.0))
		score += abs(av - bv)

	if String(a.get("structural_change", "")) != String(b.get("structural_change", "")):
		score += 1.0
	return score

func validate_variant(
	base: Dictionary,
	candidate: Dictionary,
	min_changed: int = 5,
	threshold: float = 0.8,
	structural_change_required: bool = true
) -> Dictionary:
	var base_params: Dictionary = base.get("params", {})
	var candidate_params: Dictionary = candidate.get("params", {})
	var changed_count = 0
	for key in candidate_params.keys():
		if base_params.get(key) != candidate_params.get(key):
			changed_count += 1
	var score = distance(base, candidate)
	var has_structural_change = String(base.get("structural_change", "")) != String(candidate.get("structural_change", ""))
	var rejection_code = ""
	if changed_count < min_changed:
		rejection_code = "E_VARIANT_CHANGED_PARAMS"
	elif structural_change_required and not has_structural_change:
		rejection_code = "E_VARIANT_STRUCTURAL_REQUIRED"
	elif score < threshold:
		rejection_code = "E_VARIANT_DISTANCE_TOO_LOW"
	var ok = rejection_code == ""
	return {
		"ok": ok,
		"score": score,
		"changed_count": changed_count,
		"has_structural_change": has_structural_change,
		"rejection_code": rejection_code,
	}

func _normalize_rule_spec(rule_spec: Dictionary) -> Dictionary:
	var out = DEFAULT_RULE_SPEC.duplicate(true)
	for key in rule_spec.keys():
		out[key] = rule_spec[key]
	for required in ["grading_profiles", "thumbnail_layout_rules", "duration_cycle_sec", "audio_swap_ids", "palette_profiles", "typography_profiles"]:
		var arr: Array = out.get(required, [])
		if arr.is_empty():
			arr = DEFAULT_RULE_SPEC[required]
		out[required] = arr
	return out

func _rule_spec_id(spec: Dictionary) -> String:
	var json = JSON.stringify(spec, "\t")
	var ctx = HashingContext.new()
	ctx.start(HashingContext.HASH_SHA256)
	ctx.update(json.to_utf8_buffer())
	return "spec_%s" % ctx.finish().hex_encode().substr(0, 16)
