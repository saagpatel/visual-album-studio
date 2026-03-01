import hashlib

from vas_studio import ModelRegistryServiceV2


def test_itv2_204_model_eval_harness_persists_scores(runtime, test_root):
    models_dir = test_root / "out" / "models"
    registry = ModelRegistryServiceV2(runtime.db, models_dir=models_dir)

    relpath = "stylize_v2/model.bin"
    model_path = models_dir / relpath
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_bytes(b"stylize-v2-model")
    digest = hashlib.sha256(model_path.read_bytes()).hexdigest()

    assert registry.register_candidate(
        model_id="stylize_v2",
        name="Stylize v2",
        version="2.1.0",
        license_name="Apache-2.0",
        license_spdx="Apache-2.0",
        source_url="https://example.com/stylize_v2",
        sha256=digest,
        relpath=relpath,
        size_bytes=model_path.stat().st_size,
    )["ok"]

    assert registry.promote_model("stylize_v2")["ok"]
    record = registry.record_evaluation(
        model_id="stylize_v2",
        fixture_id="fixture-stylize-v2",
        quality_score=0.84,
        perf_fps=54.0,
        safety_score=0.95,
        notes={"run": "itv2_204"},
    )
    assert record["ok"]

    row = runtime.db.execute("SELECT * FROM model_eval_runs WHERE id = ?", (record["id"],)).fetchone()
    assert row is not None
    combined = registry.score_candidate(
        quality_score=float(row["quality_score"]),
        perf_fps=float(row["perf_fps"]),
        safety_score=float(row["safety_score"]),
    )
    assert combined > 0.75
