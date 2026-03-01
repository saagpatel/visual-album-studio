from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .ids import new_id

_REDACT_KEYS = ("token", "secret", "authorization", "refresh", "access")


@dataclass
class ProviderPublishRequestV1:
    provider: str
    channel_profile_id: str
    file_path: str
    title: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    privacy_status: str = "private"
    schedule_at: str | None = None
    quota_budget: int = 10000
    quota_used: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "provider": self.provider,
            "channel_profile_id": self.channel_profile_id,
            "file_path": self.file_path,
            "title": self.title,
            "description": self.description,
            "tags": list(self.tags),
            "privacy_status": self.privacy_status,
            "schedule_at": self.schedule_at,
            "quota_budget": int(self.quota_budget),
            "quota_used": int(self.quota_used),
            "metadata": dict(self.metadata),
        }


@dataclass
class ProviderPublishStatusV1:
    provider: str
    ok: bool
    state: str
    publish_id: str = ""
    error_code: str = ""
    retryable: bool = False
    http_status: int = 200
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "provider": self.provider,
            "ok": bool(self.ok),
            "state": self.state,
            "publish_id": self.publish_id,
            "error_code": self.error_code,
            "retryable": bool(self.retryable),
            "http_status": int(self.http_status),
            "details": dict(self.details),
        }


class DistributionAdapter:
    provider: str = ""

    def preflight(self, request: ProviderPublishRequestV1) -> ProviderPublishStatusV1:
        raise NotImplementedError

    def publish(self, request: ProviderPublishRequestV1) -> ProviderPublishStatusV1:
        raise NotImplementedError


class ProviderPolicyPreflight:
    @staticmethod
    def check_quota(request: ProviderPublishRequestV1, estimated_units: int) -> ProviderPublishStatusV1:
        remaining = int(request.quota_budget) - int(request.quota_used)
        if estimated_units > remaining:
            return ProviderPublishStatusV1(
                provider=request.provider,
                ok=False,
                state="failed",
                error_code="E_PROVIDER_QUOTA_EXCEEDED",
                retryable=False,
                http_status=429,
                details={"estimated_units": estimated_units, "remaining": remaining},
            )
        return ProviderPublishStatusV1(
            provider=request.provider,
            ok=True,
            state="preflight_ok",
            details={"estimated_units": estimated_units, "remaining": remaining},
        )


class TikTokDistributionAdapter(DistributionAdapter):
    provider = "tiktok"

    def preflight(self, request: ProviderPublishRequestV1) -> ProviderPublishStatusV1:
        if len(request.title.strip()) == 0:
            return ProviderPublishStatusV1(self.provider, False, "failed", error_code="E_TIKTOK_TITLE_REQUIRED", http_status=400)
        quota = ProviderPolicyPreflight.check_quota(request, estimated_units=120)
        if not quota.ok:
            return quota
        if bool(request.metadata.get("simulate_policy_block", False)):
            return ProviderPublishStatusV1(
                self.provider,
                False,
                "failed",
                error_code="E_TIKTOK_POLICY_BLOCKED",
                retryable=False,
                http_status=403,
            )
        return ProviderPublishStatusV1(self.provider, True, "preflight_ok", details=quota.details)

    def publish(self, request: ProviderPublishRequestV1) -> ProviderPublishStatusV1:
        preflight = self.preflight(request)
        if not preflight.ok:
            return preflight
        if bool(request.metadata.get("simulate_retryable", False)):
            return ProviderPublishStatusV1(
                self.provider,
                False,
                "failed",
                error_code="E_TIKTOK_TRANSIENT",
                retryable=True,
                http_status=503,
            )
        publish_id = "tt_" + hashlib.sha256(request.file_path.encode("utf-8")).hexdigest()[:12]
        return ProviderPublishStatusV1(self.provider, True, "succeeded", publish_id=publish_id, http_status=200)


