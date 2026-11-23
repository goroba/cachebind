"""Rename storage aside for snapshot and replace workflows."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class SnapshotableStorage[ClientType](Protocol):
    """Synchronous storage that treats ``name`` as one renameable key."""

    def snapshot(self, client: ClientType, name: str) -> str:
        """Rename ``name`` aside and return the new name. A missing name still returns one."""
        ...


@runtime_checkable
class AsyncSnapshotableStorage[ClientType](Protocol):
    """Asynchronous storage that treats ``name`` as one renameable key."""

    async def snapshot(self, client: ClientType, name: str) -> str:
        """Rename ``name`` aside and return the new name. A missing name still returns one."""
        ...