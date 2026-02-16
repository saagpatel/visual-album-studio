from vas_studio import Db, MigrationRunner


def test_ts008_migration_runner_applies_schema(test_root):
    db = Db(test_root / "out" / "migration.db")
    runner = MigrationRunner(db, test_root / "migrations")
    version = runner.apply(max_version=1)
    assert version >= 1

    row = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assets'").fetchone()
    assert row is not None
