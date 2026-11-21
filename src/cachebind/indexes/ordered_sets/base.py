"""Shared ordered-set index attributes."""

from __future__ import annotations

from collections.abc import Hashable

from cachebind.indexes.base import Index
from cachebind.serializers.serializer import Serializer
from cachebind.tagging import Breadcrumbs, NoopBreadcrumbs
from cachebind.storage.ordered_sets.async_storage import AsyncOrderedSetStorage
from cachebind.storage.ordered_sets.storage import OrderedSetStorage


class OrderedSetBase[ClientType, MemberType, StorageType: Hashable](Index):
    """Member, serializer, storage key, and storage for an ordered-set index.

    ``key`` is the ordered set name. ``storage`` stores serialized members and scores.
    Each call receives the storage client.
    """

    member: type[MemberType]
    breadcrumbs: Breadcrumbs = NoopBreadcrumbs()
    serializer: Serializer[MemberType, StorageType]
    storage: (
        OrderedSetStorage[ClientType, StorageType]
        | AsyncOrderedSetStorage[ClientType, StorageType]
    )


def _empty_range(start: int, stop: int) -> bool:
    """Return whether this inclusive rank window has no members.

    Both ends must be negative, or both non-negative, and ``start`` must be past
    ``stop``. Mixed signs depend on the length of the ordered set.
    """
    if (start >= 0) != (stop >= 0):
        return False
    return start > stop
