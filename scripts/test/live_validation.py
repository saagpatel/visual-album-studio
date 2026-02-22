#!/usr/bin/env python3
"""Live validation matrix for Phase 5/6 official API checks.

Exit codes:
- 0: full pass
- 1: executed but failed
- 2: skipped/pending due to missing prerequisites
"""

from __future__ import annotations

import base64
import datetime as dt
import json
import os
import ssl
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
OUT_LOGS = ROOT / "out" / "logs"
OUT_LOGS.mkdir(parents=True, exist_ok=True)

TOKEN_URL = "https://oauth2.googleapis.com/token"
YT_CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels?part=id,snippet&mine=true"
YT_UPLOAD_INIT_URL = "https://www.googleapis.com/upload/youtube/v3/videos?part=snippet,status&uploadType=resumable"
YT_ANALYTICS_URL = "https://youtubeanalytics.googleapis.com/v2/reports"
YT_REPORTING_JOBS_URL = "https://youtubereporting.googleapis.com/v1/jobs"


@dataclass
class CheckResult:
    name: str
    status: str  # pass|fail|skip
    detail: str


class LiveValidationError(Exception):
    pass


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


def _ssl_context() -> ssl.SSLContext:
    cafile = _env("VAS_SSL_CA_BUNDLE") or _env("SSL_CERT_FILE")
    if not cafile:
        try:
            import certifi  # type: ignore

            cafile = certifi.where()
        except Exception:
            cafile = ""
    if cafile:
        return ssl.create_default_context(cafile=cafile)
    return ssl.create_default_context()


def _urlopen(req: urllib.request.Request, timeout: int):
    return urllib.request.urlopen(req, timeout=timeout, context=_ssl_context())