class InstagramDistributionAdapter(DistributionAdapter):
    provider = "instagram"

    def preflight(self, request: ProviderPublishRequestV1) -> ProviderPublishStatusV1:
        if len(request.description) > 2200:
            return ProviderPublishStatusV1(
                self.provider, False, "failed", error_code="E_INSTAGRAM_CAPTION_TOO_LONG", retryable=False, http_status=400
            )
        quota = ProviderPolicyPreflight.check_quota(request, estimated_units=130)
        if not quota.ok:
            return quota
        if bool(request.metadata.get("simulate_policy_block", False)):
            return ProviderPublishStatusV1(
                self.provider,
                False,
                "failed",
                error_code="E_INSTAGRAM_POLICY_BLOCKED",
                retryable=False,
                http_status=403,
            )
        return ProviderPublishStatusV1(self.provider, True, "preflight_ok", details=quota.details)

    def publish(self, request: ProviderPublishRequestV1) -> ProviderPublishStatusV1:
        preflight = self.preflight(request)
        if not preflight.ok:
            return preflight
        if bool(request.metadata.get("simulate_retryable", False)):
            return ProviderPublishStatusV1(
                self.provider,
                False,
                "failed",
                error_code="E_INSTAGRAM_TRANSIENT",
                retryable=True,
                http_status=503,
            )
        publish_id = "ig_" + hashlib.sha256((request.file_path + request.title).encode("utf-8")).hexdigest()[:12]
        return ProviderPublishStatusV1(self.provider, True, "succeeded", publish_id=publish_id, http_status=200)


class FacebookReelsDistributionAdapter(DistributionAdapter):
    provider = "facebook_reels"

    def preflight(self, request: ProviderPublishRequestV1) -> ProviderPublishStatusV1:
        if len(request.title.strip()) == 0:
            return ProviderPublishStatusV1(
                self.provider, False, "failed", error_code="E_FB_REELS_TITLE_REQUIRED", retryable=False, http_status=400
            )
        quota = ProviderPolicyPreflight.check_quota(request, estimated_units=140)
        if not quota.ok:
            return quota
        if bool(request.metadata.get("simulate_policy_block", False)):
            return ProviderPublishStatusV1(
                self.provider,
                False,
                "failed",
                error_code="E_FB_REELS_POLICY_BLOCKED",
                retryable=False,
                http_status=403,
            )
        return ProviderPublishStatusV1(self.provider, True, "preflight_ok", details=quota.details)

    def publish(self, request: ProviderPublishRequestV1) -> ProviderPublishStatusV1:
        preflight = self.preflight(request)
        if not preflight.ok:
            return preflight
        if bool(request.metadata.get("simulate_retryable", False)):
            return ProviderPublishStatusV1(
                self.provider,
                False,
                "failed",
                error_code="E_FB_REELS_TRANSIENT",
                retryable=True,
                http_status=503,
            )
        publish_id = "fr_" + hashlib.sha256((request.file_path + request.channel_profile_id).encode("utf-8")).hexdigest()[:12]
        return ProviderPublishStatusV1(self.provider, True, "succeeded", publish_id=publish_id, http_status=200)


class XDistributionAdapter(DistributionAdapter):
    provider = "x"

    def preflight(self, request: ProviderPublishRequestV1) -> ProviderPublishStatusV1:
        char_count = len(request.title.strip()) + len(request.description.strip())
        if char_count == 0:
            return ProviderPublishStatusV1(self.provider, False, "failed", error_code="E_X_TEXT_REQUIRED", retryable=False, http_status=400)
        if char_count > 280:
            return ProviderPublishStatusV1(self.provider, False, "failed", error_code="E_X_TEXT_TOO_LONG", retryable=False, http_status=400)
        quota = ProviderPolicyPreflight.check_quota(request, estimated_units=110)
        if not quota.ok:
            return quota
        if bool(request.metadata.get("simulate_policy_block", False)):
            return ProviderPublishStatusV1(
                self.provider,
                False,
                "failed",
                error_code="E_X_POLICY_BLOCKED",
                retryable=False,
                http_status=403,
            )
        return ProviderPublishStatusV1(self.provider, True, "preflight_ok", details=quota.details)

    def publish(self, request: ProviderPublishRequestV1) -> ProviderPublishStatusV1:
        preflight = self.preflight(request)
        if not preflight.ok:
            return preflight
        if bool(request.metadata.get("simulate_retryable", False)):
            return ProviderPublishStatusV1(
                self.provider,
                False,
                "failed",
                error_code="E_X_TRANSIENT",
                retryable=True,
                http_status=503,
            )
        publish_id = "x_" + hashlib.sha256((request.file_path + request.title + request.description).encode("utf-8")).hexdigest()[:12]
        return ProviderPublishStatusV1(self.provider, True, "succeeded", publish_id=publish_id, http_status=200)


