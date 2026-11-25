"""Redis suggestion-dictionary (FT.SUG*) wire helpers."""

from cachebind.backends.redis.decode import required_text

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


def payloads_from_suggestions(raw: object) -> list[str]:
    """Return payloads from a flat suggestion reply of string, payload, string, payload."""
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise TypeError(f"unexpected Redis suggestion type: {type(raw).__name__}")
    if len(raw) % 2 != 0:
        raise TypeError(f"unexpected Redis suggestion reply length: {len(raw)}")
    payloads: list[str] = []
    for index in range(0, len(raw), 2):
        payload = raw[index + 1]
        if payload is None:
            raise ValueError("trie suggestion has no payload")
        payloads.append(required_text(payload))
    return payloads