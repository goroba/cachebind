"""Asynchronous set index."""

from collections.abc import AsyncIterable, AsyncIterator, Hashable, Sequence
from contextlib import asynccontextmanager
from typing import Self, cast

from cachebind.indexes._replace import async_replace_context, async_snapshot_context
from cachebind.indexes._serializer import resolve_serializer
from cachebind.indexes._breadcrumb import storage_identifier
from cachebind.indexes.sets.base import SetBase
from cachebind.serializers.serializer import Serializer
from cachebind.storage.sets.async_storage import AsyncSetStorage

BATCH = 100


class AsyncSetIndex[ClientType, MemberType, StorageType: Hashable](
    SetBase[ClientType, MemberType, StorageType]
):
    """Async set index: member binding, storage key, and the storage that persists it.

    Writes serialize the member. ``contains`` serializes the lookup value.
    """

    storage: AsyncSetStorage[ClientType, StorageType]

    async def add(
        self,
        client: ClientType,
        member: MemberType,
        **kwargs,
    ) -> str:
        """Add ``member``. A member that is already present is not an error."""
        serializer = resolve_serializer(self.serializer, kwargs)
        stored = serializer.serialize(member)
        await self.storage.add(client, self.key, stored)
        return self.breadcrumbs.encode(self.key, storage_identifier(stored))

    async def madd(
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
        await self.storage.madd(client, self.key, stored)
        return [
            self.breadcrumbs.encode(self.key, storage_identifier(value)) for value in stored
        ]

    async def remove(
        self,
        client: ClientType,
        member: MemberType,
        **kwargs,
    ) -> None:
        """Remove ``member``. A missing member is not an error."""
        serializer = resolve_serializer(self.serializer, kwargs)
        await self.storage.remove(client, self.key, serializer.serialize(member))

    async def evict(self, client: ClientType, identifier: str) -> None:
        """Remove the entry for ``identifier``. A missing entry is not an error.

        ``identifier`` is the tag payload for one member (not the full encoded tag).
        """
        await self.storage.remove(client, self.key, cast(StorageType, identifier))

    async def mremove(
        self,
        client: ClientType,
        members: Sequence[MemberType],
        **kwargs,
    ) -> None:
        """Remove every member. Missing members are not an error."""
        if not members:
            return
        serializer = resolve_serializer(self.serializer, kwargs)
        await self.storage.mremove(client, self.key, serializer.mserialize(members))

    async def contains(
        self,
        client: ClientType,
        member: MemberType,
        **kwargs,
    ) -> bool:
        """Return whether ``member`` is in the set."""
        serializer = resolve_serializer(self.serializer, kwargs)
        return await self.storage.contains(client, self.key, serializer.serialize(member))

    @asynccontextmanager
    async def snapshot(self, client: ClientType):
        """Yield an unregistered index for the data that was live on enter; drop it on success."""
        async with async_snapshot_context(self, client) as detached:
            yield detached

    @asynccontextmanager
    async def replace(self, client: ClientType):
        """Yield a detached staging index; publish it on success or drop it on failure."""
        async with async_replace_context(self, client) as staging:
            yield staging

    async def drop(self, client: ClientType) -> None:
        """Delete the key this index is bound to. A missing key is not an error."""
        await self.storage.drop(client, self.key)

    async def iter(
        self,
        client: ClientType,
        **kwargs,
    ) -> AsyncIterator[MemberType]:
        """Yield each member stored under this index key."""
        serializer = resolve_serializer(self.serializer, kwargs)
        async for member in async_values(self.storage.iter(client, self.key), serializer):
            yield member


async def async_values[StorageType, ValueType](
    raw: AsyncIterable[StorageType], serializer: Serializer[ValueType, StorageType]
) -> AsyncIterator[ValueType]:
    """Yield deserialized values, calling ``mdeserialize`` once per batch."""
    batch: list[StorageType] = []
    async for value in raw:
        batch.append(value)
        if len(batch) == BATCH:
            for decoded in serializer.mdeserialize(batch):
                yield decoded
            batch = []
    if batch:
        for decoded in serializer.mdeserialize(batch):
            yield decoded
