from vas_studio import Db, MigrationRunner


def test_ts008_migration_runner_applies_schema_to_phase7(test_root):
    db = Db(test_root / "out" / "migration.db")
    runner = MigrationRunner(db, test_root / "migrations")
    version = runner.apply()
    assert version >= 7

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

    checksum_row = db.execute(
        "SELECT checksum FROM schema_migrations WHERE version = 7"
    ).fetchone()
    assert checksum_row is not None
    assert len(checksum_row["checksum"]) == 64


def test_ts008_migration_runner_transitions_6_to_7(test_root):
    db = Db(test_root / "out" / "migration_6_to_7.db")
    runner = MigrationRunner(db, test_root / "migrations")
    version6 = runner.apply(max_version=6)
    assert version6 == 6

    version7 = runner.apply()
    assert version7 >= 7

    release_profiles = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='release_profiles'"
    ).fetchone()
    assert release_profiles is not None
