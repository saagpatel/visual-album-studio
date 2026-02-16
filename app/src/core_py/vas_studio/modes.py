from dataclasses import dataclass


@dataclass
class ModePreset:
    preset_id: str
    mode_id: str
    name: str
    params: dict


PARTICLE_PRESETS = [
    ModePreset("pt_preset_01", "particles", "Pulse Bloom", {"pt.emission.rate": 1200, "pt.color.beat_flash_amount": 0.8}),
    ModePreset("pt_preset_02", "particles", "Nebula Drift", {"pt.emission.rate": 600, "pt.physics.turbulence": 3.2}),
    ModePreset("pt_preset_03", "particles", "Mono Burst", {"pt.emission.burst_on_beat": True, "pt.emission.burst_count": 240}),
]

LANDSCAPE_PRESETS = [
    ModePreset("ls_preset_01", "landscape", "Dawn Ridge", {"ls.color.grade_preset": "warm", "ls.terrain.displacement_amount": 1.2}),
    ModePreset("ls_preset_02", "landscape", "Night Plane", {"ls.color.grade_preset": "cool", "ls.atmos.fog_density": 0.35}),
    ModePreset("ls_preset_03", "landscape", "Steel Horizon", {"ls.color.grade_preset": "mono", "ls.camera.path": "flyover"}),
]

PHOTO_PRESETS = [
    ModePreset("ph_preset_01", "photo_animator", "Ken Burns Slow", {"ph.kb.start_zoom": 1.0, "ph.kb.end_zoom": 1.2}),
    ModePreset("ph_preset_02", "photo_animator", "Parallax Lift", {"ph.parallax.amount": 0.45, "ph.parallax.layer_count": 4}),
    ModePreset("ph_preset_03", "photo_animator", "Poster Push", {"ph.kb.start_zoom": 1.1, "ph.kb.end_zoom": 1.35}),
]
