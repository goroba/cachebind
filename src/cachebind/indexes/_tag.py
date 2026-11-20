"""Encode cache tags for index writes."""

from __future__ import annotations

from typing import Protocol

from cachebind.tagging import TagMaker


class _TagSource(Protocol):
    key: str
    tag_maker: TagMaker


def make_tag(index: _TagSource, identifier: str) -> str:
    """Return a tag for ``identifier`` under this index's key."""
    return index.tag_maker.encode(index.key, identifier)


def storage_identifier(value: object) -> str:
    """Turn a serialized storage value into the identifier string used in tags."""
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)