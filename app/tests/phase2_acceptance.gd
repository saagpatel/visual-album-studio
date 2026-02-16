extends SceneTree

const ParticlesPresets = preload("res://src/modes/particles/presets.gd")
const LandscapePresets = preload("res://src/modes/landscape/presets.gd")
const PhotoAnimator = preload("res://src/modes/photo_animator/photo_animator.gd")

func _init() -> void:
	randomize()
	quit(_run())

func _run() -> int:
	var particle_presets: Array = ParticlesPresets.list()
	var landscape_presets: Array = LandscapePresets.list()
	var photo_presets: Array = PhotoAnimator.presets()

	if not _assert_true(particle_presets.size() >= 3, "particles presets >= 3"):
		return 1
	if not _assert_true(landscape_presets.size() >= 3, "landscape presets >= 3"):
		return 1
	if not _assert_true(photo_presets.size() >= 3, "photo presets >= 3"):
		return 1

	var animator = PhotoAnimator.new()
	var path_a: Array = animator.tier0_path(2.0, 30, 0.2, 0.1, 1.0, 1.2)
	var path_b: Array = animator.tier0_path(2.0, 30, 0.2, 0.1, 1.0, 1.2)
	if not _assert_true(path_a.size() == path_b.size(), "tier0 path size parity"):
		return 1

	for i in path_a.size():
		var a = path_a[i]
		var b = path_b[i]
		if not _assert_true(is_equal_approx(a.x, b.x) and is_equal_approx(a.y, b.y) and is_equal_approx(a.zoom, b.zoom), "tier0 deterministic frame %d" % i):
			return 1

	var repo_root = OS.get_environment("VAS_REPO_ROOT")
	if repo_root == "":
		repo_root = ProjectSettings.globalize_path("res://").get_base_dir()
	var tmp_dir = repo_root.path_join("out/product_phase2")
	DirAccess.make_dir_recursive_absolute(tmp_dir)
	var model_src = tmp_dir.path_join("model.onnx")
	var model_file = FileAccess.open(model_src, FileAccess.WRITE)
	model_file.store_string("model-bytes")
	model_file.close()

	var sha = _hash_file(model_src)
	var manager = PhotoAnimator.ModelManager.new(tmp_dir.path_join("models"))
	var installed = manager.install_from_file(model_src, "depth_v1", sha)
	if not _assert_true(installed != "" and FileAccess.file_exists(installed), "model install with checksum"):
		return 1

	print("AT-002 product-path acceptance passed")
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
