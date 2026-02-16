from __future__ import annotations

import json
import time
from pathlib import Path

from .analysis_service import AnalysisService
from .asset_service import AssetService
from .config import VasPaths
from .db import Db, MigrationRunner
from .export_service import ExportService
from .ffmpeg_adapter import FFmpegAdapter
from .ids import new_id


DEFAULT_MAPPING_DSL = """
mp.motion.float_amp = clamp(20 + sin(time_sec) * 5, 0, 80)
mp.beat.pulse_amount = clamp(0.4 + beat_phase * 0.3, 0, 1)
""".strip()

DEFAULT_TEMPLATE = {
    "schema_version": 1,
    "name": "Default Template",
    "metadata": {
        "title": "{project.title} — Visual Album",
        "description": "Track: {project.title}\\nBPM: {audio.bpm}\\n\\n{provenance.attribution_block}",
        "tags": ["visual album", "{project.genre}"],
        "categoryId": "10",
        "privacyStatus": "private",
        "publishAt": None,
        "chapters": [],
        "playlistIds": [],
    },
    "visual_defaults": {
        "mode_id": "motion_poster",
        "preset_id": "mp_preset_01",
        "seed_strategy": "project_seed",
    },
}


class Phase1Runtime:
    def __init__(self, root: Path, worker_cmd: list[str] | None = None):
        self.paths = VasPaths(root=root)
        self.paths.ensure()

        self.db = Db(self.paths.db_path)
        self.migrations = MigrationRunner(self.db, self.paths.migrations_dir)
        self.ffmpeg = FFmpegAdapter("ffmpeg")
        self.assets = AssetService(self.db, self.paths.library_dir, ffmpeg_bin="ffmpeg")
        cmd = worker_cmd or [str((root / "worker/.venv/bin/python").resolve()), "-m", "vas_audio_worker.cli"]
        self.analysis = AnalysisService(self.db, cmd)
        self.exporter = ExportService(self.db, self.paths, self.ffmpeg, self.assets)

    def setup(self) -> None:
        self.migrations.apply(max_version=1)
        now = int(time.time())

        self.db.execute(
            "INSERT OR IGNORE INTO analysis_profiles(id, name, sample_rate_hz, hop_length, algorithm_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("analysis_default", "Default", 48000, 512, json.dumps({"algorithm": "baseline"}), now),
        )
        self.db.execute(
            "INSERT OR IGNORE INTO mapping_schemas(version, name, created_at) VALUES (1, 'v1', ?)",
            (now,),
        )
        self.db.execute(
            "INSERT OR IGNORE INTO preset_schemas(version, name, created_at) VALUES (1, 'v1', ?)",
            (now,),
        )
        self.db.execute(
            "INSERT OR IGNORE INTO template_schemas(version, name, created_at) VALUES (1, 'v1', ?)",
            (now,),
        )

        mapping_id = "mapping_motion_poster_default"
        self.db.execute(
            """
            INSERT OR IGNORE INTO mappings(id, name, schema_version, dsl_text, compiled_json, created_at, updated_at)
            VALUES (?, ?, 1, ?, ?, ?, ?)
            """,
            (mapping_id, "Motion Poster Default", DEFAULT_MAPPING_DSL, json.dumps({"compiled": True}), now, now),
        )

        self.db.execute(
            """
            INSERT OR IGNORE INTO presets(id, mode_id, name, schema_version, mapping_id, seed, overrides_json, created_at, updated_at)
            VALUES (?, 'motion_poster', 'Noir Pulse', 1, ?, 101, '{}', ?, ?)
            """,
            ("mp_preset_01", mapping_id, now, now),
        )

        self.db.execute(
            """
            INSERT OR IGNORE INTO templates(id, name, schema_version, template_json, created_at, updated_at)
            VALUES (?, ?, 1, ?, ?, ?)
            """,
            (
                "template_default",
                "Default Template",
                json.dumps(DEFAULT_TEMPLATE),
                now,
                now,
            ),
        )
        self.db.commit()

    def create_project(self, *, name: str, duration_sec: int, fps: int = 30, width: int = 1920, height: int = 1080) -> str:
        project_id = new_id("project")
        now = int(time.time())
        self.db.execute(
            """
            INSERT INTO projects(
              id, name, slug, created_at, updated_at, visual_mode, preset_id, mapping_id,
              template_id, seed, fps, width, height, duration_frames, settings_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                name,
                name.lower().replace(" ", "-"),
                now,
                now,
                "motion_poster",
                "mp_preset_01",
                "mapping_motion_poster_default",
                "template_default",
                101,
                fps,
                width,
                height,
                duration_sec * fps,
                "{}",
            ),
        )
        self.db.commit()
        return project_id

    def export_project(self, *, project_id: str, audio_asset_id: str, draft: bool, simulate_only: bool = False):
        project_row = self.db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        project = dict(project_row)

        analysis_cache_id = self.analysis.request_analysis(
            audio_asset_id=audio_asset_id,
            analysis_profile_id="analysis_default",
            analysis_version="phase1-v1",
            audio_path=self.paths.out_dir / self.db.execute("SELECT library_relpath FROM assets WHERE id = ?", (audio_asset_id,)).fetchone()["library_relpath"],
        )
        analysis_row = self.db.execute("SELECT * FROM analysis_cache WHERE id = ?", (analysis_cache_id,)).fetchone()
        analysis = {
            "tempo_bpm": analysis_row["tempo_bpm"],
            "analysis_version": analysis_row["analysis_version"],
        }

        tmpl_row = self.db.execute("SELECT template_json FROM templates WHERE id = ?", (project["template_id"],)).fetchone()
        template = json.loads(tmpl_row["template_json"])

        return self.exporter.export_project(
            project=project,
            audio_asset_id=audio_asset_id,
            analysis=analysis,
            template=template,
            draft=draft,
            simulate_only=simulate_only,
        )
