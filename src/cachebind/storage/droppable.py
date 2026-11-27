"""Delete a bound storage key."""



from abc import ABC, abstractmethod
class DroppableStorage[ClientType](ABC):
    """Synchronous storage that deletes the key named ``name``."""

    @abstractmethod
    def drop(self, client: ClientType, name: str) -> None:
        """Delete ``name``. A missing name is not an error."""
        ...


class AsyncDroppableStorage[ClientType](ABC):
    """Asynchronous storage that deletes the key named ``name``."""

    @abstractmethod
    async def drop(self, client: ClientType, name: str) -> None:
        """Delete ``name``. A missing name is not an error."""
        ...