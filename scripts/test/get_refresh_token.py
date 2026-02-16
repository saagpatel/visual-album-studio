#!/usr/bin/env python3
"""Obtain a Google OAuth refresh token using installed-app PKCE + loopback.

This utility is intended for local live validation setup (Phase 5/6).
It uses only official OAuth endpoints and prints an export-ready token line.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import http.server
import json
import os
import secrets
import socket
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from dataclasses import dataclass

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
]


@dataclass
class CallbackResult:
    code: str = ""
    state: str = ""
    error: str = ""
    error_description: str = ""


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _urlsafe_b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _pkce_pair() -> tuple[str, str]:
    verifier = _urlsafe_b64(secrets.token_bytes(32))
    challenge = _urlsafe_b64(hashlib.sha256(verifier.encode("utf-8")).digest())
    return verifier, challenge


def _auth_url(client_id: str, redirect_uri: str, code_challenge: str, state: str, scopes: list[str]) -> str:
    query = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
    )
    return f"{AUTH_URL}?{query}"


def _token_exchange(
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
    code_verifier: str,
) -> dict:
    payload = {
        "client_id": client_id,
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
        "code_verifier": code_verifier,
    }
    if client_secret:
        payload["client_secret"] = client_secret

    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        TOKEN_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def _start_callback_server(redirect_path: str) -> tuple[http.server.ThreadingHTTPServer, threading.Event, CallbackResult, int]:
    event = threading.Event()
    result = CallbackResult()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path != redirect_path:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Not found")
                return

            query = urllib.parse.parse_qs(parsed.query)
            result.code = query.get("code", [""])[0]
            result.state = query.get("state", [""])[0]
            result.error = query.get("error", [""])[0]
            result.error_description = query.get("error_description", [""])[0]

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h2>Authorization received.</h2>"
                b"<p>You can close this tab and return to the terminal.</p>"
                b"</body></html>"
            )
            event.set()

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    port = _pick_free_port()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.timeout = 0.5

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, event, result, port


def _wait_for_callback(
    server: http.server.ThreadingHTTPServer,
    event: threading.Event,
    timeout_sec: int,
) -> None:
    started = time.time()
    while not event.is_set():
        if time.time() - started > timeout_sec:
            server.shutdown()
            server.server_close()
            raise TimeoutError(f"timed out after {timeout_sec}s waiting for OAuth callback")
        time.sleep(0.1)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Get a Google OAuth refresh token for local live validation."
    )
    parser.add_argument(
        "--client-id",
        default=os.environ.get("VAS_YT_CLIENT_ID", "").strip(),
        help="OAuth client id (or set VAS_YT_CLIENT_ID)",
    )
    parser.add_argument(
        "--client-secret",
        default=os.environ.get("VAS_YT_CLIENT_SECRET", "").strip(),
        help="OAuth client secret (or set VAS_YT_CLIENT_SECRET)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds waiting for callback (default: 300)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not auto-open browser; print URL only",
    )
    args = parser.parse_args()

    client_id = args.client_id.strip()
    client_secret = args.client_secret.strip()
    if not client_id:
        print("error: missing client id (pass --client-id or set VAS_YT_CLIENT_ID)")
        return 1

    state = secrets.token_urlsafe(24)
    verifier, challenge = _pkce_pair()

    server, event, callback_result, port = _start_callback_server("/oauth/callback")
    redirect_uri = f"http://127.0.0.1:{port}/oauth/callback"
    url = _auth_url(client_id, redirect_uri, challenge, state, DEFAULT_SCOPES)

    print("Open this URL and approve access:")
    print(url)
    if not args.no_browser:
        try:
            webbrowser.open(url, new=2, autoraise=True)
        except Exception:
            pass

    try:
        _wait_for_callback(server, event, args.timeout)
    except TimeoutError as exc:
        print(f"error: {exc}")
        return 1
    finally:
        server.shutdown()
        server.server_close()

    if callback_result.error:
        print(f"error: OAuth authorization failed: {callback_result.error} {callback_result.error_description}")
        return 1
    if callback_result.state != state:
        print("error: OAuth state mismatch")
        return 1
    if not callback_result.code:
        print("error: OAuth callback did not include authorization code")
        return 1

    try:
        token_payload = _token_exchange(
            client_id=client_id,
            client_secret=client_secret,
            code=callback_result.code,
            redirect_uri=redirect_uri,
            code_verifier=verifier,
        )
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"error: token exchange failed: HTTP {exc.code}: {body[:500]}")
        return 1
    except Exception as exc:
        print(f"error: token exchange failed: {exc}")
        return 1

    refresh_token = token_payload.get("refresh_token", "")
    if not refresh_token:
        print("error: no refresh_token in response.")
        print("hint: ensure prompt=consent and revoke prior grant before retry if needed.")
        return 1

    print("")
    print("Copy these values into scripts/test/live.env:")
    print(f'VAS_YT_CLIENT_ID="{client_id}"')
    print(f'VAS_YT_CLIENT_SECRET="{client_secret}"')
    print(f'VAS_YT_REFRESH_TOKEN="{refresh_token}"')
    print("")
    print("success: refresh token acquired")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
