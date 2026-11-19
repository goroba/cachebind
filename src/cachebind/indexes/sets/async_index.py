"""Asynchronous set index."""

from collections.abc import AsyncIterable, AsyncIterator, Hashable, Sequence
from typing import Self

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

    async def add(self, client: ClientType, member: MemberType) -> None:
        """Add ``member``. A member that is already present is not an error."""
        await self.storage.add(client, self.key, self.serializer.serialize(member))

    async def madd(self, client: ClientType, members: Sequence[MemberType]) -> None:
        """Add every member."""
        if not members:
            return
        await self.storage.madd(client, self.key, self.serializer.mserialize(members))

    async def remove(self, client: ClientType, member: MemberType) -> None:
        """Remove ``member``. A missing member is not an error."""
        await self.storage.remove(client, self.key, self.serializer.serialize(member))

    async def mremove(self, client: ClientType, members: Sequence[MemberType]) -> None:
        """Remove every member. Missing members are not an error."""
        if not members:
            return
        await self.storage.mremove(client, self.key, self.serializer.mserialize(members))

    async def contains(self, client: ClientType, member: MemberType) -> bool:
        """Return whether ``member`` is in the set."""
        return await self.storage.contains(client, self.key, self.serializer.serialize(member))

    async def swap(self, client: ClientType) -> Self:
        """Rename this index aside and return an unregistered index for that data."""
        return self.detach(await self.storage.swap(client, self.key))

    async def drop(self, client: ClientType) -> None:
        """Delete the key this index is bound to. A missing key is not an error."""
        await self.storage.drop(client, self.key)

    async def iter(self, client: ClientType) -> AsyncIterator[MemberType]:
        """Yield each member stored under this index key."""
        async for member in async_values(self.storage.iter(client, self.key), self.serializer):
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
