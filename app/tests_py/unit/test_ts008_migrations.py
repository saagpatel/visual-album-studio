from vas_studio import Db, MigrationRunner


def test_ts008_migration_runner_applies_schema_to_phase7(test_root):
    db = Db(test_root / "out" / "migration.db")
    runner = MigrationRunner(db, test_root / "migrations")
    version = runner.apply()
    assert version >= 9

    assets = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assets'").fetchone()
    assert assets is not None

    ingest_runs = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='analytics_ingest_runs'"
    ).fetchone()
    assert ingest_runs is not None

    ui_prefs = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='ui_preferences'"
    ).fetchone()
    assert ui_prefs is not None

    command_history = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='command_history'"
    ).fetchone()
    assert command_history is not None

    checksum_row = db.execute("SELECT checksum FROM schema_migrations WHERE version = 9").fetchone()
    assert checksum_row is not None
    assert len(checksum_row["checksum"]) == 64

    model_registry_cols = db.execute("PRAGMA table_info(model_registry)").fetchall()
    col_names = {row["name"] for row in model_registry_cols}
    assert "license_spdx" in col_names
    assert "provenance_json" in col_names
    assert "status" in col_names
    assert "replaced_by_model_id" in col_names
    assert "updated_at" in col_names

    eval_runs = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='model_eval_runs'"
    ).fetchone()
    assert eval_runs is not None

    mode_contract_versions = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='mode_contract_versions'"
    ).fetchone()
    assert mode_contract_versions is not None


def test_ts008_migration_runner_transitions_6_to_latest(test_root):
    db = Db(test_root / "out" / "migration_6_to_7.db")
    runner = MigrationRunner(db, test_root / "migrations")
    version6 = runner.apply(max_version=6)
    assert version6 == 6

    version9 = runner.apply()
    assert version9 >= 9

    release_profiles = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='release_profiles'"
    ).fetchone()
    assert release_profiles is not None
