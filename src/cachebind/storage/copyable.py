"""Clone one storage key onto another."""



from abc import ABC, abstractmethod
class CopyableStorage[ClientType](ABC):
    """Synchronous storage that can duplicate ``source`` onto ``dest``."""

    @abstractmethod
    def copy(self, client: ClientType, source: str, dest: str) -> None:
        """Duplicate ``source`` onto ``dest``. A missing ``source`` leaves ``dest`` absent."""
        ...


class AsyncCopyableStorage[ClientType](ABC):
    """Asynchronous storage that can duplicate ``source`` onto ``dest``."""

    @abstractmethod
    async def copy(self, client: ClientType, source: str, dest: str) -> None:
        """Duplicate ``source`` onto ``dest``. A missing ``source`` leaves ``dest`` absent."""
        ...