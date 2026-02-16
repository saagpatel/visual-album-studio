extends RefCounted
class_name BatchService

func create_plan(variants: Array, max_concurrent: int = 2) -> Dictionary:
	var items: Array = []
	for variant in variants:
		items.append({
			"variant_id": String(variant.get("variant_id", "")),
			"status": "pending",
			"seed": int(variant.get("seed", 0)),
		})
	return {
		"max_concurrent": max_concurrent,
		"items": items,
	}

func reviewer_report(variants: Array, remix_service) -> Dictionary:
	var distances: Array = []
	for i in range(1, variants.size()):
		distances.append(remix_service.distance(variants[i - 1], variants[i]))

	var min_distance = 0.0
	var max_distance = 0.0
	var avg_distance = 0.0
	if not distances.is_empty():
		min_distance = distances.min()
		max_distance = distances.max()
		var total = 0.0
		for d in distances:
			total += d
		avg_distance = total / float(distances.size())

	var report_variants: Array = []
	for variant in variants:
		var params: Dictionary = variant.get("params", {})
		var changed_params: Array = params.keys()
		changed_params.sort()
		report_variants.append({
			"variant_id": String(variant.get("variant_id", "")),
			"seed": int(variant.get("seed", 0)),
			"structural_change": String(variant.get("structural_change", "")),
			"changed_params": changed_params,
		})

	return {
		"summary": {
			"count": variants.size(),
			"min_distance": min_distance,
			"avg_distance": avg_distance,
			"max_distance": max_distance,
		},
		"variants": report_variants,
	}
