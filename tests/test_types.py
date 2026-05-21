# tests/test_types.py
from charter_forge.types import AuditorUnavailable, AuditResult, Verdict


def test_verdict_enum_values():
    assert Verdict.PASS.value == "PASS"
    assert Verdict.VIOLATION.value == "VIOLATION"
    assert Verdict.UNPARSEABLE.value == "UNPARSEABLE"
    assert Verdict.AUDITOR_UNAVAILABLE.value == "AUDITOR_UNAVAILABLE"


def test_audit_result_passed_property():
    r1 = AuditResult(verdict=Verdict.PASS, rules=[], reason="ok", raw="x")
    assert r1.passed is True
    r2 = AuditResult(verdict=Verdict.VIOLATION, rules=[2], reason="lie", raw="x")
    assert r2.passed is False
    # Reference AuditorUnavailable so the import is exercised (it's a public symbol
    # that downstream tasks 6/7 depend on); keeps ruff F401 clean without adding a
    # third test function the spec did not specify.
    assert issubclass(AuditorUnavailable, RuntimeError)