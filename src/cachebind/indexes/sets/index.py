"""Synchronous set index."""

from collections.abc import Hashable, Iterable, Iterator, Sequence
from contextlib import contextmanager
from typing import Self, cast

from cachebind.indexes._replace import replace_context, snapshot_context
from cachebind.indexes._serializer import resolve_serializer
from cachebind.indexes._breadcrumb import storage_identifier
from cachebind.indexes.sets.base import SetBase
from cachebind.serializers.serializer import Serializer
from cachebind.storage.sets.storage import SetStorage

BATCH = 100


class SetIndex[ClientType, MemberType, StorageType: Hashable](
    SetBase[ClientType, MemberType, StorageType]
):
    """Sync set index: member binding, storage key, and the storage that persists it.

    Writes serialize the member. ``contains`` serializes the lookup value.
    """

    storage: SetStorage[ClientType, StorageType]

    def add(
        self,
        client: ClientType,
        member: MemberType,
        **kwargs,
    ) -> str:
        """Add ``member``. A member that is already present is not an error."""
        serializer = resolve_serializer(self.serializer, kwargs)
        stored = serializer.serialize(member)
        self.storage.add(client, self.key, stored)
        return self.breadcrumbs.encode(self.key, storage_identifier(stored))

    def madd(
        self,
        client: ClientType,
        members: Sequence[MemberType],
        **kwargs,
    ) -> list[str]:
        """Add every member."""
        if not members:
            return []
        serializer = resolve_serializer(self.serializer, kwargs)
        stored = serializer.mserialize(members)
        self.storage.madd(client, self.key, stored)
        return [
            self.breadcrumbs.encode(self.key, storage_identifier(value)) for value in stored
        ]

    def remove(
        self,
        client: ClientType,
        member: MemberType,
        **kwargs,
    ) -> None:
        """Remove ``member``. A missing member is not an error."""
        serializer = resolve_serializer(self.serializer, kwargs)
        self.storage.remove(client, self.key, serializer.serialize(member))

    def evict(self, client: ClientType, identifier: str) -> None:
        """Remove the entry for ``identifier``. A missing entry is not an error.

        ``identifier`` is the tag payload for one member (not the full encoded tag).
        """
        self.storage.remove(client, self.key, cast(StorageType, identifier))

    def mremove(
        self,
        client: ClientType,
        members: Sequence[MemberType],
        **kwargs,
    ) -> None:
        """Remove every member. Missing members are not an error."""
        if not members:
            return
        serializer = resolve_serializer(self.serializer, kwargs)
        self.storage.mremove(client, self.key, serializer.mserialize(members))

    def contains(
        self,
        client: ClientType,
        member: MemberType,
        **kwargs,
    ) -> bool:
        """Return whether ``member`` is in the set."""
        serializer = resolve_serializer(self.serializer, kwargs)
        return self.storage.contains(client, self.key, serializer.serialize(member))

    @contextmanager
    def snapshot(self, client: ClientType):
        """Yield an unregistered index for the data that was live on enter; drop it on success."""
        with snapshot_context(self, client) as detached:
            yield detached

    @contextmanager
    def replace(self, client: ClientType):
        """Yield a detached staging index; publish it on success or drop it on failure."""
        with replace_context(self, client) as staging:
            yield staging

    def drop(self, client: ClientType) -> None:
        """Delete the key this index is bound to. A missing key is not an error."""
        self.storage.drop(client, self.key)

    def iter(
        self,
        client: ClientType,
        **kwargs,
    ) -> Iterator[MemberType]:
        """Yield each member stored under this index key."""
        serializer = resolve_serializer(self.serializer, kwargs)
        return values(self.storage.iter(client, self.key), serializer)


def values[StorageType, ValueType](
    raw: Iterable[StorageType], serializer: Serializer[ValueType, StorageType]
) -> Iterator[ValueType]:
    """Yield deserialized values, calling ``mdeserialize`` once per batch."""
    batch: list[StorageType] = []
    for value in raw:
        batch.append(value)
        if len(batch) == BATCH:
            yield from serializer.mdeserialize(batch)
            batch = []
    if batch:
        yield from serializer.mdeserialize(batch)
