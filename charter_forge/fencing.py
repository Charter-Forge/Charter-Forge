BEGIN_MARKER = "<<<UNTRUSTED_OUTPUT_BEGIN>>>"
END_MARKER = "<<<UNTRUSTED_OUTPUT_END>>>"


def strip_markers(text: str) -> str:
    """Remove any pre-existing fence markers so the producer cannot close the fence."""
    return text.replace(BEGIN_MARKER, "").replace(END_MARKER, "")


def fence(content: str) -> str:
    """Wrap content in BEGIN/END markers after stripping any pre-existing markers."""
    return f"{BEGIN_MARKER}\n{strip_markers(content)}\n{END_MARKER}"