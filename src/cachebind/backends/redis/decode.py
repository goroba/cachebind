"""Decode Redis wire values to Python text."""


def decode(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8")
    raise TypeError(f"unexpected Redis value type: {type(value).__name__}")


def required_text(value: object) -> str:
    """Return ``value`` as text. ``None`` is an error."""
    decoded = decode(value)
    if decoded is None:
        raise TypeError(f"unexpected Redis value type: {type(value).__name__}")
    return decoded


def scan_done(cursor: object) -> bool:
    """Return whether a Redis scan cursor marks the end of the walk."""
    if isinstance(cursor, bytes):
        cursor = cursor.decode("utf-8")
    if isinstance(cursor, str):
        return int(cursor) == 0
    if isinstance(cursor, int) and not isinstance(cursor, bool):
        return cursor == 0
    raise TypeError(f"unexpected Redis scan cursor type: {type(cursor).__name__}")


__all__ = ["decode", "required_text", "scan_done"]