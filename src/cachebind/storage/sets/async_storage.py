"""Asynchronous set storage."""

from collections.abc import AsyncIterator, Hashable, Sequence
from typing import Protocol, runtime_checkable


@runtime_checkable
class AsyncSetStorage[ClientType, MemberType: Hashable](Protocol):
    """Asynchronous set storage.

    ``client`` is the storage client for that call.
    ``name`` is the set name. ``member`` is one element of that set.
    Adding a member that is already present is not an error.
    Removing a missing member is not an error.
    A storage that cannot treat ``name`` as one key raises ``NotImplementedError``
    from ``swap``, ``drop``, and ``iter``.
    """

    async def add(self, client: ClientType, name: str, member: MemberType) -> None:
        """Add ``member`` to the set."""
        ...

    async def madd(self, client: ClientType, name: str, members: Sequence[MemberType]) -> None:
        """Add every member."""
        ...

    async def remove(self, client: ClientType, name: str, member: MemberType) -> None:
        """Remove ``member``. A missing member is not an error."""
        ...

    async def mremove(self, client: ClientType, name: str, members: Sequence[MemberType]) -> None:
        """Remove every member. Missing members are not an error."""
        ...

    async def contains(self, client: ClientType, name: str, member: MemberType) -> bool:
        """Return whether ``member`` is in the set."""
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

    def iter(self, client: ClientType, name: str) -> AsyncIterator[MemberType]:
        """Yield every member stored under ``name``."""
        ...
