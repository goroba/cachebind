"""Tag keeper storage key helpers."""

TAG_KEEPER_PREFIX = "tag_keeper"

DEFAULT_TAG_KEEPER_NAME = "default"


def tag_set_key(name: str, tag: str) -> str:
    """Set storage key for one tag under a keeper name."""
    return f"{TAG_KEEPER_PREFIX}:{name}:{tag}"