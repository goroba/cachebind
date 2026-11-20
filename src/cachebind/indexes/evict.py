"""Index eviction by tag identifier."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class EvictableIndex[ClientType](Protocol):
    """Synchronous index that removes one entry by its tag identifier."""

    def evict(self, client: ClientType, identifier: str) -> None:
        """Remove the entry for ``identifier``. A missing entry is not an error."""
        ...


@runtime_checkable
class AsyncEvictableIndex[ClientType](Protocol):
    """Asynchronous index that removes one entry by its tag identifier."""

    async def evict(self, client: ClientType, identifier: str) -> None:
        """Remove the entry for ``identifier``. A missing entry is not an error."""
        ...