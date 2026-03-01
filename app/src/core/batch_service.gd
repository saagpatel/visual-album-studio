extends RefCounted
class_name BatchService

const DEFAULT_WINDOW_START := "22:00"
const DEFAULT_WINDOW_END := "06:00"
const DEFAULT_RETRY_LIMIT := 2
const DEFAULT_BACKOFF_BASE_SECONDS := 30
const DEFAULT_BACKOFF_FACTOR := 2
const DEFAULT_BACKOFF_MAX_SECONDS := 600
const DEFAULT_DISK_GUARD_MIN_BYTES := 10 * 1024 * 1024 * 1024
const DEFAULT_CIRCUIT_FAILURE_THRESHOLD := 5
const DEFAULT_CIRCUIT_WINDOW_SECONDS := 600

func create_plan(variants: Array, max_concurrent: int = 2, options: Dictionary = {}) -> Dictionary:
	var now = int(Time.get_unix_time_from_system())
	var window_start = String(options.get("window_start", DEFAULT_WINDOW_START))
	var window_end = String(options.get("window_end", DEFAULT_WINDOW_END))
	var retry_limit = int(options.get("retry_limit", DEFAULT_RETRY_LIMIT))
	var disk_guard_min_bytes = int(options.get("disk_guard_min_bytes", DEFAULT_DISK_GUARD_MIN_BYTES))
	var disk_free_bytes = int(options.get("disk_free_bytes", _disk_free_bytes()))
	var status = "planned"
	var blocked_reason = ""
	if disk_free_bytes > 0 and disk_free_bytes < disk_guard_min_bytes:
		status = "blocked"
		blocked_reason = "E_DISK_GUARD_BLOCKED"

	var items: Array = []
	for variant in variants:
		items.append({
			"variant_id": String(variant.get("variant_id", "")),
			"status": "pending",
			"seed": int(variant.get("seed", 0)),
			"attempts": 0,
			"last_error_json": {},
			"scheduled_at": now,
		})
	return {
		"schema_version": 1,
		"status": status,
		"blocked_reason": blocked_reason,
		"max_concurrent": max_concurrent,
		"window_start": window_start,
		"window_end": window_end,
		"retry_limit": retry_limit,
		"backoff_policy": {
			"base_seconds": int(options.get("backoff_base_seconds", DEFAULT_BACKOFF_BASE_SECONDS)),
			"factor": int(options.get("backoff_factor", DEFAULT_BACKOFF_FACTOR)),
			"max_seconds": int(options.get("backoff_max_seconds", DEFAULT_BACKOFF_MAX_SECONDS)),
		},
		"disk_guard_min_bytes": disk_guard_min_bytes,
		"disk_free_bytes": disk_free_bytes,
		"circuit_breaker": {
			"failure_threshold": int(options.get("circuit_failure_threshold", DEFAULT_CIRCUIT_FAILURE_THRESHOLD)),
			"window_seconds": int(options.get("circuit_window_seconds", DEFAULT_CIRCUIT_WINDOW_SECONDS)),
			"circuit_open": false,
		},
		"items": items,
	}

func reviewer_report(variants: Array, remix_service, near_duplicate_threshold: float = 0.8) -> Dictionary:
	var distances: Array = []
	var flagged_near_duplicates: Array = []
	for i in range(1, variants.size()):
		var distance = float(remix_service.distance(variants[i - 1], variants[i]))
		distances.append(distance)
		if distance < near_duplicate_threshold:
			flagged_near_duplicates.append({
				"variant_a": String(variants[i - 1].get("variant_id", "")),
				"variant_b": String(variants[i].get("variant_id", "")),
				"distance_score": distance,
				"rejection_code": "E_VARIANT_DISTANCE_TOO_LOW",
			})

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
			"variant_spec_id": String(variant.get("variant_spec_id", "")),
			"seed": int(variant.get("seed", 0)),
			"structural_change": String(variant.get("structural_change", "")),
			"distance_score": float(variant.get("distance_score", 0.0)),
			"changed_params_summary": {
				"count": changed_params.size(),
				"keys": changed_params,
			},
			"changed_params": changed_params,
		})

	return {
		"schema_version": 1,
		"summary": {
			"count": variants.size(),
			"min_distance": min_distance,
			"avg_distance": avg_distance,
			"max_distance": max_distance,
		},
		"flagged_near_duplicates": flagged_near_duplicates,
		"variants": report_variants,
	}

func evaluate_circuit_breaker(
	failure_timestamps: Array,
	now_ts: int = 0,
	threshold: int = DEFAULT_CIRCUIT_FAILURE_THRESHOLD,
	window_seconds: int = DEFAULT_CIRCUIT_WINDOW_SECONDS
) -> Dictionary:
	if now_ts <= 0:
		now_ts = int(Time.get_unix_time_from_system())
	var recent_failures = 0
	for ts in failure_timestamps:
		var t = int(ts)
		if now_ts - t <= window_seconds:
			recent_failures += 1
	return {
		"recent_failures": recent_failures,
		"circuit_open": recent_failures >= threshold,
		"threshold": threshold,
		"window_seconds": window_seconds,
	}

func mark_item_failure(item: Dictionary, error_code: String, retry_limit: int = DEFAULT_RETRY_LIMIT) -> Dictionary:
	var updated = item.duplicate(true)
	var attempts = int(updated.get("attempts", 0)) + 1
	updated["attempts"] = attempts
	updated["last_error_json"] = {"error_code": error_code}
	updated["status"] = "failed" if attempts > retry_limit else "pending"
	return updated

func _disk_free_bytes() -> int:
	var dir = DirAccess.open(".")
	if dir == null:
		return -1
	return int(dir.get_space_left())
