extends RefCounted
class_name RemixService

func generate_variants(base_seed: int, count: int) -> Array:
	var variants: Array = []
	for i in count:
		variants.append({
			"variant_id": "variant_%03d" % i,
			"seed": base_seed + i,
			"params": {
				"mp.motion.float_amp": 10.0 + (i * 0.5),
				"mp.beat.pulse_amount": 0.2 + (i * 0.01),
				"mp.color.grade_amount": 0.05 + (i * 0.005),
				"mp.layout.art_scale": 0.6 + (i * 0.002),
				"mp.motion.zoom_amp": 0.01 + (i * 0.003),
			},
			"structural_change": ["layout", "palette", "typography"][i % 3],
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

func validate_variant(base: Dictionary, candidate: Dictionary, min_changed: int = 5, threshold: float = 0.8) -> Dictionary:
	var base_params: Dictionary = base.get("params", {})
	var candidate_params: Dictionary = candidate.get("params", {})
	var changed = 0
	for key in candidate_params.keys():
		if base_params.get(key) != candidate_params.get(key):
			changed += 1
	var score = distance(base, candidate)
	var has_structural_change = String(base.get("structural_change", "")) != String(candidate.get("structural_change", ""))
	return {
		"ok": changed >= min_changed and has_structural_change and score >= threshold,
		"score": score,
		"changed": changed,
	}
