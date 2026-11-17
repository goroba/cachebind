"""Asynchronous ordered-set index."""

from collections.abc import Hashable, Sequence

from cacher.indexes.ordered_sets.base import OrderedSetBase, _empty_range
from cacher.storage.ordered_sets.async_storage import AsyncOrderedSetStorage


class AsyncOrderedSetIndex[ClientType, MemberType, StorageType: Hashable](
    OrderedSetBase[ClientType, MemberType, StorageType]
):
    """Async ordered-set index: member binding, storage key, and the storage that persists it.

    Writes serialize the member and pass the score through. Reads deserialize members.
    """

    storage: AsyncOrderedSetStorage[ClientType, StorageType]

    async def add(self, client: ClientType, member: MemberType, score: float) -> None:
        """Add ``member`` with ``score``. A member that is already present gets the new score."""
        await self.storage.add(client, self.key, self.serializer.serialize(member), score)

    async def madd(
        self, client: ClientType, members: Sequence[tuple[MemberType, float]]
    ) -> None:
        """Add every member with its score. A repeated member keeps the last score."""
        if not members:
            return
        serialized = [(self.serializer.serialize(member), score) for member, score in members]
        await self.storage.madd(client, self.key, serialized)

    async def remove(self, client: ClientType, member: MemberType) -> None:
        """Remove ``member``. A missing member is not an error."""
        await self.storage.remove(client, self.key, self.serializer.serialize(member))

    async def mremove(self, client: ClientType, members: Sequence[MemberType]) -> None:
        """Remove every member. Missing members are not an error."""
        if not members:
            return
        serialized = [self.serializer.serialize(member) for member in members]
        await self.storage.mremove(client, self.key, serialized)

    async def contains(self, client: ClientType, member: MemberType) -> bool:
        """Return whether ``member`` is in the ordered set."""
        return await self.storage.contains(client, self.key, self.serializer.serialize(member))

    async def score(self, client: ClientType, member: MemberType) -> float | None:
        """Return the score of ``member``, or ``None`` when it is missing."""
        return await self.storage.score(client, self.key, self.serializer.serialize(member))

    async def rank(self, client: ClientType, member: MemberType) -> int | None:
        """Return the 0-based ascending rank of ``member``, or ``None`` when it is missing."""
        return await self.storage.rank(client, self.key, self.serializer.serialize(member))

    async def range(self, client: ClientType, start: int, stop: int) -> list[MemberType]:
        """Return members from ``start`` through ``stop``, both inclusive."""
        if _empty_range(start, stop):
            return []
        raw = await self.storage.range(client, self.key, start, stop)
        return [self.serializer.deserialize(member) for member in raw]

    async def range_with_scores(
        self, client: ClientType, start: int, stop: int
    ) -> list[tuple[MemberType, float]]:
        """Return members and scores from ``start`` through ``stop``, both inclusive."""
        if _empty_range(start, stop):
            return []
        raw = await self.storage.range_with_scores(client, self.key, start, stop)
        return [(self.serializer.deserialize(member), score) for member, score in raw]

    async def rev_rank(self, client: ClientType, member: MemberType) -> int | None:
        """Return the 0-based descending rank of ``member``, or ``None`` when it is missing."""
        return await self.storage.rev_rank(client, self.key, self.serializer.serialize(member))

    async def rev_range(self, client: ClientType, start: int, stop: int) -> list[MemberType]:
        """Return members from ``start`` through ``stop``, both inclusive, highest score first."""
        if _empty_range(start, stop):
            return []
        raw = await self.storage.rev_range(client, self.key, start, stop)
        return [self.serializer.deserialize(member) for member in raw]

    async def rev_range_with_scores(
        self, client: ClientType, start: int, stop: int
    ) -> list[tuple[MemberType, float]]:
        """Return members and scores from ``start`` through ``stop``, highest score first."""
        if _empty_range(start, stop):
            return []
        raw = await self.storage.rev_range_with_scores(client, self.key, start, stop)
        return [(self.serializer.deserialize(member), score) for member, score in raw]
