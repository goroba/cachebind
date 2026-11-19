"""Decode Redis suggestion replies and build suggestion commands."""

DEFAULT_LIMIT = 10


def check_limit(limit: int) -> None:
    """Raise ``ValueError`` unless ``limit`` is a positive integer."""
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError(f"trie limit must be a positive int, got {limit!r}")


def sugadd_command(
    name: str, string: str, score: float, payload: str, *, increment: bool
) -> list[object]:
    """Return an ``FT.SUGADD`` command. ``INCR`` updates the score instead of replacing it."""
    command: list[object] = ["FT.SUGADD", name, string, score]
    if increment:
        command.append("INCR")
    command.extend(("PAYLOAD", payload))
    return command


def sugget_command(name: str, prefix: str, *, fuzzy: bool, limit: int) -> list[object]:
    """Return an ``FT.SUGGET`` command that asks for payloads, highest score first."""
    check_limit(limit)
    command: list[object] = ["FT.SUGGET", name, prefix, "MAX", limit, "WITHPAYLOADS"]
    if fuzzy:
        command.append("FUZZY")
    return command


def length_value(value: object) -> int:
    """Return a suggestion-dictionary length. ``bool`` is rejected."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"unexpected Redis suggestion length type: {type(value).__name__}")
    return value
