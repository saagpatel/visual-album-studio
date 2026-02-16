extends RefCounted
class_name LandscapePresets

static func list() -> Array:
	return [
		{"id": "ls_preset_01", "mode_id": "landscape", "name": "Dawn Ridge", "params": {"ls.color.grade_preset": "warm", "ls.terrain.displacement_amount": 1.2}},
		{"id": "ls_preset_02", "mode_id": "landscape", "name": "Night Plane", "params": {"ls.color.grade_preset": "cool", "ls.atmos.fog_density": 0.35}},
		{"id": "ls_preset_03", "mode_id": "landscape", "name": "Steel Horizon", "params": {"ls.color.grade_preset": "mono", "ls.camera.path": "flyover"}},
	]
