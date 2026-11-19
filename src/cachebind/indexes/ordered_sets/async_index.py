"""Asynchronous ordered-set index."""

from collections.abc import AsyncIterable, AsyncIterator, Hashable, Iterator, Sequence
from typing import Self

from cachebind.indexes._serializer import resolve_serializer
from cachebind.indexes.ordered_sets.base import OrderedSetBase, _empty_range
from cachebind.serializers.serializer import Serializer
from cachebind.storage.ordered_sets.async_storage import AsyncOrderedSetStorage

BATCH = 100


class AsyncOrderedSetIndex[ClientType, MemberType, StorageType: Hashable](
    OrderedSetBase[ClientType, MemberType, StorageType]
):
    """Async ordered-set index: member binding, storage key, and the storage that persists it.

    Writes serialize the member and pass the score through. Reads deserialize members.
    """

    storage: AsyncOrderedSetStorage[ClientType, StorageType]

    async def add(
        self,
        client: ClientType,
        member: MemberType,
        score: float,
        **kwargs,
    ) -> None:
        """Add ``member`` with ``score``. A member that is already present gets the new score."""
        serializer = resolve_serializer(self.serializer, kwargs)
        await self.storage.add(client, self.key, serializer.serialize(member), score)

    async def madd(
        self,
        client: ClientType,
        members: Sequence[tuple[MemberType, float]],
        **kwargs,
    ) -> None:
        """Add every member with its score. A repeated member keeps the last score."""
        if not members:
            return
        serializer = resolve_serializer(self.serializer, kwargs)
        serialized = serializer.mserialize([member for member, _score in members])
        scores = (score for _member, score in members)
        await self.storage.madd(client, self.key, list(zip(serialized, scores, strict=True)))

    async def remove(
        self,
        client: ClientType,
        member: MemberType,
        **kwargs,
    ) -> None:
        """Remove ``member``. A missing member is not an error."""
        serializer = resolve_serializer(self.serializer, kwargs)
        await self.storage.remove(client, self.key, serializer.serialize(member))

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
        """Return whether ``member`` is in the ordered set."""
        serializer = resolve_serializer(self.serializer, kwargs)
        return await self.storage.contains(client, self.key, serializer.serialize(member))

    async def score(
        self,
        client: ClientType,
        member: MemberType,
        **kwargs,
    ) -> float | None:
        """Return the score of ``member``, or ``None`` when it is missing."""
        serializer = resolve_serializer(self.serializer, kwargs)
        return await self.storage.score(client, self.key, serializer.serialize(member))

    async def rank(
        self,
        client: ClientType,
        member: MemberType,
        **kwargs,
    ) -> int | None:
        """Return the 0-based ascending rank of ``member``, or ``None`` when it is missing."""
        serializer = resolve_serializer(self.serializer, kwargs)
        return await self.storage.rank(client, self.key, serializer.serialize(member))

    async def range(
        self,
        client: ClientType,
        start: int,
        stop: int,
        **kwargs,
    ) -> list[MemberType]:
        """Return members from ``start`` through ``stop``, both inclusive."""
        if _empty_range(start, stop):
            return []
        serializer = resolve_serializer(self.serializer, kwargs)
        raw = await self.storage.range(client, self.key, start, stop)
        return serializer.mdeserialize(raw)

    async def range_with_scores(
        self,
        client: ClientType,
        start: int,
        stop: int,
        **kwargs,
    ) -> list[tuple[MemberType, float]]:
        """Return members and scores from ``start`` through ``stop``, both inclusive."""
        if _empty_range(start, stop):
            return []
        serializer = resolve_serializer(self.serializer, kwargs)
        raw = await self.storage.range_with_scores(client, self.key, start, stop)
        members = serializer.mdeserialize([member for member, _score in raw])
        return list(zip(members, (score for _member, score in raw), strict=True))

    async def rev_rank(
        self,
        client: ClientType,
        member: MemberType,
        **kwargs,
    ) -> int | None:
        """Return the 0-based descending rank of ``member``, or ``None`` when it is missing."""
        serializer = resolve_serializer(self.serializer, kwargs)
        return await self.storage.rev_rank(client, self.key, serializer.serialize(member))

    async def rev_range(
        self,
        client: ClientType,
        start: int,
        stop: int,
        **kwargs,
    ) -> list[MemberType]:
        """Return members from ``start`` through ``stop``, both inclusive, highest score first."""
        if _empty_range(start, stop):
            return []
        serializer = resolve_serializer(self.serializer, kwargs)
        raw = await self.storage.rev_range(client, self.key, start, stop)
        return serializer.mdeserialize(raw)

    async def rev_range_with_scores(
        self,
        client: ClientType,
        start: int,
        stop: int,
        **kwargs,
    ) -> list[tuple[MemberType, float]]:
        """Return members and scores from ``start`` through ``stop``, highest score first."""
        if _empty_range(start, stop):
            return []
        serializer = resolve_serializer(self.serializer, kwargs)
        raw = await self.storage.rev_range_with_scores(client, self.key, start, stop)
        members = serializer.mdeserialize([member for member, _score in raw])
        return list(zip(members, (score for _member, score in raw), strict=True))

    async def swap(self, client: ClientType) -> Self:
        """Rename this index aside and return an unregistered index for that data."""
        return self.detach(await self.storage.swap(client, self.key))

    async def drop(self, client: ClientType) -> None:
        """Delete the key this index is bound to. A missing key is not an error."""
        await self.storage.drop(client, self.key)

    async def iter(
        self,
        client: ClientType,
        **kwargs,
    ) -> AsyncIterator[tuple[MemberType, float]]:
        """Yield each member and score under this index key, lowest score first."""
        serializer = resolve_serializer(self.serializer, kwargs)
        async for pair in async_scored(self.storage.iter(client, self.key), serializer):
            yield pair


async def async_scored[StorageType, ValueType](
    raw: AsyncIterable[tuple[StorageType, float]], serializer: Serializer[ValueType, StorageType]
) -> AsyncIterator[tuple[ValueType, float]]:
    """Yield deserialized members and their scores, one ``mdeserialize`` per batch."""
    batch: list[tuple[StorageType, float]] = []
    async for item in raw:
        batch.append(item)
        if len(batch) == BATCH:
            for decoded in _scored(batch, serializer):
                yield decoded
            batch = []
    if batch:
        for decoded in _scored(batch, serializer):
            yield decoded


def _scored[StorageType, ValueType](
    batch: list[tuple[StorageType, float]], serializer: Serializer[ValueType, StorageType]
) -> Iterator[tuple[ValueType, float]]:
    decoded = serializer.mdeserialize([member for member, _score in batch])
    return zip(decoded, (score for _member, score in batch), strict=True)