class DistributionServiceV2:
    def __init__(self, db=None, *, feature_flags=None):
        self.db = db
        self.feature_flags = feature_flags
        self.adapters: dict[str, DistributionAdapter] = {
            "tiktok": TikTokDistributionAdapter(),
            "instagram": InstagramDistributionAdapter(),
            "facebook_reels": FacebookReelsDistributionAdapter(),
            "x": XDistributionAdapter(),
        }

    def register_adapter(self, adapter: DistributionAdapter) -> None:
        self.adapters[adapter.provider] = adapter

    def _adapter(self, provider: str) -> DistributionAdapter | None:
        return self.adapters.get(provider)

    def _provider_enabled(self, provider: str) -> bool:
        if self.feature_flags is None:
            return True
        if not hasattr(self.feature_flags, "is_enabled"):
            return True
        return bool(self.feature_flags.is_enabled(provider))

    def preflight_publish(self, request: ProviderPublishRequestV1) -> dict[str, Any]:
        if not self._provider_enabled(request.provider):
            return ProviderPublishStatusV1(
                request.provider,
                False,
                "failed",
                error_code="E_PROVIDER_FEATURE_DISABLED",
                retryable=False,
                http_status=423,
            ).to_dict()
        adapter = self._adapter(request.provider)
        if adapter is None:
            return ProviderPublishStatusV1(
                request.provider, False, "failed", error_code="E_PROVIDER_UNSUPPORTED", retryable=False, http_status=400
            ).to_dict()
        result = adapter.preflight(request)
        return result.to_dict()

    def publish(self, request: ProviderPublishRequestV1) -> dict[str, Any]:
        if not self._provider_enabled(request.provider):
            result = ProviderPublishStatusV1(
                request.provider,
                False,
                "failed",
                error_code="E_PROVIDER_FEATURE_DISABLED",
                retryable=False,
                http_status=423,
            )
            return result.to_dict()
        adapter = self._adapter(request.provider)
        if adapter is None:
            result = ProviderPublishStatusV1(
                request.provider, False, "failed", error_code="E_PROVIDER_UNSUPPORTED", retryable=False, http_status=400
            )
        else:
            result = adapter.publish(request)

        if self.db and request.provider in {"youtube", "tiktok", "instagram", "facebook_reels", "x"}:
            now = int(time.time())
            job_id = new_id("dist_job")
            self.db.execute(
                """
                INSERT INTO distribution_publish_jobs(
                  id, provider, channel_profile_id, request_json, status, error_code, retryable, publish_ref, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    request.provider,
                    request.channel_profile_id,
                    json.dumps(request.to_dict(), sort_keys=True),
                    "succeeded" if result.ok else "failed",
                    result.error_code,
                    1 if result.retryable else 0,
                    result.publish_id,
                    now,
                    now,
                ),
            )
            self.db.commit()
        return result.to_dict()

    def log_connector_diagnostic(
        self,
        connector: str,
        payload: dict[str, Any],
        severity: str = "info",
        *,
        project_id: str,
    ) -> str:
        if not self.db:
            return ""
        now = int(time.time())
        diag_id = new_id("diag")
        self.db.execute(
            "INSERT INTO connector_diagnostics(id, project_id, connector, severity, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (diag_id, str(project_id), connector, severity, json.dumps(_redact_payload(payload), sort_keys=True), now),
        )
        self.db.commit()
        return diag_id


def _redact_payload(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            key_str = str(key)
            if any(token in key_str.lower() for token in _REDACT_KEYS):
                out[key_str] = "[REDACTED]"
            else:
                out[key_str] = _redact_payload(item)
        return out
    if isinstance(value, list):
        return [_redact_payload(item) for item in value]
    if isinstance(value, str):
        lowered = value.lower()
        if "bearer " in lowered or "refresh_token" in lowered or "client_secret" in lowered or "access_token" in lowered:
            return "[REDACTED]"
    return value


def make_request(
    *,
    provider: str,
    channel_profile_id: str,
    file_path: str,
    title: str,
    description: str = "",
    quota_budget: int = 10000,
    quota_used: int = 0,
    metadata: dict[str, Any] | None = None,
) -> ProviderPublishRequestV1:
    if not Path(file_path).exists():
        # Keep non-runtime tests deterministic by allowing missing files when explicitly simulated.
        if not (metadata or {}).get("allow_missing_file", False):
            raise FileNotFoundError(file_path)
    return ProviderPublishRequestV1(
        provider=provider,
        channel_profile_id=channel_profile_id,
        file_path=file_path,
        title=title,
        description=description,
        quota_budget=quota_budget,
        quota_used=quota_used,
        metadata=metadata or {},
    )
