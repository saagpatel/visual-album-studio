import json
import subprocess
from pathlib import Path


def _run(repo_root: Path, command: str, payload: dict) -> dict:
    script = repo_root / "scripts" / "youtube_adapter.py"
    proc = subprocess.run(
        ["python3", str(script), command, json.dumps(payload)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    body = proc.stdout.strip()
    assert body
    parsed = json.loads(body)
    assert "ok" in parsed
    assert "error_code" in parsed
    assert "http_status" in parsed
    assert "retryable" in parsed
    assert "data" in parsed
    return parsed


def test_it013_unknown_command_envelope(repo_root: Path):
    result = _run(repo_root, "unknown_command", {})
    assert result["ok"] is False
    assert result["error_code"] == "E_ADAPTER_UNKNOWN_COMMAND"
    assert result["http_status"] == 0


def test_it013_auth_guard_without_token(repo_root: Path):
    result = _run(repo_root, "list_channels", {})
    assert result["ok"] is False
    assert result["error_code"] == "E_YT_AUTH_REQUIRED"
    assert result["http_status"] == 401


def test_it013_start_upload_file_guard(repo_root: Path):
    result = _run(
        repo_root,
        "start_resumable_upload",
        {
            "access_token": "fake-token",
            "file_path": str(repo_root / "out" / "missing-video.mp4"),
            "metadata": {},
        },
    )
    assert result["ok"] is False
    assert result["error_code"] == "E_YT_FILE_NOT_FOUND"
    assert result["http_status"] == 0


def test_it013_attach_playlists_input_guard(repo_root: Path):
    result = _run(
        repo_root,
        "attach_playlists",
        {
            "access_token": "fake-token",
            "video_id": "v123",
            "playlist_ids": "not-a-list",
        },
    )
    assert result["ok"] is False
    assert result["error_code"] == "E_YT_PLAYLIST_INPUT_INVALID"
