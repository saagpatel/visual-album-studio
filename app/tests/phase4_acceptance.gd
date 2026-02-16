extends SceneTree

const RemixService = preload("res://src/core/remix_service.gd")
const BatchService = preload("res://src/core/batch_service.gd")

func _init() -> void:
	randomize()
	quit(_run())

func _run() -> int:
	var remix = RemixService.new()
	var batch = BatchService.new()
	var variants: Array = remix.generate_variants(1000, 100)
	if not _assert_true(variants.size() == 100, "generated 100 variants"):
		return 1

	var base: Dictionary = variants[0]
	var valid_count = 0
	for i in range(1, variants.size()):
		var validation = remix.validate_variant(base, variants[i], 5, 0.5)
		if validation.get("ok", false):
			valid_count += 1
	if not _assert_true(valid_count >= 50, "guardrails accept >=50 variants"):
		return 1

	var plan = batch.create_plan(variants, 4)
	if not _assert_true(Array(plan.get("items", [])).size() == 100, "batch plan contains 100 items"):
		return 1

	var report = batch.reviewer_report(variants, remix)
	if not _assert_true(int(report.get("summary", {}).get("count", 0)) == 100, "review report count 100"):
		return 1

	print("AT-004 product-path acceptance passed")
	return 0

func _assert_true(condition: bool, label: String) -> bool:
	if condition:
		print("[PASS] %s" % label)
		return true
	printerr("[FAIL] %s" % label)
	return false
