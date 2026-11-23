"""Asynchronous ordered-set storage."""

from collections.abc import AsyncIterator, Hashable, Sequence
from typing import Protocol, runtime_checkable


@runtime_checkable
class AsyncOrderedSetStorage[ClientType, MemberType: Hashable](Protocol):
    """Asynchronous ordered-set storage.

    ``client`` is the storage client for that call.
    ``name`` is the ordered set name. ``member`` is one element of that set.
    Each member has one score. Adding a member that is already present updates its score.
    Removing a missing member is not an error.
    ``rank`` is 0-based and ascending. ``rev_rank`` is 0-based and descending.
    A range includes ``start`` and ``stop``.
    A storage that cannot treat ``name`` as one key raises ``NotImplementedError``
    from ``swap``, ``drop``, and ``iter``.
    """

    async def add(self, client: ClientType, name: str, member: MemberType, score: float) -> None:
        """Add ``member`` with ``score``. A member that is already present gets the new score."""
        ...

    async def madd(
        self, client: ClientType, name: str, members: Sequence[tuple[MemberType, float]]
    ) -> None:
        """Add every member with its score. A repeated member keeps the last score."""
        ...

    async def remove(self, client: ClientType, name: str, member: MemberType) -> None:
        """Remove ``member``. A missing member is not an error."""
        ...

    async def mremove(self, client: ClientType, name: str, members: Sequence[MemberType]) -> None:
        """Remove every member. Missing members are not an error."""
        ...

    async def contains(self, client: ClientType, name: str, member: MemberType) -> bool:
        """Return whether ``member`` is in the ordered set."""
        ...

    async def score(self, client: ClientType, name: str, member: MemberType) -> float | None:
        """Return the score of ``member``, or ``None`` when it is missing."""
        ...

    async def rank(self, client: ClientType, name: str, member: MemberType) -> int | None:
        """Return the 0-based ascending rank of ``member``, or ``None`` when it is missing."""
        ...

    async def range(
        self, client: ClientType, name: str, start: int, stop: int
    ) -> list[MemberType]:
        """Return members from ``start`` through ``stop``, both inclusive."""
        ...

    async def range_with_scores(
        self, client: ClientType, name: str, start: int, stop: int
    ) -> list[tuple[MemberType, float]]:
        """Return members and scores from ``start`` through ``stop``, both inclusive."""
        ...

    async def rev_rank(self, client: ClientType, name: str, member: MemberType) -> int | None:
        """Return the 0-based descending rank of ``member``, or ``None`` when it is missing."""
        ...

    async def rev_range(
        self, client: ClientType, name: str, start: int, stop: int
    ) -> list[MemberType]:
        """Return members from ``start`` through ``stop``, both inclusive, highest score first."""
        ...

    async def rev_range_with_scores(
        self, client: ClientType, name: str, start: int, stop: int
    ) -> list[tuple[MemberType, float]]:
        """Return members and scores from ``start`` through ``stop``, highest score first."""
        ...

    async def swap(self, client: ClientType, name: str) -> str:
        """Rename ``name`` aside and return the new name. A missing name still returns one."""
        ...

    async def replace(self, client: ClientType, source: str, dest: str) -> None:
        """Rename ``source`` onto ``dest``. ``dest`` is overwritten atomically."""
        ...

    async def drop(self, client: ClientType, name: str) -> None:
        """Delete ``name``. A missing name is not an error."""
        ...

    def iter(self, client: ClientType, name: str) -> AsyncIterator[tuple[MemberType, float]]:
        """Yield every member and score stored under ``name``, lowest score first."""
        ...
