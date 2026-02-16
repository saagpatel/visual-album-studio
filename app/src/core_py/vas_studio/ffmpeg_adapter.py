import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, Optional

from .errors import VasError


@dataclass
class FfmpegProgress:
    frame: int = 0
    out_time_ms: int = 0
    progress: str = "continue"


class FFmpegAdapter:
    def __init__(self, ffmpeg_bin: str = "ffmpeg"):
        self.ffmpeg_bin = ffmpeg_bin

    def run(self, args: Iterable[str], on_progress: Optional[Callable[[Dict[str, str]], None]] = None) -> None:
        cmd = [self.ffmpeg_bin, *args, "-progress", "pipe:1", "-nostats", "-hide_banner"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        assert proc.stdout is not None

        progress: Dict[str, str] = {}
        for line in proc.stdout:
            line = line.strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            progress[k] = v
            if on_progress:
                on_progress(progress)

        stderr = proc.stderr.read() if proc.stderr else ""
        rc = proc.wait()
        if rc != 0:
            raise VasError(
                code="E_FFMPEG_FAILED",
                message="ffmpeg command failed",
                details={"cmd": " ".join(shlex.quote(c) for c in cmd), "stderr": stderr[-2000:]},
                recoverable=True,
                hint="Inspect ffmpeg arguments and input files",
            )

    def ffmpeg_version(self) -> str:
        result = subprocess.run([self.ffmpeg_bin, "-version"], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise VasError("E_FFMPEG_NOT_FOUND", "Unable to run ffmpeg")
        return result.stdout.splitlines()[0].strip()

    def preferred_h264_encoder(self) -> str:
        result = subprocess.run([self.ffmpeg_bin, "-encoders"], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            return "libx264"

        encoders = result.stdout
        if " h264_videotoolbox" in encoders:
            return "h264_videotoolbox"
        if " libx264" in encoders:
            return "libx264"
        return "mpeg4"
