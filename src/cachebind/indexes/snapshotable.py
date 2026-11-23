"""Index snapshot for write-back and flush workflows."""

from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class SnapshotableIndex[ClientType](Protocol):
    """Synchronous index that renames storage aside and returns an unregistered copy."""

    def snapshot(self, client: ClientType) -> Self:
        """Rename this index aside and return an unregistered index for that data."""
        ...


@runtime_checkable
class AsyncSnapshotableIndex[ClientType](Protocol):
    """Asynchronous index that renames storage aside and returns an unregistered copy."""

    async def snapshot(self, client: ClientType) -> Self:
        """Rename this index aside and return an unregistered index for that data."""
        ...