import json
import subprocess  # nosec B404
import time
from pathlib import Path

from .errors import VasError


class AnalysisService:
    def __init__(self, db, worker_cmd: list[str]):
        self.db = db
        self.worker_cmd = worker_cmd

    def request_analysis(self, audio_asset_id: str, analysis_profile_id: str, analysis_version: str, audio_path: Path) -> str:
        asset = self.db.execute("SELECT sha256 FROM assets WHERE id = ?", (audio_asset_id,)).fetchone()
        if not asset:
            raise VasError("E_ASSET_NOT_FOUND", f"Asset {audio_asset_id} not found")

        existing = self.db.execute(
            """
            SELECT id FROM analysis_cache
            WHERE audio_sha256 = ? AND analysis_profile_id = ? AND analysis_version = ?
            """,
            (asset["sha256"], analysis_profile_id, analysis_version),
        ).fetchone()
        if existing:
            return existing["id"]

        worker_cmd = self._validated_worker_cmd()
        req = {"audio_path": str(audio_path)}
        proc = subprocess.Popen(
            worker_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )  # nosec B603
        if proc.stdin is None or proc.stdout is None:
            proc.terminate()
            raise VasError("E_WORKER_UNAVAILABLE", "Analysis worker stream setup failed")
        proc.stdin.write(json.dumps(req) + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline().strip()
        proc.terminate()
        proc.wait(timeout=5)

        if not line:
            raise VasError("E_WORKER_UNAVAILABLE", "Analysis worker returned no result")

        result = json.loads(line)
        cache_id = f"analysis_{audio_asset_id}_{analysis_version}"
        now = int(time.time())
        self.db.execute(
            """
            INSERT INTO analysis_cache(
              id, audio_asset_id, audio_sha256, analysis_profile_id, analysis_version,
              tempo_bpm, beat_times_json, summary_json, created_at, computed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cache_id,
                audio_asset_id,
                asset["sha256"],
                analysis_profile_id,
                analysis_version,
                float(result.get("tempo_bpm", 0.0)),
                json.dumps(result.get("beat_times_sec", [])),
                json.dumps({"duration_sec": result.get("duration_sec", 0.0)}),
                now,
                now,
            ),
        )
        self.db.commit()
        return cache_id

    def _validated_worker_cmd(self) -> list[str]:
        if not isinstance(self.worker_cmd, list) or not self.worker_cmd:
            raise VasError("E_WORKER_CMD_INVALID", "Analysis worker command is not configured")
        sanitized: list[str] = []
        for item in self.worker_cmd:
            if not isinstance(item, str) or not item.strip():
                raise VasError("E_WORKER_CMD_INVALID", "Analysis worker command contains an invalid token")
            sanitized.append(item.strip())
        return sanitized

    def get_analysis(self, audio_asset_id: str, analysis_version: str):
        return self.db.execute(
            "SELECT * FROM analysis_cache WHERE audio_asset_id = ? AND analysis_version = ?",
            (audio_asset_id, analysis_version),
        ).fetchone()
