"""Clone one storage key onto another."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class CopyableStorage[ClientType](Protocol):
    """Synchronous storage that can duplicate ``source`` onto ``dest``."""

    def copy(self, client: ClientType, source: str, dest: str) -> None:
        """Duplicate ``source`` onto ``dest``. A missing ``source`` leaves ``dest`` absent."""
        ...


@runtime_checkable
class AsyncCopyableStorage[ClientType](Protocol):
    """Asynchronous storage that can duplicate ``source`` onto ``dest``."""

    async def copy(self, client: ClientType, source: str, dest: str) -> None:
        """Duplicate ``source`` onto ``dest``. A missing ``source`` leaves ``dest`` absent."""
        ...