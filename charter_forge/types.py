from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum


class Verdict(StrEnum):
    PASS = "PASS"
    VIOLATION = "VIOLATION"
    UNPARSEABLE = "UNPARSEABLE"
    AUDITOR_UNAVAILABLE = "AUDITOR_UNAVAILABLE"


@dataclass(frozen=True)
class AuditResult:
    verdict: Verdict
    rules: Sequence[int]
    reason: str
    raw: str

    @property
    def passed(self) -> bool:
        return self.verdict is Verdict.PASS


class AuditorUnavailable(RuntimeError):
    """Raised when the auditor cascade cannot return a parseable result."""