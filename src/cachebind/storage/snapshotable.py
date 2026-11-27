"""Rename storage aside for snapshot and replace workflows."""



from abc import ABC, abstractmethod
class SnapshotableStorage[ClientType](ABC):
    """Synchronous storage that treats ``name`` as one renameable key."""

    @abstractmethod
    def snapshot(self, client: ClientType, name: str) -> str:
        """Rename ``name`` aside and return the new name. A missing name still returns one."""
        ...


class AsyncSnapshotableStorage[ClientType](ABC):
    """Asynchronous storage that treats ``name`` as one renameable key."""

    @abstractmethod
    async def snapshot(self, client: ClientType, name: str) -> str:
        """Rename ``name`` aside and return the new name. A missing name still returns one."""
        ...