def _http_json(method: str, url: str, *, headers: Optional[Dict[str, str]] = None, payload: Optional[Dict[str, Any]] = None) -> Tuple[int, Dict[str, Any], Dict[str, str], str]:
    data = None
    req_headers = {"Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url=url, data=data, headers=req_headers, method=method)
    try:
        with _urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            parsed = json.loads(body) if body else {}
            resp_headers = {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, parsed, resp_headers, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        parsed = {}
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {}
        resp_headers = {k.lower(): v for k, v in getattr(e, "headers", {}).items()} if getattr(e, "headers", None) else {}
        return e.code, parsed, resp_headers, body


def _refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    data = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
    ).encode("utf-8")
    req = urllib.request.Request(TOKEN_URL, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    try:
        with _urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise LiveValidationError(f"token refresh failed: HTTP {e.code}: {body[:500]}") from e

    token = payload.get("access_token", "")
    if not token:
        raise LiveValidationError(f"token refresh response missing access_token: keys={sorted(payload.keys())}")
    return token


def _auth_headers(access_token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _keyring_roundtrip() -> CheckResult:
    helper = ROOT / "native" / "vas_keyring" / "target" / "debug" / "vas_keyring"
    if not helper.exists():
        return CheckResult("keyring_roundtrip", "skip", f"helper missing at {helper}")

    service = "vas-live-validation"
    account = f"phase5-{dt.datetime.now(dt.UTC).strftime('%Y%m%d%H%M%S')}"
    secret = base64.urlsafe_b64encode(os.urandom(24)).decode("utf-8")

    set_cmd = [str(helper), "set", service, account, secret]
    get_cmd = [str(helper), "get", service, account]
    del_cmd = [str(helper), "delete", service, account]

    set_proc = subprocess.run(set_cmd, capture_output=True, text=True)
    if set_proc.returncode != 0:
        return CheckResult("keyring_roundtrip", "skip", f"set unavailable: {set_proc.stderr.strip()[:300]}")

    get_proc = subprocess.run(get_cmd, capture_output=True, text=True)
    if get_proc.returncode != 0:
        return CheckResult("keyring_roundtrip", "fail", f"get failed: {get_proc.stderr.strip()[:300]}")

    ok = get_proc.stdout.strip() == secret
    subprocess.run(del_cmd, capture_output=True, text=True)
    if not ok:
        return CheckResult("keyring_roundtrip", "fail", "retrieved secret mismatch")
    return CheckResult("keyring_roundtrip", "pass", "set/get/delete succeeded")


def _phase5(access_token: str) -> Dict[str, Any]:
    checks: list[CheckResult] = []

    checks.append(_keyring_roundtrip())

    status, payload, _headers, _raw = _http_json("GET", YT_CHANNELS_URL, headers=_auth_headers(access_token))
    if status == 200 and payload.get("items"):
        channel = payload["items"][0]
        checks.append(CheckResult("youtube_channels_mine", "pass", f"channel_id={channel.get('id','')}, title={channel.get('snippet',{}).get('title','')}"))
    else:
        checks.append(CheckResult("youtube_channels_mine", "fail", f"status={status}, body_keys={sorted(payload.keys())}"))

    video_path = _env("VAS_YT_TEST_VIDEO_PATH")
    if not video_path:
        checks.append(CheckResult("youtube_resumable_upload", "skip", "set VAS_YT_TEST_VIDEO_PATH for live upload interruption/resume check"))
    else:
        path = Path(video_path)
        if not path.exists():
            checks.append(CheckResult("youtube_resumable_upload", "fail", f"file missing: {path}"))
        else:
            init_payload = {
                "snippet": {"title": f"VAS live validation {dt.datetime.now(dt.UTC).isoformat()}"},
                "status": {"privacyStatus": "private"},
            }
            size = path.stat().st_size
            headers = _auth_headers(access_token)
            headers.update(
                {
                    "X-Upload-Content-Type": "video/mp4",
                    "X-Upload-Content-Length": str(size),
                }
            )
            status_i, payload_i, headers_i, raw_i = _http_json("POST", YT_UPLOAD_INIT_URL, headers=headers, payload=init_payload)
            location = headers_i.get("location", "")
            if status_i not in (200, 201) or not location:
                checks.append(CheckResult("youtube_resumable_upload", "fail", f"init failed status={status_i}, body={raw_i[:300]}"))
            else:
                # interruption/resume simulation: upload first half then remainder
                data = path.read_bytes()
                midpoint = max(1, len(data) // 2)
                part1 = data[:midpoint]
                part2 = data[midpoint:]

                req1 = urllib.request.Request(
                    location,
                    data=part1,
                    method="PUT",
                    headers={
                        **_auth_headers(access_token),
                        "Content-Length": str(len(part1)),
                        "Content-Type": "video/mp4",
                        "Content-Range": f"bytes 0-{midpoint - 1}/{len(data)}",
                    },
                )
                try:
                    with _urlopen(req1, timeout=60) as r1:
                        # some servers may complete for tiny files
                        _ = r1.read()
                        code1 = r1.status
                except urllib.error.HTTPError as e:
                    code1 = e.code

                req2 = urllib.request.Request(
                    location,
                    data=part2,
                    method="PUT",
                    headers={
                        **_auth_headers(access_token),
                        "Content-Length": str(len(part2)),
                        "Content-Type": "video/mp4",
                        "Content-Range": f"bytes {midpoint}-{len(data)-1}/{len(data)}",
                    },
                )
                try:
                    with _urlopen(req2, timeout=120) as r2:
                        body2 = r2.read().decode("utf-8", errors="replace")
                        code2 = r2.status
                        parsed2 = json.loads(body2) if body2 else {}
                except urllib.error.HTTPError as e:
                    code2 = e.code
                    parsed2 = {}
                    try:
                        parsed2 = json.loads(e.read().decode("utf-8", errors="replace"))
                    except Exception:
                        pass

                if code2 in (200, 201) and parsed2.get("id"):
                    checks.append(CheckResult("youtube_resumable_upload", "pass", f"upload completed video_id={parsed2['id']} (phase1={code1}, phase2={code2})"))
                else:
                    checks.append(CheckResult("youtube_resumable_upload", "fail", f"resume failed phase1={code1}, phase2={code2}"))

    return {
        "phase": "05",
        "checks": [c.__dict__ for c in checks],
    }


def _phase6(access_token: str) -> Dict[str, Any]:
    checks: list[CheckResult] = []
    today = dt.date.today()
    start = today - dt.timedelta(days=7)

    q = urllib.parse.urlencode(
        {
            "ids": "channel==MINE",
            "startDate": start.isoformat(),
            "endDate": today.isoformat(),
            "metrics": "views,estimatedMinutesWatched",
            "dimensions": "day",
        }
    )
    status, payload, _headers, _raw = _http_json("GET", f"{YT_ANALYTICS_URL}?{q}", headers=_auth_headers(access_token))
    if status == 200 and "rows" in payload:
        checks.append(CheckResult("youtube_analytics_report", "pass", f"rows={len(payload.get('rows', []))}"))
    else:
        checks.append(CheckResult("youtube_analytics_report", "fail", f"status={status}, keys={sorted(payload.keys())}"))

    q_rev = urllib.parse.urlencode(
        {
            "ids": "channel==MINE",
            "startDate": start.isoformat(),
            "endDate": today.isoformat(),
            "metrics": "estimatedRevenue",
            "dimensions": "day",
            "currency": "USD",
        }
    )
    status_r, payload_r, _h, _raw_r = _http_json("GET", f"{YT_ANALYTICS_URL}?{q_rev}", headers=_auth_headers(access_token))
    if status_r == 200:
        checks.append(CheckResult("youtube_revenue_metric", "pass", f"rows={len(payload_r.get('rows', []))}"))
    elif status_r in (403, 400):
        checks.append(CheckResult("youtube_revenue_metric", "skip", f"unavailable for account/project (status={status_r})"))
    else:
        checks.append(CheckResult("youtube_revenue_metric", "fail", f"status={status_r}, keys={sorted(payload_r.keys())}"))

    status_j, payload_j, _h2, _raw2 = _http_json("GET", YT_REPORTING_JOBS_URL, headers=_auth_headers(access_token))
    if status_j == 200:
        checks.append(CheckResult("youtube_reporting_jobs", "pass", f"jobs={len(payload_j.get('jobs', []))}"))
    elif status_j in (403, 404):
        checks.append(CheckResult("youtube_reporting_jobs", "skip", f"reporting API unavailable (status={status_j})"))
    else:
        checks.append(CheckResult("youtube_reporting_jobs", "fail", f"status={status_j}, keys={sorted(payload_j.keys())}"))

    return {
        "phase": "06",
        "checks": [c.__dict__ for c in checks],
    }


def _summarize(report: Dict[str, Any]) -> Dict[str, int]:
    summary = {"pass": 0, "fail": 0, "skip": 0}
    for check in report.get("checks", []):
        status = check.get("status", "skip")
        summary[status] = summary.get(status, 0) + 1
    return summary


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"05", "06"}:
        print("usage: live_validation.py <05|06>", file=sys.stderr)
        return 2

    phase = sys.argv[1]
    client_id = _env("VAS_YT_CLIENT_ID")
    client_secret = _env("VAS_YT_CLIENT_SECRET")
    refresh_token = _env("VAS_YT_REFRESH_TOKEN")

    if not (client_id and client_secret and refresh_token):
        report = {
            "phase": phase,
            "status": "pending",
            "reason": "missing VAS_YT_CLIENT_ID/VAS_YT_CLIENT_SECRET/VAS_YT_REFRESH_TOKEN",
            "checks": [],
        }
        out = OUT_LOGS / f"live_phase_{phase}_report.json"
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 2

    try:
        access_token = _refresh_access_token(client_id, client_secret, refresh_token)
    except LiveValidationError as exc:
        report = {
            "phase": phase,
            "status": "failed",
            "reason": str(exc),
            "checks": [],
        }
        out = OUT_LOGS / f"live_phase_{phase}_report.json"
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 1

    report = _phase5(access_token) if phase == "05" else _phase6(access_token)
    summary = _summarize(report)
    report["summary"] = summary
    report["status"] = "passed" if summary.get("fail", 0) == 0 and summary.get("pass", 0) > 0 else "failed"

    out = OUT_LOGS / f"live_phase_{phase}_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

    if report["status"] == "passed":
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
