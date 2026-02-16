import hashlib
import json
import math
import shutil
import time
from pathlib import Path
from typing import Dict, List

from .errors import VasError
from .ffmpeg_adapter import FFmpegAdapter
from .ids import new_id
from .template_service import TemplateService


class ExportService:
    def __init__(self, db, paths, ffmpeg: FFmpegAdapter, asset_service):
        self.db = db
        self.paths = paths
        self.ffmpeg = ffmpeg
        self.asset_service = asset_service
        self.template_service = TemplateService()

    @staticmethod
    def plan_segments(total_frames: int, segment_frames: int) -> List[dict]:
        segments = []
        i = 0
        while i * segment_frames < total_frames:
            start_frame = i * segment_frames
            frame_count = min(segment_frames, total_frames - start_frame)
            segments.append({"index": i, "start_frame": start_frame, "frame_count": frame_count})
            i += 1
        return segments

    def _write_json(self, path: Path, payload: dict) -> None:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _hash_file(self, path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def _checkpoint_hash(self, video_path: Path, fps: int, frame_index: int) -> str:
        tmp_png = self.paths.tmp_dir / f"checkpoint_{frame_index}.png"
        time_sec = frame_index / fps
        args = [
            "-y",
            "-ss",
            f"{time_sec:.6f}",
            "-i",
            str(video_path),
            "-vframes",
            "1",
            str(tmp_png),
        ]
        self.ffmpeg.run(args)
        digest = self._hash_file(tmp_png)
        tmp_png.unlink(missing_ok=True)
        return digest

    def export_project(
        self,
        *,
        project: Dict,
        audio_asset_id: str,
        analysis: Dict,
        template: Dict,
        draft: bool,
        simulate_only: bool = False,
    ) -> Dict:
        allowed, reason = self.asset_service.validate_production_allowed(audio_asset_id)
        if not draft and not allowed:
            raise VasError("E_LICENSE_INCOMPLETE", reason, recoverable=True)

        export_id = new_id("export")
        job_id = new_id("job")

        fps = int(project["fps"])
        width = int(project["width"])
        height = int(project["height"])
        duration_frames = int(project["duration_frames"])
        segment_frames = fps * 60
        segments = self.plan_segments(duration_frames, segment_frames)

        workspace = self.paths.tmp_dir / "jobs" / job_id
        seg_dir = workspace / "segments"
        concat_dir = workspace / "concat"
        final_dir = workspace / "final"
        bundle_tmp = self.paths.exports_dir / f"{export_id}.tmp"
        bundle_dir = self.paths.exports_dir / export_id

        for p in [seg_dir, concat_dir, final_dir, bundle_tmp]:
            p.mkdir(parents=True, exist_ok=True)

        manifest = {
            "job_id": job_id,
            "project_id": project["id"],
            "export_id": export_id,
            "segments": segments,
            "fps": fps,
            "resolution": [width, height],
            "created_at": int(time.time()),
        }
        self._write_json(workspace / "job_manifest.json", manifest)

        audio_rel = self.db.execute("SELECT library_relpath, sha256 FROM assets WHERE id = ?", (audio_asset_id,)).fetchone()
        if not audio_rel:
            raise VasError("E_ASSET_NOT_FOUND", f"Missing audio asset {audio_asset_id}")
        audio_path = self.paths.out_dir / audio_rel["library_relpath"]

        seg_mp4s = []
        encoder = self.ffmpeg.preferred_h264_encoder()
        if not simulate_only:
            for seg in segments:
                idx = seg["index"]
                seg_path = seg_dir / f"{idx:03d}"
                seg_path.mkdir(parents=True, exist_ok=True)
                seg_mp4 = seg_path / "segment.mp4"
                start_sec = seg["start_frame"] / fps
                dur_sec = seg["frame_count"] / fps

                args = [
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    f"color=c=black:s={width}x{height}:r={fps}",
                    "-ss",
                    f"{start_sec:.6f}",
                    "-t",
                    f"{dur_sec:.6f}",
                    "-i",
                    str(audio_path),
                    "-c:v",
                    encoder,
                    "-pix_fmt",
                    "yuv420p",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "192k",
                    "-shortest",
                    "-movflags",
                    "+faststart",
                    str(seg_mp4),
                ]
                self.ffmpeg.run(args)
                seg_hash = self._hash_file(seg_mp4)
                self._write_json(
                    seg_path / "segment.manifest.json",
                    {"index": idx, "start_frame": seg["start_frame"], "frame_count": seg["frame_count"], "sha256": seg_hash},
                )
                seg_mp4s.append(seg_mp4)

            concat_list = concat_dir / "concat_list.txt"
            concat_list.write_text(
                "\n".join([f"file '{p.resolve()}'" for p in seg_mp4s]) + "\n",
                encoding="utf-8",
            )
            final_video = final_dir / "video.mp4"
            self.ffmpeg.run(
                [
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(concat_list),
                    "-c",
                    "copy",
                    str(final_video),
                ]
            )

            thumb = final_dir / "thumbnail.png"
            self.ffmpeg.run(["-y", "-ss", "0", "-i", str(final_video), "-vframes", "1", "-vf", "scale=1280:720", str(thumb)])

            if thumb.stat().st_size > 2_000_000:
                self.ffmpeg.run(["-y", "-i", str(thumb), "-vf", "scale=1280:720", "-compression_level", "9", str(thumb)])

            checkpoint_frames = [0, min(duration_frames - 1, 900), min(duration_frames - 1, 1800)] if duration_frames > 0 else [0]
            checkpoints = {str(f): self._checkpoint_hash(final_video, fps, f) for f in checkpoint_frames}
        else:
            final_video = final_dir / "video.mp4"
            final_video.write_bytes(b"SIMULATED")
            thumb = final_dir / "thumbnail.png"
            thumb.write_bytes(b"SIMULATED")
            checkpoints = {"0": hashlib.sha256(b"SIMULATED").hexdigest()}

        provenance = self.asset_service.provenance_json(
            audio_asset_id,
            template_id=project["template_id"],
            preset_id=project["preset_id"],
            mapping_id=project["mapping_id"],
            seed=int(project["seed"]),
        )

        duration_hms = f"{duration_frames / fps:.3f}s"
        metadata = self.template_service.render_metadata(
            template=template,
            project=project,
            audio={"tempo_bpm": analysis.get("tempo_bpm", 0), "duration_sec": duration_frames / fps},
            export={"fps": fps, "width": width, "height": height, "duration_hms": duration_hms},
            attribution_block=provenance.get("attribution_block", ""),
        )

        build_manifest = {
            "schema_version": 1,
            "toolchain": {
                "godot_version": "4.4.x",
                "render_graph_hash": hashlib.sha256(f"{project['visual_mode']}:{project['preset_id']}".encode()).hexdigest(),
                "ffmpeg_version": self.ffmpeg.ffmpeg_version(),
                "ffmpeg_license_mode": "lgpl",
                "analysis_worker_version": analysis.get("analysis_version", "phase1"),
            },
            "snapshot": {
                "export_id": export_id,
                "project_id": project["id"],
                "inputs": {
                    "audio_asset_id": audio_asset_id,
                    "audio_sha256": audio_rel["sha256"],
                    "album_art_asset_id": project.get("album_art_asset_id", ""),
                    "album_art_sha256": project.get("album_art_sha256", ""),
                    "fonts": [],
                },
                "preset_id": project["preset_id"],
                "mapping_id": project["mapping_id"],
                "template_id": project["template_id"],
                "seed": int(project["seed"]),
                "fps": fps,
                "width": width,
                "height": height,
                "duration_frames": duration_frames,
                "segment_plan": {
                    "segment_frames": segment_frames,
                    "segments": segments,
                },
                "checkpoints": checkpoints,
            },
            "outputs": {
                "video": {"container": "mp4", "codec": "h264", "encoder": encoder, "settings": {}},
                "audio": {"codec": "aac", "bitrate": 192000},
                "thumbnail": {"width": 1280, "height": 720, "time_sec": 0.0},
            },
        }

        for src, dst_name in [
            (final_video, "video.mp4"),
            (thumb, "thumbnail.png"),
        ]:
            shutil.copy2(src, bundle_tmp / dst_name)

        self._write_json(bundle_tmp / "metadata.json", metadata)
        self._write_json(bundle_tmp / "provenance.json", provenance)
        self._write_json(bundle_tmp / "build_manifest.json", build_manifest)

        if bundle_dir.exists():
            shutil.rmtree(bundle_dir)
        bundle_tmp.rename(bundle_dir)

        self.db.execute(
            """
            INSERT INTO exports(
              id, job_id, project_id, created_at, bundle_relpath, video_relpath,
              thumbnail_relpath, metadata_relpath, provenance_relpath, build_manifest_relpath
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                export_id,
                job_id,
                project["id"],
                int(time.time()),
                str(bundle_dir.relative_to(self.paths.root)),
                str((bundle_dir / "video.mp4").relative_to(self.paths.root)),
                str((bundle_dir / "thumbnail.png").relative_to(self.paths.root)),
                str((bundle_dir / "metadata.json").relative_to(self.paths.root)),
                str((bundle_dir / "provenance.json").relative_to(self.paths.root)),
                str((bundle_dir / "build_manifest.json").relative_to(self.paths.root)),
            ),
        )
        self.db.commit()

        return {
            "export_id": export_id,
            "job_id": job_id,
            "bundle_dir": str(bundle_dir),
            "checkpoints": checkpoints,
            "segments": segments,
        }
