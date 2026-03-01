#!/usr/bin/env python3
"""Runtime YouTube adapter sidecar used by Godot adapter.

Usage:
  youtube_adapter.py <command> <payload_json>

Commands:
  - list_channels
  - start_resumable_upload
  - resume_upload
  - apply_metadata
  - upload_thumbnail
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Tuple

YT_CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels?part=id,snippet&mine=true"
YT_UPLOAD_INIT_URL = "https://www.googleapis.com/upload/youtube/v3/videos?part=snippet,status&uploadType=resumable"
YT_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos?part=snippet,status"
YT_THUMBNAILS_URL = "https://www.googleapis.com/upload/youtube/v3/thumbnails/set"
YT_PLAYLIST_ITEMS_URL = "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet"
ALLOWED_HOST_SUFFIXES = ("googleapis.com", "googleusercontent.com", "youtube.com")


def envelope(
    ok: bool,
    *,
    error_code: str = "",
    http_status: int = 0,
    retryable: bool = False,
    data: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return {
        "ok": bool(ok),
        "error_code": error_code,
        "http_status": int(http_status),
        "retryable": bool(retryable),
        "data": data or {},
    }


def is_retryable_status(status: int) -> bool:
    return status in (408, 425, 429, 500, 502, 503, 504)


def is_safe_https_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host:
        return False
    return any(host == suffix or host.endswith(f".{suffix}") for suffix in ALLOWED_HOST_SUFFIXES)


def http_json(method: str, url: str, headers: Dict[str, str], payload: Dict[str, Any] | None = None) -> Tuple[int, Dict[str, str], str, Dict[str, Any]]:
    if not is_safe_https_url(url):
        return 0, {}, "", {"error_code": "E_ADAPTER_UNSAFE_URL", "url": url[:300]}

    body_bytes = None
    req_headers = {"Accept": "application/json"}
    req_headers.update(headers)
    if payload is not None:
        body_bytes = json.dumps(payload).encode("utf-8")
        req_headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url=url, method=method, data=body_bytes, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:  # nosec B310
            raw = resp.read().decode("utf-8", errors="replace")
            parsed = json.loads(raw) if raw else {}
            return int(resp.status), {k.lower(): v for k, v in resp.headers.items()}, raw, parsed
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        parsed: Dict[str, Any] = {}
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {}
        headers_out = {k.lower(): v for k, v in (exc.headers.items() if exc.headers else [])}
        return int(exc.code), headers_out, raw, parsed


def http_bytes(method: str, url: str, headers: Dict[str, str], payload: bytes | None) -> Tuple[int, Dict[str, str], str, Dict[str, Any]]:
    if not is_safe_https_url(url):
        return 0, {}, "", {"error_code": "E_ADAPTER_UNSAFE_URL", "url": url[:300]}

    req = urllib.request.Request(url=url, method=method, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:  # nosec B310
            raw = resp.read().decode("utf-8", errors="replace")
            parsed = json.loads(raw) if raw else {}
            return int(resp.status), {k.lower(): v for k, v in resp.headers.items()}, raw, parsed
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        parsed: Dict[str, Any] = {}
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {}
        headers_out = {k.lower(): v for k, v in (exc.headers.items() if exc.headers else [])}
        return int(exc.code), headers_out, raw, parsed


def auth_headers(access_token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def token_from_payload(payload: Dict[str, Any]) -> str:
    # Prefer environment handoff to avoid token exposure in process args.
    env_token = os.environ.get("VAS_YT_ACCESS_TOKEN", "").strip()
    if env_token:
        return env_token
    return str(payload.get("access_token", "")).strip()


def build_video_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    if "snippet" in metadata or "status" in metadata:
        return {
            "snippet": metadata.get("snippet", {}),
            "status": metadata.get("status", {}),
        }

    snippet = {
        "title": metadata.get("title", "Visual Album Studio Upload"),
        "description": metadata.get("description", ""),
        "tags": metadata.get("tags", []),
        "categoryId": str(metadata.get("category_id", "10")),
    }
    status = {
        "privacyStatus": metadata.get("privacy_status", "private"),
    }
    publish_at = metadata.get("publish_at", "")
    if publish_at:
        status["publishAt"] = publish_at
    return {"snippet": snippet, "status": status}


def cmd_list_channels(payload: Dict[str, Any]) -> Dict[str, Any]:
    access_token = token_from_payload(payload)
    if not access_token:
        return envelope(False, error_code="E_YT_AUTH_REQUIRED", http_status=401, data={"message": "access_token is required"})

    status, _headers, _raw, parsed = http_json("GET", YT_CHANNELS_URL, auth_headers(access_token))
    if status == 200:
        return envelope(True, http_status=status, data={"channels": parsed.get("items", []), "raw": parsed})
    return envelope(False, error_code="E_YT_LIST_CHANNELS_FAILED", http_status=status, retryable=is_retryable_status(status), data={"raw": parsed})


def cmd_start_resumable_upload(payload: Dict[str, Any]) -> Dict[str, Any]:
    access_token = token_from_payload(payload)
    file_path = Path(str(payload.get("file_path", "")))
    metadata = payload.get("metadata", {}) if isinstance(payload.get("metadata", {}), dict) else {}
    if not access_token:
        return envelope(False, error_code="E_YT_AUTH_REQUIRED", http_status=401, data={"message": "access_token is required"})
    if not file_path.exists():
        return envelope(False, error_code="E_YT_FILE_NOT_FOUND", http_status=0, data={"file_path": str(file_path)})

    size = file_path.stat().st_size
    headers = auth_headers(access_token)
    headers.update(
        {
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(size),
        }
    )
    status, response_headers, raw, parsed = http_json("POST", YT_UPLOAD_INIT_URL, headers, build_video_metadata(metadata))
    location = response_headers.get("location", "")
    if status in (200, 201) and location:
        return envelope(
            True,
            http_status=status,
            data={
                "session_url": location,
                "bytes_total": size,
                "bytes_uploaded": 0,
            },
        )
    return envelope(
        False,
        error_code="E_YT_UPLOAD_INIT_FAILED",
        http_status=status,
        retryable=is_retryable_status(status),
        data={"body": raw[:1000], "parsed": parsed},
    )


def _range_uploaded_bytes(range_header: str, fallback: int) -> int:
    # Example Range response: "bytes=0-1048575"
    m = re.search(r"bytes=0-(\d+)", range_header)
    if not m:
        return fallback
    return int(m.group(1)) + 1


def cmd_resume_upload(payload: Dict[str, Any]) -> Dict[str, Any]:
    access_token = token_from_payload(payload)
    session_url = str(payload.get("session_url", "")).strip()
    file_path = Path(str(payload.get("file_path", "")))
    bytes_uploaded = int(payload.get("bytes_uploaded", 0) or 0)
    chunk_size = int(payload.get("chunk_size", 8 * 1024 * 1024) or 8 * 1024 * 1024)

    if not access_token:
        return envelope(False, error_code="E_YT_AUTH_REQUIRED", http_status=401, data={"message": "access_token is required"})
    if not session_url:
        return envelope(False, error_code="E_YT_SESSION_MISSING", http_status=0, data={})
    if not is_safe_https_url(session_url):
        return envelope(False, error_code="E_YT_UNSAFE_SESSION_URL", http_status=0, data={"session_url": session_url[:300]})
    if not file_path.exists():
        return envelope(False, error_code="E_YT_FILE_NOT_FOUND", http_status=0, data={"file_path": str(file_path)})

    total_size = file_path.stat().st_size
    if bytes_uploaded >= total_size:
        return envelope(True, http_status=200, data={"bytes_uploaded": total_size, "bytes_total": total_size, "complete": True})

    with file_path.open("rb") as fp:
        fp.seek(bytes_uploaded)
        chunk = fp.read(max(1, chunk_size))

    if not chunk:
        return envelope(False, error_code="E_YT_UPLOAD_EMPTY_CHUNK", http_status=0, data={"bytes_uploaded": bytes_uploaded})

    chunk_end = bytes_uploaded + len(chunk) - 1
    headers = auth_headers(access_token)
    headers.update(
        {
            "Content-Type": "video/mp4",
            "Content-Length": str(len(chunk)),
            "Content-Range": f"bytes {bytes_uploaded}-{chunk_end}/{total_size}",
        }
    )
    status, response_headers, raw, parsed = http_bytes("PUT", session_url, headers, chunk)

    if status in (200, 201):
        video_id = ""
        if isinstance(parsed, dict):
            video_id = str(parsed.get("id", ""))
        return envelope(
            True,
            http_status=status,
            data={
                "bytes_uploaded": total_size,
                "bytes_total": total_size,
                "resume_offset": total_size,
                "complete": True,
                "video_id": video_id,
                "etag": str(response_headers.get("etag", "")),
                "raw": parsed,
            },
        )

    if status == 308:
        range_header = response_headers.get("range", "")
        uploaded = _range_uploaded_bytes(range_header, chunk_end + 1)
        uploaded = min(uploaded, total_size)
        return envelope(
            True,
            http_status=status,
            data={
                "bytes_uploaded": uploaded,
                "bytes_total": total_size,
                "resume_offset": uploaded,
                "complete": uploaded >= total_size,
                "session_url": session_url,
                "etag": str(response_headers.get("etag", "")),
            },
        )

    return envelope(
        False,
        error_code="E_YT_UPLOAD_RESUME_FAILED",
        http_status=status,
        retryable=is_retryable_status(status),
        data={"body": raw[:1000], "parsed": parsed},
    )


def cmd_apply_metadata(payload: Dict[str, Any]) -> Dict[str, Any]:
    access_token = token_from_payload(payload)
    video_id = str(payload.get("video_id", "")).strip()
    metadata = payload.get("metadata", {}) if isinstance(payload.get("metadata", {}), dict) else {}
    if not access_token:
        return envelope(False, error_code="E_YT_AUTH_REQUIRED", http_status=401, data={"message": "access_token is required"})
    if not video_id:
        return envelope(False, error_code="E_YT_VIDEO_ID_MISSING", http_status=0, data={})

    body = build_video_metadata(metadata)
    body["id"] = video_id
    status, _headers, raw, parsed = http_json("PUT", YT_VIDEOS_URL, auth_headers(access_token), body)
    if status in (200, 201):
        return envelope(True, http_status=status, data={"raw": parsed})
    return envelope(
        False,
        error_code="E_YT_APPLY_METADATA_FAILED",
        http_status=status,
        retryable=is_retryable_status(status),
        data={"body": raw[:1000], "parsed": parsed},
    )


def cmd_upload_thumbnail(payload: Dict[str, Any]) -> Dict[str, Any]:
    access_token = token_from_payload(payload)
    video_id = str(payload.get("video_id", "")).strip()
    thumbnail_path = Path(str(payload.get("thumbnail_path", "")))
    if not access_token:
        return envelope(False, error_code="E_YT_AUTH_REQUIRED", http_status=401, data={"message": "access_token is required"})
    if not video_id:
        return envelope(False, error_code="E_YT_VIDEO_ID_MISSING", http_status=0, data={})
    if not thumbnail_path.exists():
        return envelope(False, error_code="E_YT_THUMBNAIL_NOT_FOUND", http_status=0, data={"thumbnail_path": str(thumbnail_path)})

    data = thumbnail_path.read_bytes()
    headers = auth_headers(access_token)
    headers.update({"Content-Type": "image/png", "Content-Length": str(len(data))})
    url = f"{YT_THUMBNAILS_URL}?{urllib.parse.urlencode({'videoId': video_id})}"
    status, _headers, raw, parsed = http_bytes("POST", url, headers, data)
    if status in (200, 201):
        return envelope(True, http_status=status, data={"raw": parsed})
    return envelope(
        False,
        error_code="E_YT_UPLOAD_THUMBNAIL_FAILED",
        http_status=status,
        retryable=is_retryable_status(status),
        data={"body": raw[:1000], "parsed": parsed},
    )


def cmd_attach_playlists(payload: Dict[str, Any]) -> Dict[str, Any]:
    access_token = token_from_payload(payload)
    video_id = str(payload.get("video_id", "")).strip()
    playlist_ids = payload.get("playlist_ids", [])
    if not access_token:
        return envelope(False, error_code="E_YT_AUTH_REQUIRED", http_status=401, data={"message": "access_token is required"})
    if not video_id:
        return envelope(False, error_code="E_YT_VIDEO_ID_MISSING", http_status=0, data={})
    if not isinstance(playlist_ids, list):
        return envelope(False, error_code="E_YT_PLAYLIST_INPUT_INVALID", http_status=0, data={})

    attached: list[str] = []
    for pid in playlist_ids:
        playlist_id = str(pid).strip()
        if not playlist_id:
            continue
        body = {
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {"kind": "youtube#video", "videoId": video_id},
            }
        }
        status, _headers, raw, parsed = http_json("POST", YT_PLAYLIST_ITEMS_URL, auth_headers(access_token), body)
        if status not in (200, 201):
            return envelope(
                False,
                error_code="E_YT_ATTACH_PLAYLIST_FAILED",
                http_status=status,
                retryable=is_retryable_status(status),
                data={"playlist_id": playlist_id, "body": raw[:1000], "parsed": parsed},
            )
        attached.append(playlist_id)
    return envelope(True, http_status=200, data={"video_id": video_id, "playlist_ids": attached})


def cmd_readback_video(payload: Dict[str, Any]) -> Dict[str, Any]:
    access_token = token_from_payload(payload)
    video_id = str(payload.get("video_id", "")).strip()
    if not access_token:
        return envelope(False, error_code="E_YT_AUTH_REQUIRED", http_status=401, data={"message": "access_token is required"})
    if not video_id:
        return envelope(False, error_code="E_YT_VIDEO_ID_MISSING", http_status=0, data={})

    query = urllib.parse.urlencode({"part": "snippet,status", "id": video_id})
    status, _headers, raw, parsed = http_json(
        "GET",
        f"https://www.googleapis.com/youtube/v3/videos?{query}",
        auth_headers(access_token),
    )
    if status == 200:
        items = parsed.get("items", []) if isinstance(parsed, dict) else []
        first = items[0] if items else {}
        return envelope(True, http_status=200, data=first if isinstance(first, dict) else {"raw": first})
    return envelope(
        False,
        error_code="E_YT_READBACK_FAILED",
        http_status=status,
        retryable=is_retryable_status(status),
        data={"body": raw[:1000], "parsed": parsed},
    )


def main() -> int:
    if len(sys.argv) != 3:
        print(json.dumps(envelope(False, error_code="E_ADAPTER_USAGE", data={"usage": "youtube_adapter.py <command> <payload_json>"})))
        return 0

    command = sys.argv[1].strip()
    try:
        payload = json.loads(sys.argv[2]) if sys.argv[2].strip() else {}
        if not isinstance(payload, dict):
            payload = {}
    except json.JSONDecodeError:
        print(json.dumps(envelope(False, error_code="E_ADAPTER_BAD_PAYLOAD")))
        return 0

    command_map = {
        "list_channels": cmd_list_channels,
        "start_resumable_upload": cmd_start_resumable_upload,
        "resume_upload": cmd_resume_upload,
        "apply_metadata": cmd_apply_metadata,
        "upload_thumbnail": cmd_upload_thumbnail,
        "attach_playlists": cmd_attach_playlists,
        "readback_video": cmd_readback_video,
    }
    fn = command_map.get(command)
    if fn is None:
        print(json.dumps(envelope(False, error_code="E_ADAPTER_UNKNOWN_COMMAND", data={"command": command})))
        return 0

    try:
        print(json.dumps(fn(payload)))
    except Exception as exc:  # defensive boundary for adapter invocation
        if os.environ.get("VAS_YT_ADAPTER_DEBUG", "0") == "1":
            raise
        print(
            json.dumps(
                envelope(
                    False,
                    error_code="E_ADAPTER_EXCEPTION",
                    data={"message": str(exc)[:500]},
                )
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
