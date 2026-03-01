from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path


def pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8").rstrip("=")
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("utf-8")).digest()).decode("utf-8").rstrip("=")
    return verifier, challenge


@dataclass
class UploadSession:
    session_id: str
    file_path: Path
    bytes_total: int
    bytes_uploaded: int = 0
    etag: str = ""
    updated_at: int = 0


class ResumableUploadStore:
    def __init__(self, state_path: Path):
        self.state_path = state_path
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, session: UploadSession) -> None:
        now = int(time.time())
        self.state_path.write_text(
            json.dumps(
                {
                    "session_id": session.session_id,
                    "file_path": str(session.file_path),
                    "bytes_total": session.bytes_total,
                    "bytes_uploaded": session.bytes_uploaded,
                    "etag": session.etag,
                    "updated_at": session.updated_at or now,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def load(self) -> UploadSession | None:
        if not self.state_path.exists():
            return None
        d = json.loads(self.state_path.read_text(encoding="utf-8"))
        return UploadSession(
            session_id=d["session_id"],
            file_path=Path(d["file_path"]),
            bytes_total=int(d["bytes_total"]),
            bytes_uploaded=int(d["bytes_uploaded"]),
            etag=str(d.get("etag", "")),
            updated_at=int(d.get("updated_at", 0)),
        )


class QuotaBudget:
    def __init__(self, daily_budget: int = 10000):
        self.daily_budget = daily_budget
        self.used = 0

    def estimate_publish(self, with_thumbnail: bool = True, with_playlist: bool = False) -> int:
        units = 100
        if with_thumbnail:
            units += 50
        if with_playlist:
            units += 50
        return units

    def can_run(self, estimated: int) -> bool:
        return (self.used + estimated) <= self.daily_budget

    def consume(self, units: int) -> None:
        self.used += units

    def remaining(self) -> int:
        return max(0, self.daily_budget - self.used)

    def should_pause(self, estimated: int) -> bool:
        return not self.can_run(estimated)


class ChannelBindingGuard:
    def validate(self, selected_channel_id: str, profile_channel_id: str) -> bool:
        return selected_channel_id == profile_channel_id


@dataclass
class PublishProfile:
    channel_profile_id: str
    channel_id: str
    channel_title: str
    daily_quota_budget: int = 10000

    def to_dict(self) -> dict:
        return {
            "channel_profile_id": self.channel_profile_id,
            "channel_id": self.channel_id,
            "channel_title": self.channel_title,
            "daily_quota_budget": self.daily_quota_budget,
        }
