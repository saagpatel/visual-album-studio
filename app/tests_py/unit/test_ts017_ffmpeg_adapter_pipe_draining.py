import json
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest


def _run_adapter_with_pipe_pressure(tmp_path: Path, fail_child: bool, fail_callback: bool = False) -> dict:
    core_py = Path(__file__).resolve().parents[2] / "src" / "core_py"
    runner = tmp_path / "adapter_runner.py"
    child_pid_file = tmp_path / "fake_ffmpeg.pid"
    child_code = "import sys; sys.stderr.write('HEAD\\n' + 'x' * 262144 + 'TAIL-MARKER\\n'); sys.stderr.flush(); "
    if fail_callback:
        child_code += f"open({str(child_pid_file)!r}, 'w').write(str(__import__('os').getpid())); "
    child_code += "print('frame=1\\nout_time_ms=10\\nprogress=continue\\nframe=2\\nprogress=end', flush=True)"
    if fail_child:
        child_code += "; sys.exit(7)"
    if fail_callback:
        child_code += "; __import__('time').sleep(30)"
    progress_callback = (
        "def report_progress(event): raise RuntimeError('progress callback failed')"
        if fail_callback
        else "def report_progress(event): events.append(dict(event))"
    )
    runner.write_text(
        "\n".join(
            [
                "import json, sys",
                f"sys.path.insert(0, {str(core_py)!r})",
                "from vas_studio import FFmpegAdapter",
                "from vas_studio.errors import VasError",
                f"child_code = {child_code!r}",
                "events = []",
                progress_callback,
                "try:",
                "    FFmpegAdapter(sys.executable).run(['-c', child_code], report_progress)",
                "    result = {'ok': True, 'events': events}",
                "except RuntimeError as error:",
                f"    child_pid = int(open({str(child_pid_file)!r}).read()) if {fail_callback!r} else -1",
                "    try:",
                "        __import__('os').kill(child_pid, 0)",
                "        child_running = True",
                "    except ProcessLookupError:",
                "        child_running = False",
                "    result = {'ok': False, 'callback_error': str(error), 'child_running': child_running}",
                "except VasError as error:",
                "    result = {'ok': False, 'code': error.code, 'stderr': error.details.get('stderr', ''), 'events': events}",
                "print(json.dumps(result))",
            ]
        ),
        encoding="utf-8",
    )

    process = subprocess.Popen(
        [sys.executable, str(runner)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=8)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        pytest.fail("FFmpeg adapter deadlocked while child filled stderr before stdout progress")
    assert process.returncode == 0, stderr
    return json.loads(stdout)


def test_ffmpeg_adapter_drains_stderr_while_consuming_progress(tmp_path: Path):
    result = _run_adapter_with_pipe_pressure(tmp_path, fail_child=False)

    assert result["ok"] is True
    assert result["events"][-1]["progress"] == "end"
    assert result["events"][-1]["frame"] == "2"


def test_ffmpeg_adapter_keeps_error_tail_after_pipe_pressure(tmp_path: Path):
    result = _run_adapter_with_pipe_pressure(tmp_path, fail_child=True)

    assert result["ok"] is False
    assert result["code"] == "E_FFMPEG_FAILED"
    assert "TAIL-MARKER" in result["stderr"]
    assert len(result["stderr"]) <= 2000


def test_ffmpeg_adapter_stops_process_when_progress_callback_raises(tmp_path: Path):
    result = _run_adapter_with_pipe_pressure(tmp_path, fail_child=False, fail_callback=True)

    assert result["ok"] is False
    assert result["callback_error"] == "progress callback failed"
    assert result["child_running"] is False
