"""Synchronous ordered-set index."""

from collections.abc import Hashable, Iterable, Iterator, Sequence
from typing import Self

from cachebind.indexes.ordered_sets.base import OrderedSetBase, _empty_range
from cachebind.serializers.serializer import Serializer
from cachebind.storage.ordered_sets.storage import OrderedSetStorage

BATCH = 100


class OrderedSetIndex[ClientType, MemberType, StorageType: Hashable](
    OrderedSetBase[ClientType, MemberType, StorageType]
):
    """Sync ordered-set index: member binding, storage key, and the storage that persists it.

    Writes serialize the member and pass the score through. Reads deserialize members.
    """

    storage: OrderedSetStorage[ClientType, StorageType]

    def add(self, client: ClientType, member: MemberType, score: float) -> None:
        """Add ``member`` with ``score``. A member that is already present gets the new score."""
        self.storage.add(client, self.key, self.serializer.serialize(member), score)

    def madd(self, client: ClientType, members: Sequence[tuple[MemberType, float]]) -> None:
        """Add every member with its score. A repeated member keeps the last score."""
        if not members:
            return
        serialized = self.serializer.mserialize([member for member, _score in members])
        scores = (score for _member, score in members)
        self.storage.madd(client, self.key, list(zip(serialized, scores, strict=True)))

    def remove(self, client: ClientType, member: MemberType) -> None:
        """Remove ``member``. A missing member is not an error."""
        self.storage.remove(client, self.key, self.serializer.serialize(member))

    def mremove(self, client: ClientType, members: Sequence[MemberType]) -> None:
        """Remove every member. Missing members are not an error."""
        if not members:
            return
        self.storage.mremove(client, self.key, self.serializer.mserialize(members))

    def contains(self, client: ClientType, member: MemberType) -> bool:
        """Return whether ``member`` is in the ordered set."""
        return self.storage.contains(client, self.key, self.serializer.serialize(member))

    def score(self, client: ClientType, member: MemberType) -> float | None:
        """Return the score of ``member``, or ``None`` when it is missing."""
        return self.storage.score(client, self.key, self.serializer.serialize(member))

    def rank(self, client: ClientType, member: MemberType) -> int | None:
        """Return the 0-based ascending rank of ``member``, or ``None`` when it is missing."""
        return self.storage.rank(client, self.key, self.serializer.serialize(member))

    def range(self, client: ClientType, start: int, stop: int) -> list[MemberType]:
        """Return members from ``start`` through ``stop``, both inclusive."""
        if _empty_range(start, stop):
            return []
        raw = self.storage.range(client, self.key, start, stop)
        return self.serializer.mdeserialize(raw)

    def range_with_scores(
        self, client: ClientType, start: int, stop: int
    ) -> list[tuple[MemberType, float]]:
        """Return members and scores from ``start`` through ``stop``, both inclusive."""
        if _empty_range(start, stop):
            return []
        raw = self.storage.range_with_scores(client, self.key, start, stop)
        members = self.serializer.mdeserialize([member for member, _score in raw])
        return list(zip(members, (score for _member, score in raw), strict=True))

    def rev_rank(self, client: ClientType, member: MemberType) -> int | None:
        """Return the 0-based descending rank of ``member``, or ``None`` when it is missing."""
        return self.storage.rev_rank(client, self.key, self.serializer.serialize(member))

    def rev_range(self, client: ClientType, start: int, stop: int) -> list[MemberType]:
        """Return members from ``start`` through ``stop``, both inclusive, highest score first."""
        if _empty_range(start, stop):
            return []
        raw = self.storage.rev_range(client, self.key, start, stop)
        return self.serializer.mdeserialize(raw)

    def rev_range_with_scores(
        self, client: ClientType, start: int, stop: int
    ) -> list[tuple[MemberType, float]]:
        """Return members and scores from ``start`` through ``stop``, highest score first."""
        if _empty_range(start, stop):
            return []
        raw = self.storage.rev_range_with_scores(client, self.key, start, stop)
        members = self.serializer.mdeserialize([member for member, _score in raw])
        return list(zip(members, (score for _member, score in raw), strict=True))

    def swap(self, client: ClientType) -> Self:
        """Rename this index aside and return an unregistered index for that data."""
        return self.detach(self.storage.swap(client, self.key))

    def drop(self, client: ClientType) -> None:
        """Delete the key this index is bound to. A missing key is not an error."""
        self.storage.drop(client, self.key)

    def iter(self, client: ClientType) -> Iterator[tuple[MemberType, float]]:
        """Yield each member and score under this index key, lowest score first."""
        return scored(self.storage.iter(client, self.key), self.serializer)


def scored[StorageType, ValueType](
    raw: Iterable[tuple[StorageType, float]], serializer: Serializer[ValueType, StorageType]
) -> Iterator[tuple[ValueType, float]]:
    """Yield deserialized members and their scores, one ``mdeserialize`` per batch."""
    batch: list[tuple[StorageType, float]] = []
    for item in raw:
        batch.append(item)
        if len(batch) == BATCH:
            yield from _scored(batch, serializer)
            batch = []
    if batch:
        yield from _scored(batch, serializer)


def _scored[StorageType, ValueType](
    batch: list[tuple[StorageType, float]], serializer: Serializer[ValueType, StorageType]
) -> Iterator[tuple[ValueType, float]]:
    decoded = serializer.mdeserialize([member for member, _score in batch])
    return zip(decoded, (score for _member, score in batch), strict=True)
