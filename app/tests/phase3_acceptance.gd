extends SceneTree

const FfmpegAdapter = preload("res://src/adapters/ffmpeg_adapter.gd")
const MixerService = preload("res://src/core/mixer_service.gd")

func _init() -> void:
	randomize()
	quit(_run())

func _run() -> int:
	var repo_root = OS.get_environment("VAS_REPO_ROOT")
	if repo_root == "":
		repo_root = ProjectSettings.globalize_path("res://").get_base_dir()
	var out_dir = repo_root.path_join("out/product_phase3")
	DirAccess.make_dir_recursive_absolute(out_dir)

	var ffmpeg = FfmpegAdapter.new("ffmpeg")
	var mixer = MixerService.new(ffmpeg)

	var a = out_dir.path_join("a.wav")
	var b = out_dir.path_join("b.wav")
	var tone_a = ffmpeg.run(PackedStringArray(["-y", "-f", "lavfi", "-i", "sine=frequency=220:sample_rate=48000:duration=2", "-ac", "2", a]))
	var tone_b = ffmpeg.run(PackedStringArray(["-y", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=2", "-ac", "2", b]))
	if not _assert_true(tone_a["ok"] and tone_b["ok"], "source tones generated"):
		return 1

	var pid = "project_mix"
	var t1 = mixer.add_track(pid, a)
	var t2 = mixer.add_track(pid, b)
	mixer.set_track_params(pid, t1, {"volume_db": -1.0})
	mixer.set_track_params(pid, t2, {"volume_db": -2.0})

	var out1 = out_dir.path_join("mix1.wav")
	var out2 = out_dir.path_join("mix2.wav")
	var r1 = mixer.bounce(pid, out1)
	var r2 = mixer.bounce(pid, out2)
	if not _assert_true(not r1.has("error") and not r2.has("error"), "bounce succeeded"):
		return 1

	var h1 = _hash_file(out1)
	var h2 = _hash_file(out2)
	if not _assert_true(String(r1.get("sha256", "")) == h1, "bounce hash recorded 1"):
		return 1
	if not _assert_true(String(r2.get("sha256", "")) == h2, "bounce hash recorded 2"):
		return 1
	if not _assert_true(h1 == h2, "deterministic bounce hash"):
		return 1

	print("AT-003 product-path acceptance passed")
	return 0

func _hash_file(path: String) -> String:
	var file = FileAccess.open(path, FileAccess.READ)
	if file == null:
		return ""
	var hash = HashingContext.new()
	hash.start(HashingContext.HASH_SHA256)
	while not file.eof_reached():
		hash.update(file.get_buffer(1024 * 1024))
	file.close()
	return hash.finish().hex_encode()

func _assert_true(condition: bool, label: String) -> bool:
	if condition:
		print("[PASS] %s" % label)
		return true
	printerr("[FAIL] %s" % label)
	return false
