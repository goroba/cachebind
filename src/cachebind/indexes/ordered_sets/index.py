"""Synchronous ordered-set index."""

from collections.abc import Hashable, Iterable, Iterator, Sequence
from contextlib import contextmanager
from typing import Self, cast

from cachebind.indexes._replace import replace_context
from cachebind.indexes._serializer import resolve_serializer
from cachebind.indexes._breadcrumb import storage_identifier
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

    def add(
        self,
        client: ClientType,
        member: MemberType,
        score: float,
        **kwargs,
    ) -> str:
        """Add ``member`` with ``score``. A member that is already present gets the new score."""
        serializer = resolve_serializer(self.serializer, kwargs)
        stored = serializer.serialize(member)
        self.storage.add(client, self.key, stored, score)
        return self.breadcrumbs.encode(self.key, storage_identifier(stored))

    def madd(
        self,
        client: ClientType,
        members: Sequence[tuple[MemberType, float]],
        **kwargs,
    ) -> list[str]:
        """Add every member with its score. A repeated member keeps the last score."""
        if not members:
            return []
        serializer = resolve_serializer(self.serializer, kwargs)
        serialized = serializer.mserialize([member for member, _score in members])
        scores = (score for _member, score in members)
        self.storage.madd(client, self.key, list(zip(serialized, scores, strict=True)))
        return [
            self.breadcrumbs.encode(self.key, storage_identifier(value)) for value in serialized
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
        """Return whether ``member`` is in the ordered set."""
        serializer = resolve_serializer(self.serializer, kwargs)
        return self.storage.contains(client, self.key, serializer.serialize(member))

    def score(
        self,
        client: ClientType,
        member: MemberType,
        **kwargs,
    ) -> float | None:
        """Return the score of ``member``, or ``None`` when it is missing."""
        serializer = resolve_serializer(self.serializer, kwargs)
        return self.storage.score(client, self.key, serializer.serialize(member))

    def rank(
        self,
        client: ClientType,
        member: MemberType,
        **kwargs,
    ) -> int | None:
        """Return the 0-based ascending rank of ``member``, or ``None`` when it is missing."""
        serializer = resolve_serializer(self.serializer, kwargs)
        return self.storage.rank(client, self.key, serializer.serialize(member))

    def range(
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
        raw = self.storage.range(client, self.key, start, stop)
        return serializer.mdeserialize(raw)

    def range_with_scores(
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
        raw = self.storage.range_with_scores(client, self.key, start, stop)
        members = serializer.mdeserialize([member for member, _score in raw])
        return list(zip(members, (score for _member, score in raw), strict=True))

    def rev_rank(
        self,
        client: ClientType,
        member: MemberType,
        **kwargs,
    ) -> int | None:
        """Return the 0-based descending rank of ``member``, or ``None`` when it is missing."""
        serializer = resolve_serializer(self.serializer, kwargs)
        return self.storage.rev_rank(client, self.key, serializer.serialize(member))

    def rev_range(
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
        raw = self.storage.rev_range(client, self.key, start, stop)
        return serializer.mdeserialize(raw)

    def rev_range_with_scores(
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
        raw = self.storage.rev_range_with_scores(client, self.key, start, stop)
        members = serializer.mdeserialize([member for member, _score in raw])
        return list(zip(members, (score for _member, score in raw), strict=True))

    def snapshot(self, client: ClientType) -> Self:
        """Rename this index aside and return an unregistered index for that data."""
        return self.detach(self.storage.snapshot(client, self.key))

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
    ) -> Iterator[tuple[MemberType, float]]:
        """Yield each member and score under this index key, lowest score first."""
        serializer = resolve_serializer(self.serializer, kwargs)
        return scored(self.storage.iter(client, self.key), serializer)


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
