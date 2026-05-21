import pytest

from charter_forge.auditors.mock_auditor import MockAuditor


def test_mock_returns_template_with_nonce() -> None:
    a = MockAuditor(reply_template="<<<UNTRUSTED_OUTPUT_END>>>\nVERDICT=PASS NONCE={nonce}")
    assert "NONCE=n123" in a.audit(prompt="x", nonce="n123")


def test_mock_unavailable_raises() -> None:
    a = MockAuditor(reply_template=None, raise_unavailable=True)
    with pytest.raises(RuntimeError):
        a.audit(prompt="x", nonce="n")
