from __future__ import annotations

import time
from typing import Any


class ProviderFeatureFlagServiceV1:
    _DEFAULT_ENABLED = {"youtube", "tiktok", "instagram", "facebook_reels", "x"}

    def __init__(self, db):
        self.db = db

    @staticmethod
    def _now() -> int:
        return int(time.time())

    def set_flag(self, *, provider: str, enabled: bool, rollout_stage: str = "canary", candidate: bool = True) -> dict[str, Any]:
        provider = str(provider).strip().lower()
        self.db.execute(
            """
            INSERT OR REPLACE INTO provider_feature_flags(provider, enabled, rollout_stage, candidate, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (provider, 1 if enabled else 0, str(rollout_stage), 1 if candidate else 0, self._now()),
        )
        self.db.commit()
        return {
            "ok": True,
            "provider": provider,
            "enabled": bool(enabled),
            "rollout_stage": rollout_stage,
            "candidate": bool(candidate),
        }

    def is_enabled(self, provider: str) -> bool:
        provider = str(provider).strip().lower()
        row = self.db.execute(
            "SELECT enabled FROM provider_feature_flags WHERE provider = ?",
            (provider,),
        ).fetchone()
        if row is not None:
            return int(row["enabled"]) == 1
        return provider in self._DEFAULT_ENABLED

    def list_flags(self) -> dict[str, Any]:
        rows = self.db.execute(
            "SELECT provider, enabled, rollout_stage, candidate, updated_at FROM provider_feature_flags ORDER BY provider ASC"
        ).fetchall()
        return {
            "ok": True,
            "flags": [
                {
                    "provider": str(row["provider"]),
                    "enabled": int(row["enabled"]) == 1,
                    "rollout_stage": str(row["rollout_stage"]),
                    "candidate": int(row["candidate"]) == 1,
                    "updated_at": int(row["updated_at"]),
                }
                for row in rows
            ],
        }

    def filter_enabled(self, providers: list[str]) -> list[str]:
        return [provider for provider in providers if self.is_enabled(provider)]
