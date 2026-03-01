from dataclasses import dataclass


@dataclass
class ModePresetV2:
    preset_id: str
    mode_id: str
    name: str
    params: dict


NEXT_GEN_PRESETS = [
    ModePresetV2(
        "ng_preset_01",
        "nebula_waves",
        "Nebula Waves",
        {
            "ng.wave.amplitude": 0.62,
            "ng.wave.frequency": 1.35,
            "ng.color.energy_mix": 0.8,
        },
    ),
    ModePresetV2(
        "ng_preset_02",
        "pulse_mesh",
        "Pulse Mesh",
        {
            "ng.mesh.displacement": 0.38,
            "ng.mesh.edge_glow": 0.58,
            "ng.beat.response": 0.74,
        },
    ),
]
