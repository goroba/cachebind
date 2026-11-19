"""Synchronous set index."""

from collections.abc import Hashable, Iterable, Iterator, Sequence
from typing import Self

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

    def add(self, client: ClientType, member: MemberType) -> None:
        """Add ``member``. A member that is already present is not an error."""
        self.storage.add(client, self.key, self.serializer.serialize(member))

    def madd(self, client: ClientType, members: Sequence[MemberType]) -> None:
        """Add every member."""
        if not members:
            return
        self.storage.madd(client, self.key, self.serializer.mserialize(members))

    def remove(self, client: ClientType, member: MemberType) -> None:
        """Remove ``member``. A missing member is not an error."""
        self.storage.remove(client, self.key, self.serializer.serialize(member))

    def mremove(self, client: ClientType, members: Sequence[MemberType]) -> None:
        """Remove every member. Missing members are not an error."""
        if not members:
            return
        self.storage.mremove(client, self.key, self.serializer.mserialize(members))

    def contains(self, client: ClientType, member: MemberType) -> bool:
        """Return whether ``member`` is in the set."""
        return self.storage.contains(client, self.key, self.serializer.serialize(member))

    def swap(self, client: ClientType) -> Self:
        """Rename this index aside and return an unregistered index for that data."""
        return self.detach(self.storage.swap(client, self.key))

    def drop(self, client: ClientType) -> None:
        """Delete the key this index is bound to. A missing key is not an error."""
        self.storage.drop(client, self.key)

    def iter(self, client: ClientType) -> Iterator[MemberType]:
        """Yield each member stored under this index key."""
        return values(self.storage.iter(client, self.key), self.serializer)


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
