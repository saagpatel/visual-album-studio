import json
import os
import subprocess
from pathlib import Path


def _run(repo_root: Path, command: str, payload: dict, access_token: str = "") -> dict:
    script = repo_root / "scripts" / "youtube_adapter.py"
    env = dict(os.environ)
    if access_token:
        env["VAS_YT_ACCESS_TOKEN"] = access_token
    proc = subprocess.run(
        ["python3", str(script), command, json.dumps(payload)],
        capture_output=True,
        text=True,
        check=False,
        env=env,
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
            "file_path": str(repo_root / "out" / "missing-video.mp4"),
            "metadata": {},
        },
        access_token="tkn",
    )
    assert result["ok"] is False
    assert result["error_code"] == "E_YT_FILE_NOT_FOUND"
    assert result["http_status"] == 0


def test_it013_attach_playlists_input_guard(repo_root: Path):
    result = _run(
        repo_root,
        "attach_playlists",
        {
            "video_id": "v123",
            "playlist_ids": "not-a-list",
        },
        access_token="tkn",
    )
    assert result["ok"] is False
    assert result["error_code"] == "E_YT_PLAYLIST_INPUT_INVALID"


def test_it013_payload_token_disallowed_by_default(repo_root: Path):
    result = _run(
        repo_root,
        "start_resumable_upload",
        {
            "access_token": "x",
            "file_path": str(repo_root / "out" / "missing-video.mp4"),
            "metadata": {},
        },
    )
    assert result["ok"] is False
    assert result["error_code"] == "E_YT_AUTH_REQUIRED"
