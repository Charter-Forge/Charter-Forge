import re

from charter_forge.fencing import END_MARKER
from charter_forge.nonce import NONCE_REGEX
from charter_forge.types import AuditResult, Verdict

_VERDICT_LINE = re.compile(r"VERDICT=([A-Z_]+)")
_RULES = re.compile(r"RULES=([0-9,]*)")
_REASON = re.compile(r"REASON=(.+?)(?:\s+NONCE=|$)")
_ALLOWED = {"PASS", "VIOLATION"}


def parse_verdict(raw: str, *, nonce: str) -> AuditResult:
    """Parse an auditor reply. Fail-CLOSED on any uncertainty.

    Rules:
    - No END marker -> UNPARSEABLE
    - No VERDICT after the END marker -> UNPARSEABLE
    - Dual VERDICT on one line -> VIOLATION (classic injection shape)
    - Missing or wrong nonce -> UNPARSEABLE
    - Unknown VERDICT token -> UNPARSEABLE
    """
    if END_MARKER not in raw:
        return AuditResult(Verdict.UNPARSEABLE, [], "no end marker", raw)
    tail = raw.split(END_MARKER, 1)[1]

    verdicts = _VERDICT_LINE.findall(tail)
    if not verdicts:
        return AuditResult(Verdict.UNPARSEABLE, [], "no VERDICT", raw)

    for line in tail.splitlines():
        if len(_VERDICT_LINE.findall(line)) > 1:
            return AuditResult(Verdict.VIOLATION, [], "dual VERDICT one line", raw)

    nm = NONCE_REGEX.search(tail)
    if not nm or nm.group(1) != nonce:
        return AuditResult(Verdict.UNPARSEABLE, [], "missing or wrong nonce", raw)

    v = verdicts[0]
    if v not in _ALLOWED:
        return AuditResult(Verdict.UNPARSEABLE, [], f"unknown verdict {v}", raw)

    rules: list[int] = []
    rm = _RULES.search(tail)
    if rm and rm.group(1):
        rules = [int(x) for x in rm.group(1).split(",") if x.strip().isdigit()]

    reason_m = _REASON.search(tail)
    reason = reason_m.group(1).strip() if reason_m else ""

    return AuditResult(Verdict(v), rules, reason, raw)