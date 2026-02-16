import hashlib
import re
import sqlite3
import time
from pathlib import Path
from typing import Iterable, Optional

from .errors import VasError


_MIGRATION_RE = re.compile(r"^(\d+)_.*\.sql$")


class Db:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL;")

    def close(self) -> None:
        self.conn.close()

    def execute(self, sql: str, params: tuple = ()):
        return self.conn.execute(sql, params)

    def executemany(self, sql: str, seq):
        return self.conn.executemany(sql, seq)

    def commit(self) -> None:
        self.conn.commit()


class MigrationRunner:
    def __init__(self, db: Db, migrations_dir: Path):
        self.db = db
        self.migrations_dir = migrations_dir

    def _list_migrations(self) -> Iterable[tuple[int, Path]]:
        files = []
        for path in sorted(self.migrations_dir.glob("*.sql")):
            match = _MIGRATION_RE.match(path.name)
            if not match:
                continue
            files.append((int(match.group(1)), path))
        return files

    def _ensure_table(self) -> None:
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
              version INTEGER PRIMARY KEY,
              name TEXT NOT NULL,
              checksum TEXT NOT NULL,
              applied_at INTEGER NOT NULL
            )
            """
        )
        self.db.commit()

    def current_version(self) -> int:
        self._ensure_table()
        row = self.db.execute("SELECT COALESCE(MAX(version), 0) AS v FROM schema_migrations").fetchone()
        return int(row["v"]) if row else 0

    def apply(self, max_version: Optional[int] = None) -> int:
        self._ensure_table()
        cur_version = self.current_version()

        for version, path in self._list_migrations():
            if version <= cur_version:
                continue
            if max_version is not None and version > max_version:
                continue

            sql = path.read_text(encoding="utf-8")
            checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()

            try:
                self.db.conn.execute("BEGIN")
                self.db.conn.executescript(sql)
                self.db.execute(
                    "INSERT INTO schema_migrations(version, name, checksum, applied_at) VALUES (?, ?, ?, ?)",
                    (version, path.name, checksum, int(time.time())),
                )
                self.db.conn.execute("COMMIT")
            except Exception as exc:
                self.db.conn.execute("ROLLBACK")
                raise VasError(
                    code="E_MIGRATION_FAILED",
                    message=f"Failed to apply migration {path.name}",
                    details={"migration": path.name, "error": str(exc)},
                    recoverable=False,
                    hint="Inspect migration SQL and DB compatibility",
                ) from exc

        return self.current_version()
