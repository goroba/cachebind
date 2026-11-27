"""Index drop (delete bound storage key)."""



from abc import ABC, abstractmethod
class DroppableIndex[ClientType](ABC):
    """Synchronous index that deletes the key it is bound to."""

    @abstractmethod
    def drop(self, client: ClientType) -> None:
        """Delete the key this index is bound to. A missing key is not an error."""
        ...


class AsyncDroppableIndex[ClientType](ABC):
    """Asynchronous index that deletes the key it is bound to."""

    @abstractmethod
    async def drop(self, client: ClientType) -> None:
        """Delete the key this index is bound to. A missing key is not an error."""
        ...