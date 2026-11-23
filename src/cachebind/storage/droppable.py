"""Delete a bound storage key."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class DroppableStorage[ClientType](Protocol):
    """Synchronous storage that deletes the key named ``name``."""

    def drop(self, client: ClientType, name: str) -> None:
        """Delete ``name``. A missing name is not an error."""
        ...


@runtime_checkable
class AsyncDroppableStorage[ClientType](Protocol):
    """Asynchronous storage that deletes the key named ``name``."""

    async def drop(self, client: ClientType, name: str) -> None:
        """Delete ``name``. A missing name is not an error."""
        ...