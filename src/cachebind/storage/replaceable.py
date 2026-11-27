"""Publish a staging key onto a live storage name."""



from abc import ABC, abstractmethod
class ReplaceableStorage[ClientType](ABC):
    """Synchronous storage that can rename a staging key onto a live key."""

    @abstractmethod
    def replace(self, client: ClientType, source: str, dest: str) -> None:
        """Rename ``source`` onto ``dest``. ``dest`` is overwritten atomically."""
        ...


class AsyncReplaceableStorage[ClientType](ABC):
    """Asynchronous storage that can rename a staging key onto a live key."""

    @abstractmethod
    async def replace(self, client: ClientType, source: str, dest: str) -> None:
        """Rename ``source`` onto ``dest``. ``dest`` is overwritten atomically."""
        ...