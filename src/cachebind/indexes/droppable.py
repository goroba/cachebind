"""Index drop (delete bound storage key)."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class DroppableIndex[ClientType](Protocol):
    """Synchronous index that deletes the key it is bound to."""

    def drop(self, client: ClientType) -> None:
        """Delete the key this index is bound to. A missing key is not an error."""
        ...


@runtime_checkable
class AsyncDroppableIndex[ClientType](Protocol):
    """Asynchronous index that deletes the key it is bound to."""

    async def drop(self, client: ClientType) -> None:
        """Delete the key this index is bound to. A missing key is not an error."""
        ...