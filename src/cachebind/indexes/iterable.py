"""Index iteration over stored entries."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Iterator


class IterableIndex[ClientType, ItemType](ABC):
    """Synchronous index that yields stored entries under its key."""

    @abstractmethod
    def iter(self, client: ClientType, **kwargs) -> Iterator[ItemType]:
        """Yield each entry stored under this index key."""
        ...


class AsyncIterableIndex[ClientType, ItemType](ABC):
    """Asynchronous index that yields stored entries under its key."""

    @abstractmethod
    async def iter(self, client: ClientType, **kwargs) -> AsyncIterator[ItemType]:
        """Yield each entry stored under this index key."""
        ...