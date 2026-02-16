from dataclasses import dataclass
from typing import Dict

from .errors import VasError


ALLOWED_TRANSITIONS: Dict[str, set[str]] = {
    "queued": {"running", "canceled"},
    "running": {"paused", "failed", "succeeded", "canceled"},
    "paused": {"running", "canceled"},
    "failed": {"queued", "canceled"},
    "canceled": {"queued"},
    "succeeded": set(),
}


@dataclass
class JobState:
    job_id: str
    status: str = "queued"

    def transition(self, new_status: str) -> None:
        allowed = ALLOWED_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise VasError(
                code="E_JOB_INVALID_TRANSITION",
                message=f"Invalid job transition {self.status} -> {new_status}",
                details={"from": self.status, "to": new_status},
                recoverable=False,
                hint="Use valid transition order",
            )
        self.status = new_status
