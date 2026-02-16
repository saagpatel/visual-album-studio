from vas_studio import Db, MigrationRunner


def test_ts008_migration_runner_applies_schema(test_root):
    db = Db(test_root / "out" / "migration.db")
    runner = MigrationRunner(db, test_root / "migrations")
    version = runner.apply()
    assert version >= 6

    assets = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assets'").fetchone()
    assert assets is not None

    ingest_runs = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='analytics_ingest_runs'"
    ).fetchone()
    assert ingest_runs is not None
