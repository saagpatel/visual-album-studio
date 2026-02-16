extends RefCounted
class_name PhotoAnimator

class ParallaxFrame:
	extends RefCounted
	var t: float
	var x: float
	var y: float
	var zoom: float

	func _init(p_t: float, p_x: float, p_y: float, p_zoom: float) -> void:
		t = p_t
		x = p_x
		y = p_y
		zoom = p_zoom

class ModelManager:
	extends RefCounted
	var models_dir: String

	func _init(p_models_dir: String) -> void:
		models_dir = p_models_dir
		DirAccess.make_dir_recursive_absolute(models_dir)

	func install_from_file(src: String, model_id: String, expected_sha256: String) -> String:
		if not FileAccess.file_exists(src):
			return ""
		var digest = _hash_file(src)
		if digest != expected_sha256:
			return ""
		var target_dir = models_dir.path_join(model_id)
		DirAccess.make_dir_recursive_absolute(target_dir)
		var dst = target_dir.path_join(src.get_file())
		DirAccess.copy_absolute(src, dst)
		var provenance = FileAccess.open(target_dir.path_join("provenance.json"), FileAccess.WRITE)
		if provenance != null:
			provenance.store_string(JSON.stringify({"sha256": digest, "source": src}, "\t"))
			provenance.close()
		return dst

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

static func presets() -> Array:
	return [
		{"id": "ph_preset_01", "mode_id": "photo_animator", "name": "Ken Burns Slow", "params": {"ph.kb.start_zoom": 1.0, "ph.kb.end_zoom": 1.2}},
		{"id": "ph_preset_02", "mode_id": "photo_animator", "name": "Parallax Lift", "params": {"ph.parallax.amount": 0.45, "ph.parallax.layer_count": 4}},
		{"id": "ph_preset_03", "mode_id": "photo_animator", "name": "Poster Push", "params": {"ph.kb.start_zoom": 1.1, "ph.kb.end_zoom": 1.35}},
	]

func tier0_path(duration_sec: float, fps: int, pan_x: float, pan_y: float, start_zoom: float, end_zoom: float) -> Array:
	var frames: Array = []
	var total = int(duration_sec * float(fps))
	if total <= 0:
		return frames
	for i in total:
		var alpha = float(i) / float(max(total - 1, 1))
		frames.append(ParallaxFrame.new(
			float(i) / float(fps),
			pan_x * alpha,
			pan_y * alpha,
			start_zoom + (end_zoom - start_zoom) * alpha
		))
	return frames
