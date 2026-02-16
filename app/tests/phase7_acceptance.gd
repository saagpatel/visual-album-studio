extends SceneTree

const SQLiteAdapter = preload("res://src/adapters/sqlite_adapter.gd")
const DiagnosticsAdapter = preload("res://src/adapters/diagnostics_adapter.gd")
const PackagingAdapter = preload("res://src/adapters/packaging_adapter.gd")
const UxPlatformService = preload("res://src/core/ux_platform_service.gd")
const ProductizationService = preload("res://src/core/productization_service.gd")

func _init() -> void:
	randomize()
	quit(_run())

func _run() -> int:
	var repo_root = OS.get_environment("VAS_REPO_ROOT")
	if repo_root == "":
		repo_root = ProjectSettings.globalize_path("res://").get_base_dir()
	var out_root = repo_root.path_join("out/product_phase7")
	DirAccess.make_dir_recursive_absolute(out_root)
	DirAccess.make_dir_recursive_absolute(out_root.path_join("logs"))

	var db = SQLiteAdapter.new(out_root.path_join("vas.db"))
	var schema = db.apply_migrations(repo_root.path_join("migrations"), 7)
	if not _assert_true(schema >= 7, "migrations through phase 7"):
		return 1

	var ux = UxPlatformService.new(db)
	var productization = ProductizationService.new(
		db,
		DiagnosticsAdapter.new(),
		PackagingAdapter.new(),
		{
			"root": repo_root,
			"out_dir": out_root,
		}
	)

	var tokens = ux.get_tokens()
	if not _assert_true(Array(tokens.get("spacing_scale", [])).size() >= 4, "design tokens available"):
		return 1

	ux.register_command({
		"id": "export.retry_last",
		"label": "Retry Last Export",
		"description": "Retry the latest failed export",
		"idempotent": true,
	})
	var command_result = ux.run_command("export.retry_last", {"job_id": "job_phase7"})
	if not _assert_true(bool(command_result.get("ok", false)), "command dispatch"):
		return 1

	var readiness = ux.readiness_report(out_root.path_join("phase7_onboarding"))
	if not _assert_true(bool(readiness.get("checks", {}).get("output_writable", false)), "readiness output writable"):
		return 1

	var guided = ux.guided_workflow_status({
		"assets_imported": true,
		"preset_selected": true,
		"provenance_complete": true,
		"export_queued": false,
	})
	if not _assert_true(String(guided.get("next_step", "")) == "queue_export", "guided workflow queue step"):
		return 1

	var command_center = ux.build_export_command_center([
		{"id": "job1", "status": "failed"},
		{"id": "job2", "status": "running"},
	])
	if not _assert_true(Array(command_center.get("recovery_actions", [])).size() == 1, "command center recovery action"):
		return 1

	var accessibility = ux.validate_accessibility("phase7_acceptance", {
		"focus_order": ["onboard", "guided", "command", "diagnostics"],
		"has_focus_indicators": true,
		"reduced_motion_supported": true,
		"contrast_checks": [{"name": "primary", "ratio": 6.0}],
	})
	if not _assert_true(bool(accessibility.get("ok", false)), "accessibility baseline"):
		return 1

	var log_path = out_root.path_join("logs").path_join("phase7.log")
	var log_file = FileAccess.open(log_path, FileAccess.WRITE)
	log_file.store_string("normal line\nAuthorization: Bearer abc123\nrefresh_token=zzz\n")
	log_file.close()

	var diag = productization.export_diagnostics({"log_paths": [log_path], "scope_id": "at007"})
	if not _assert_true(bool(diag.get("ok", false)), "diagnostics export"):
		return 1
	var diag_path = String(diag.get("diagnostics", {}).get("output_path", ""))
	var diag_json = _read_json(diag_path)
	var lines_redacted = int(diag_json.get("payload", {}).get("log_summary", {}).get("redaction_summary", {}).get("lines_redacted", 0))
	if not _assert_true(lines_redacted >= 1, "diagnostics redaction applied"):
		return 1

	var pack_a = productization.run_packaging_dry_run("phase7_profile")
	var pack_b = productization.run_packaging_dry_run("phase7_profile")
	if not _assert_true(bool(pack_a.get("ok", false)) and bool(pack_b.get("ok", false)), "packaging dry run"):
		return 1
	var hash_a = String(pack_a.get("package", {}).get("content_sha256", ""))
	var hash_b = String(pack_b.get("package", {}).get("content_sha256", ""))
	if not _assert_true(hash_a == hash_b and hash_a != "", "packaging determinism hash"):
		return 1

	var set_channel = productization.set_release_channel("beta")
	if not _assert_true(bool(set_channel.get("ok", false)), "set release channel"):
		return 1
	var channels = productization.get_release_channels()
	var selected_ok = false
	for item in channels:
		if typeof(item) != TYPE_DICTIONARY:
			continue
		if String(item.get("id", "")) == "beta" and bool(item.get("selected", false)):
			selected_ok = true
	if not _assert_true(selected_ok, "selected release channel reflected"):
		return 1

	var support = productization.generate_support_report({
		"error_code": "E_FFMPEG_FAILED",
		"context": "phase7_acceptance",
	})
	if not _assert_true(String(support.get("severity", "")) == "high", "support report severity"):
		return 1

	print("AT-007 product-path acceptance passed")
	return 0

func _read_json(path: String) -> Dictionary:
	if path == "" or not FileAccess.file_exists(path):
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(parsed) != TYPE_DICTIONARY:
		return {}
	return parsed

func _assert_true(condition: bool, label: String) -> bool:
	if condition:
		print("[PASS] %s" % label)
		return true
	printerr("[FAIL] %s" % label)
	return false
