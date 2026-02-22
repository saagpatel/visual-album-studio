extends SceneTree

const PublishService = preload("res://src/core/publish_service.gd")
const YouTubeApiAdapter = preload("res://src/adapters/youtube_api_adapter.gd")

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

	var upload_file = tmp_dir.path_join("upload.bin")
	var upload_data = PackedByteArray()
	upload_data.resize(4096)
	var upload_writer = FileAccess.open(upload_file, FileAccess.WRITE)
	if upload_writer == null:
		printerr("[FAIL] unable to create upload fixture")
		return 1
	upload_writer.store_buffer(upload_data)
	upload_writer.close()

	var mock_adapter = YouTubeApiAdapter.new("python3", "scripts/youtube_adapter.py", "", true)
	var publish_runtime = PublishService.new(mock_adapter)
	var started = publish_runtime.start_upload_session(
		upload_file,
		{
			"title": "Acceptance Upload",
			"quota_budget": 500,
			"quota_used": 0,
			"with_thumbnail": true,
			"with_playlist": false,
		},
		"ch_A",
		"ch_A"
	)
	if not _assert_true(bool(started.get("ok", false)), "publish session start"):
		return 1
	var start_data: Dictionary = started.get("data", {})
	if not _assert_true(start_data.has("session_url"), "adapter envelope includes session_url"):
		return 1

	var resumed = publish_runtime.resume_upload_step(
		String(start_data.get("session_url", "")),
		upload_file,
		0,
		8192
	)
	if not _assert_true(bool(resumed.get("ok", false)), "publish session resume"):
		return 1
	var resume_data: Dictionary = resumed.get("data", {})
	if not _assert_true(bool(resume_data.get("complete", false)), "resume reaches complete state"):
		return 1
	if not _assert_true(String(resume_data.get("video_id", "")).length() > 0, "resume provides video id"):
		return 1

	var finalized = publish_runtime.finalize_upload(
		String(resume_data.get("video_id", "")),
		{"title": "Acceptance Upload"},
		""
	)
	if not _assert_true(bool(finalized.get("ok", false)), "publish finalize metadata"):
		return 1

	print("AT-005 product-path acceptance passed")
	return 0

func _assert_true(condition: bool, label: String) -> bool:
	if condition:
		print("[PASS] %s" % label)
		return true
	printerr("[FAIL] %s" % label)
	return false
