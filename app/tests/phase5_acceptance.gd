extends SceneTree

const PublishService = preload("res://src/core/publish_service.gd")

func _init() -> void:
	randomize()
	quit(_run())

func _run() -> int:
	var publish = PublishService.new()
	var pkce = publish.pkce_pair()
	if not _assert_true(String(pkce.get("verifier", "")).length() > 20, "pkce verifier generated"):
		return 1
	if not _assert_true(String(pkce.get("challenge", "")).length() > 20, "pkce challenge generated"):
		return 1

	var repo_root = OS.get_environment("VAS_REPO_ROOT")
	if repo_root == "":
		repo_root = ProjectSettings.globalize_path("res://").get_base_dir()
	var tmp_dir = repo_root.path_join("out/product_phase5")
	DirAccess.make_dir_recursive_absolute(tmp_dir)

	var store = PublishService.ResumableUploadStore.new(tmp_dir.path_join("upload_state.json"))
	var session = PublishService.UploadSession.new("u1", tmp_dir.path_join("video.mp4"), 2000, 1000)
	store.save(session)
	var restored = store.load()
	if not _assert_true(restored != null and restored.bytes_uploaded == 1000, "resumable session roundtrip"):
		return 1

	var guard = PublishService.ChannelBindingGuard.new()
	if not _assert_true(guard.validate("ch_A", "ch_A"), "channel guard positive"):
		return 1
	if not _assert_true(not guard.validate("ch_A", "ch_B"), "channel guard negative"):
		return 1

	var quota = PublishService.QuotaBudget.new(500)
	var est = quota.estimate_publish(true, true)
	if not _assert_true(est == 200, "quota estimate"):
		return 1
	if not _assert_true(quota.can_run(est), "quota first run"):
		return 1
	quota.consume(est)
	quota.consume(est)
	if not _assert_true(not quota.can_run(est), "quota budget exhausted"):
		return 1

	print("AT-005 product-path acceptance passed")
	return 0

func _assert_true(condition: bool, label: String) -> bool:
	if condition:
		print("[PASS] %s" % label)
		return true
	printerr("[FAIL] %s" % label)
	return false
