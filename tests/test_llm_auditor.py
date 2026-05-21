from unittest.mock import MagicMock, patch

import pytest

from charter_forge.auditors.llm_auditor import LLMAuditor


def test_calls_litellm() -> None:
    resp = MagicMock()
    resp.choices = [
        MagicMock(message=MagicMock(content="<<<UNTRUSTED_OUTPUT_END>>>\nVERDICT=PASS NONCE=n"))
    ]
    with patch("charter_forge.auditors.llm_auditor.completion", return_value=resp):
        a = LLMAuditor(model="claude-3-5-haiku-20241022", timeout_s=10)
        assert "VERDICT=PASS" in a.audit(prompt="rules", nonce="n")


def test_raises_on_error() -> None:
    with patch("charter_forge.auditors.llm_auditor.completion", side_effect=RuntimeError("boom")):
        a = LLMAuditor(model="x", timeout_s=10)
        with pytest.raises(RuntimeError):
            a.audit(prompt="x", nonce="n")
