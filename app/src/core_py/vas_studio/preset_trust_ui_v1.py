from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from .ids import new_id
from .preset_exchange_v1 import PresetExchangeServiceV1


@dataclass
class PresetTrustStateV1:
    view_state: str
    signature_state: str
    provenance_state: str
    focus_order: list[str] = field(default_factory=list)
    keyboard_hints: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": int(self.schema_version),
            "view_state": self.view_state,
            "signature_state": self.signature_state,
            "provenance_state": self.provenance_state,
            "focus_order": list(self.focus_order),
            "keyboard_hints": list(self.keyboard_hints),
            "messages": list(self.messages),
        }


class PresetTrustUxServiceV1:
    def __init__(self, db, *, exchange_service: PresetExchangeServiceV1 | None = None):
        self.db = db
        self.exchange_service = exchange_service or PresetExchangeServiceV1(db)

    @staticmethod
    def _now() -> int:
        return int(time.time())

    def state_matrix(
        self,
        *,
        bundle_payload: dict[str, Any] | None,
        is_loading: bool = False,
        disabled: bool = False,
        keyboard_only: bool = True,
    ) -> dict[str, Any]:
        focus_order = ["signature_panel", "provenance_panel", "import_button", "details_toggle"]
        keyboard_hints = ["Tab", "Shift+Tab", "Enter", "Space"] if keyboard_only else []

        if is_loading:
            state = PresetTrustStateV1(
                view_state="loading",
                signature_state="unknown",
                provenance_state="pending",
                focus_order=focus_order,
                keyboard_hints=keyboard_hints,
                messages=["Loading preset trust metadata"],
            )
            return {"ok": True, "state": state.to_dict()}

        if bundle_payload is None:
            state = PresetTrustStateV1(
                view_state="empty",
                signature_state="unknown",
                provenance_state="unknown",
                focus_order=focus_order,
                keyboard_hints=keyboard_hints,
                messages=["No preset selected"],
            )
            return {"ok": True, "state": state.to_dict()}

        compatibility = self.exchange_service.compatibility_report(bundle_payload)
        verification = self.exchange_service.verify_signature(bundle_payload)

        messages: list[str] = []
        if not compatibility["ok"]:
            messages.extend(list(compatibility["issues"]))
        if not verification["ok"]:
            messages.append(str(verification.get("error_code", "E_PRESET_SIGNATURE_INVALID")))

        if disabled:
            state = PresetTrustStateV1(
                view_state="disabled",
                signature_state="valid" if verification["ok"] else "invalid",
                provenance_state="valid" if compatibility["ok"] else "invalid",
                focus_order=focus_order,
                keyboard_hints=keyboard_hints,
                messages=messages or ["Import disabled"],
            )
            return {"ok": True, "state": state.to_dict()}

        if not compatibility["ok"] or not verification["ok"]:
            state = PresetTrustStateV1(
                view_state="error",
                signature_state="valid" if verification["ok"] else "invalid",
                provenance_state="valid" if compatibility["ok"] else "invalid",
                focus_order=focus_order,
                keyboard_hints=keyboard_hints,
                messages=messages,
            )
            return {"ok": True, "state": state.to_dict()}

        state = PresetTrustStateV1(
            view_state="success",
            signature_state="valid",
            provenance_state="valid",
            focus_order=focus_order,
            keyboard_hints=keyboard_hints,
            messages=["Preset signature and provenance verified"],
        )
        return {"ok": True, "state": state.to_dict()}

    def record_state(self, *, preset_id: str, actor_id: str, state_payload: dict[str, Any]) -> dict[str, Any]:
        event_id = new_id("preset_trust")
        now = self._now()
        signature_valid = 1 if str(state_payload.get("signature_state", "")).lower() == "valid" else 0
        provenance = {
            "provenance_state": state_payload.get("provenance_state"),
            "messages": state_payload.get("messages", []),
        }
        self.db.execute(
            "INSERT INTO preset_trust_ui_events(id, preset_id, actor_id, state, signature_valid, provenance_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                event_id,
                preset_id,
                actor_id,
                str(state_payload.get("view_state", "unknown")),
                signature_valid,
                json.dumps(provenance, sort_keys=True),
                now,
            ),
        )
        self.db.commit()
        return {"ok": True, "event_id": event_id, "created_at": now}
