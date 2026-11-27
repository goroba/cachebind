"""Combine a staging key into a live storage name."""



from abc import ABC, abstractmethod
class MergeableStorage[ClientType](ABC):
    """Synchronous storage that can merge ``source`` into ``dest``."""

    @abstractmethod
    def merge(self, client: ClientType, source: str, dest: str) -> None:
        """Apply every entry in ``source`` onto ``dest``. Staging values win field conflicts."""
        ...


class AsyncMergeableStorage[ClientType](ABC):
    """Asynchronous storage that can merge ``source`` into ``dest``."""

    @abstractmethod
    async def merge(self, client: ClientType, source: str, dest: str) -> None:
        """Apply every entry in ``source`` onto ``dest``. Staging values win field conflicts."""
        ...