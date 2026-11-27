"""Asynchronous set storage."""

from abc import ABC, abstractmethod
from collections.abc import Hashable, Sequence


class AsyncSetStorage[ClientType, MemberType: Hashable](ABC):
    """Asynchronous set storage.

    ``client`` is the storage client for that call.
    ``name`` is the set name. ``member`` is one element of that set.
    Adding a member that is already present is not an error.
    Removing a missing member is not an error.
    """

    @abstractmethod
    async def add(self, client: ClientType, name: str, member: MemberType) -> None:
        """Add ``member`` to the set."""
        ...

    @abstractmethod
    async def madd(self, client: ClientType, name: str, members: Sequence[MemberType]) -> None:
        """Add every member."""
        ...

    @abstractmethod
    async def remove(self, client: ClientType, name: str, member: MemberType) -> None:
        """Remove ``member``. A missing member is not an error."""
        ...

    @abstractmethod
    async def mremove(self, client: ClientType, name: str, members: Sequence[MemberType]) -> None:
        """Remove every member. Missing members are not an error."""
        ...

    @abstractmethod
    async def contains(self, client: ClientType, name: str, member: MemberType) -> bool:
        """Return whether ``member`` is in the set."""
        ...