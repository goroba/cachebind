"""Decode Redis ordered-set members, scores, and ranks."""

from cacher.storage._redis import decode


def empty_range(start: int, stop: int) -> bool:
    """Return whether this inclusive rank window has no members.

    Both ends must be negative, or both non-negative, and ``start`` must be past
    ``stop``. Mixed signs depend on the length of the ordered set.
    """
    if (start >= 0) != (stop >= 0):
        return False
    return start > stop


def member(value: object) -> str:
    decoded = decode(value)
    if decoded is None:
        raise TypeError("unexpected Redis member type: NoneType")
    return decoded


def score_value(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        raise TypeError(f"unexpected Redis score type: {type(value).__name__}")
    return float(value)


def rank_value(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"unexpected Redis rank type: {type(value).__name__}")
    return value


def members_from_range(raw: object) -> list[str]:
    if not isinstance(raw, list):
        raise TypeError(f"unexpected Redis range type: {type(raw).__name__}")
    return [member(item) for item in raw]


def pairs_from_range(raw: object) -> list[tuple[str, float]]:
    if not isinstance(raw, list):
        raise TypeError(f"unexpected Redis range type: {type(raw).__name__}")
    pairs: list[tuple[str, float]] = []
    for item in raw:
        if not isinstance(item, tuple | list) or len(item) != 2:
            raise TypeError(f"unexpected Redis scored member type: {type(item).__name__}")
        member_raw, score_raw = item
        parsed = score_value(score_raw)
        if parsed is None:
            raise TypeError("unexpected Redis score type: NoneType")
        pairs.append((member(member_raw), parsed))
    return pairs
