extends RefCounted
class_name ParticlesPresets

static func list() -> Array:
	return [
		{"id": "pt_preset_01", "mode_id": "particles", "name": "Pulse Bloom", "params": {"pt.emission.rate": 1200, "pt.color.beat_flash_amount": 0.8}},
		{"id": "pt_preset_02", "mode_id": "particles", "name": "Nebula Drift", "params": {"pt.emission.rate": 600, "pt.physics.turbulence": 3.2}},
		{"id": "pt_preset_03", "mode_id": "particles", "name": "Mono Burst", "params": {"pt.emission.burst_on_beat": true, "pt.emission.burst_count": 240}},
	]
