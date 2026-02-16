from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VasPaths:
    root: Path

    @property
    def out_dir(self) -> Path:
        return self.root / "out"

    @property
    def tmp_dir(self) -> Path:
        return self.out_dir / "tmp"

    @property
    def exports_dir(self) -> Path:
        return self.out_dir / "exports"

    @property
    def cache_dir(self) -> Path:
        return self.out_dir / "cache"

    @property
    def library_dir(self) -> Path:
        return self.out_dir / "library"

    @property
    def db_path(self) -> Path:
        return self.out_dir / "vas.db"

    @property
    def migrations_dir(self) -> Path:
        return self.root / "migrations"

    def ensure(self) -> None:
        for p in [self.out_dir, self.tmp_dir, self.exports_dir, self.cache_dir, self.library_dir]:
            p.mkdir(parents=True, exist_ok=True)
