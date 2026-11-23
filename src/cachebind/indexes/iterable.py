"""Index iteration over stored entries."""

from collections.abc import AsyncIterator, Iterator
from typing import Protocol, runtime_checkable


@runtime_checkable
class IterableIndex[ClientType, ItemType](Protocol):
    """Synchronous index that yields stored entries under its key."""

    def iter(self, client: ClientType, **kwargs) -> Iterator[ItemType]:
        """Yield each entry stored under this index key."""
        ...


@runtime_checkable
class AsyncIterableIndex[ClientType, ItemType](Protocol):
    """Asynchronous index that yields stored entries under its key."""

    async def iter(self, client: ClientType, **kwargs) -> AsyncIterator[ItemType]:
        """Yield each entry stored under this index key."""
        ...