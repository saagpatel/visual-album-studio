import hashlib

from vas_studio import LANDSCAPE_PRESETS, PARTICLE_PRESETS, PHOTO_PRESETS, ModelManager, PhotoAnimator


def test_at002_phase2_modes_and_photo_tier0(tmp_path):
    assert len(PARTICLE_PRESETS) >= 3
    assert len(LANDSCAPE_PRESETS) >= 3
    assert len(PHOTO_PRESETS) >= 3

    animator = PhotoAnimator()
    path_a = animator.tier0_path(duration_sec=2.0, fps=30, pan_x=0.2, pan_y=0.1, start_zoom=1.0, end_zoom=1.2)
    path_b = animator.tier0_path(duration_sec=2.0, fps=30, pan_x=0.2, pan_y=0.1, start_zoom=1.0, end_zoom=1.2)
    assert [(f.x, f.y, f.zoom) for f in path_a] == [(f.x, f.y, f.zoom) for f in path_b]

    model_src = tmp_path / "model.onnx"
    model_src.write_bytes(b"model-bytes")
    sha = hashlib.sha256(model_src.read_bytes()).hexdigest()
    manager = ModelManager(tmp_path / "models")
    installed = manager.install_from_file(model_src, model_id="depth_v1", expected_sha256=sha)
    assert installed.exists()
