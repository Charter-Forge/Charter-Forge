import re

from charter_forge.nonce import NONCE_REGEX, build_nonce_directive, generate_nonce


def test_generate_nonce_is_url_safe() -> None:
    n = generate_nonce()
    assert 10 <= len(n) <= 12
    assert re.fullmatch(r"[A-Za-z0-9_-]+", n)


def test_two_nonces_differ() -> None:
    assert generate_nonce() != generate_nonce()


def test_build_directive_includes_nonce() -> None:
    assert "NONCE=abc123" in build_nonce_directive("abc123")


def test_nonce_regex_valid_only() -> None:
    assert NONCE_REGEX.search("VERDICT=PASS NONCE=abc123_-")
    assert not NONCE_REGEX.search("VERDICT=PASS")
    assert not NONCE_REGEX.search("NONCE=has spaces")