"""Parse an ``FT.SUGGET ... WITHPAYLOADS`` reply into payload strings."""

from cachebind.storage._redis import required_text


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
