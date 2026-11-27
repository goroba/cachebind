"""Index eviction by tag identifier."""



from abc import ABC, abstractmethod
class EvictableIndex[ClientType](ABC):
    """Synchronous index that removes one entry by its tag identifier."""

    @abstractmethod
    def evict(self, client: ClientType, identifier: str) -> None:
        """Remove the entry for ``identifier``. A missing entry is not an error."""
        ...


class AsyncEvictableIndex[ClientType](ABC):
    """Asynchronous index that removes one entry by its tag identifier."""

    @abstractmethod
    async def evict(self, client: ClientType, identifier: str) -> None:
        """Remove the entry for ``identifier``. A missing entry is not an error."""
        ...