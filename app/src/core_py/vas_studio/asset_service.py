import hashlib
import json
import subprocess  # nosec B404
import shutil
import time
from pathlib import Path
from typing import Optional

from .errors import VasError
from .ids import new_id


AUDIO_EXTS = {".wav", ".mp3", ".flac", ".m4a", ".aac", ".aiff", ".aif"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
FONT_EXTS = {".ttf", ".otf"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def kind_from_path(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in AUDIO_EXTS:
        return "audio"
    if ext in IMAGE_EXTS:
        return "image"
    if ext in FONT_EXTS:
        return "font"
    return "other"


class AssetService:
    def __init__(self, db, library_dir: Path, ffmpeg_bin: str = "ffmpeg"):
        self.db = db
        self.library_dir = library_dir
        self.ffmpeg_bin = ffmpeg_bin

    def _target_path(self, kind: str, sha256: str, src_path: Path) -> Path:
        subdir = {
            "audio": "audio_src",
            "image": "images",
            "font": "fonts",
            "other": "other",
        }.get(kind, "other")
        p = self.library_dir / subdir / sha256[:2]
        p.mkdir(parents=True, exist_ok=True)
        ext = src_path.suffix.lower() or ".bin"
        return p / f"{sha256}{ext}"

    def _canonical_audio_path(self, sha256: str) -> Path:
        p = self.library_dir / "audio" / sha256[:2]
        p.mkdir(parents=True, exist_ok=True)
        return p / f"{sha256}.wav"

    def _decode_canonical_audio(self, src: Path, dst: Path) -> None:
        ffmpeg_bin = str(self.ffmpeg_bin).strip()
        if not ffmpeg_bin:
            raise VasError("E_FFMPEG_FAILED", "ffmpeg binary is not configured")
        result = subprocess.run(
            [
                ffmpeg_bin,
                "-y",
                "-i",
                str(src),
                "-vn",
                "-ac",
                "2",
                "-ar",
                "48000",
                "-sample_fmt",
                "s16",
                str(dst),
            ],
            capture_output=True,
            text=True,
            check=False,
        )  # nosec B603
        if result.returncode != 0:
            raise VasError(
                "E_FFMPEG_FAILED",
                "Failed to decode canonical WAV",
                details={"stderr": result.stderr[-2000:], "src": str(src)},
                recoverable=True,
                hint="Verify ffmpeg installation and source audio format",
            )

    def import_asset(self, src: Path) -> str:
        if not src.exists():
            raise VasError("E_ASSET_NOT_FOUND", f"Asset not found: {src}")

        kind = kind_from_path(src)
        source_digest = sha256_file(src)

        stored_digest = source_digest

        if kind == "audio":
            canonical = self._canonical_audio_path(source_digest)
            if not canonical.exists():
                self._decode_canonical_audio(src, canonical)
            stored_digest = sha256_file(canonical)
            existing = self.db.execute(
                "SELECT id FROM assets WHERE sha256 = ? AND kind = ?",
                (stored_digest, kind),
            ).fetchone()
            if existing:
                return existing["id"]
        else:
            existing = self.db.execute(
                "SELECT id FROM assets WHERE sha256 = ? AND kind = ?", (stored_digest, kind)
            ).fetchone()
            if existing:
                return existing["id"]

        dst = self._target_path(kind, source_digest, src)
        if not dst.exists():
            shutil.copy2(src, dst)

        library_relpath = dst
        if kind == "audio":
            canonical = self._canonical_audio_path(source_digest)
            if not canonical.exists():
                self._decode_canonical_audio(src, canonical)
            library_relpath = canonical

        asset_id = new_id("asset")
        now = int(time.time())
        self.db.execute(
            """
            INSERT INTO assets(
              id, kind, sha256, size_bytes, original_path, library_relpath,
              mime_type, created_at, imported_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                asset_id,
                kind,
                stored_digest,
                src.stat().st_size,
                str(src),
                str(library_relpath.relative_to(self.library_dir.parent)),
                "",
                now,
                now,
                "{}",
            ),
        )

        self.db.execute(
            """
            INSERT INTO asset_license(asset_id, source_type, is_production_allowed, updated_at)
            VALUES (?, 'unknown', 0, ?)
            """,
            (asset_id, now),
        )
        self.db.commit()
        return asset_id

    def set_license(
        self,
        asset_id: str,
        *,
        source_type: str,
        license_name: Optional[str] = None,
        license_url: Optional[str] = None,
        attribution_text: Optional[str] = None,
        proof_relpath: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> None:
        now = int(time.time())
        allowed = source_type != "unknown" and bool(license_name or license_url)
        self.db.execute(
            """
            UPDATE asset_license
            SET source_type = ?, license_name = ?, license_url = ?, attribution_text = ?,
                proof_relpath = ?, notes = ?, is_production_allowed = ?, updated_at = ?
            WHERE asset_id = ?
            """,
            (
                source_type,
                license_name,
                license_url,
                attribution_text,
                proof_relpath,
                notes,
                1 if allowed else 0,
                now,
                asset_id,
            ),
        )
        self.db.commit()

    def validate_production_allowed(self, asset_id: str) -> tuple[bool, str]:
        row = self.db.execute(
            "SELECT source_type, license_name, license_url, is_production_allowed FROM asset_license WHERE asset_id = ?",
            (asset_id,),
        ).fetchone()
        if not row:
            return False, "Missing license metadata"
        if row["source_type"] == "unknown":
            return False, "Audio source_type is unknown"
        if not row["license_name"] and not row["license_url"]:
            return False, "Audio license_name or license_url is required"
        if int(row["is_production_allowed"]) != 1:
            return False, "Audio not marked production allowed"
        return True, "ok"

    def verify_integrity(self, asset_id: str) -> bool:
        row = self.db.execute("SELECT sha256, library_relpath FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if not row:
            raise VasError("E_ASSET_NOT_FOUND", f"Asset {asset_id} not found")
        path = self.library_dir.parent / row["library_relpath"]
        if not path.exists():
            return False
        return sha256_file(path) == row["sha256"]

    def provenance_json(self, asset_id: str, template_id: str, preset_id: str, mapping_id: str, seed: int) -> dict:
        a = self.db.execute(
            "SELECT id, sha256 FROM assets WHERE id = ?", (asset_id,)
        ).fetchone()
        l = self.db.execute(
            "SELECT source_type, license_name, license_url, attribution_text, proof_relpath, notes FROM asset_license WHERE asset_id = ?",
            (asset_id,),
        ).fetchone()
        proof = []
        if l and l["proof_relpath"]:
            proof.append({"type": "file", "value": l["proof_relpath"]})
        attribution = l["attribution_text"] if l and l["attribution_text"] else ""
        return {
            "schema_version": 1,
            "audio": {
                "asset_id": a["id"] if a else asset_id,
                "sha256": a["sha256"] if a else "",
                "source_type": l["source_type"] if l else "unknown",
                "license_name": l["license_name"] if l else None,
                "license_url": l["license_url"] if l else None,
                "attribution_text": l["attribution_text"] if l else None,
                "proof": proof,
                "notes": l["notes"] if l else None,
            },
            "originality_ledger": {
                "template_id": template_id,
                "preset_id": preset_id,
                "mapping_id": mapping_id,
                "seed": seed,
                "notable_changes": [],
                "user_notes": None,
            },
            "attribution_block": attribution,
        }
