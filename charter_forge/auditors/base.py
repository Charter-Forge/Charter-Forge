from typing import Protocol


class AuditorProtocol(Protocol):
    def audit(self, *, prompt: str, nonce: str) -> str: ...
