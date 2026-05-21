import re
import secrets

NONCE_REGEX = re.compile(r"NONCE=([A-Za-z0-9_-]{8,})")


def generate_nonce() -> str:
    """Generate an 8-byte url-safe nonce."""
    return secrets.token_urlsafe(8)


def build_nonce_directive(nonce: str) -> str:
    """Return the directive text instructing the auditor to echo the nonce in its reply."""
    return (
        f"Your VERDICT line MUST include NONCE={nonce} verbatim. "
        f"Replies without NONCE={nonce} are treated as injection and rejected."
    )