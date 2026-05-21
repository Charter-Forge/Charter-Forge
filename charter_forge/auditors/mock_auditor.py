from charter_forge.types import AuditorUnavailable


class MockAuditor:
    def __init__(self, *, reply_template: str | None, raise_unavailable: bool = False) -> None:
        self.reply_template = reply_template
        self.raise_unavailable = raise_unavailable

    def audit(self, *, prompt: str, nonce: str) -> str:
        if self.raise_unavailable or self.reply_template is None:
            raise AuditorUnavailable("mock configured to fail")
        return self.reply_template.format(nonce=nonce)
