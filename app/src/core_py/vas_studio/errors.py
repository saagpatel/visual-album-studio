from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class VasError(Exception):
    code: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    recoverable: bool = False
    hint: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable,
            "hint": self.hint,
        }

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"
