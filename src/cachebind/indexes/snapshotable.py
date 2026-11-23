"""Index snapshot for write-back and flush workflows."""

from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class SnapshotableIndex[ClientType](Protocol):
    """Synchronous index that renames storage aside for a flush workflow."""

    def snapshot(self, client: ClientType) -> AbstractContextManager[Self]:
        """Yield an unregistered index for the data that was live on enter; drop it on success."""
        ...


@runtime_checkable
class AsyncSnapshotableIndex[ClientType](Protocol):
    """Asynchronous index that renames storage aside for a flush workflow."""

    def snapshot(self, client: ClientType) -> AbstractAsyncContextManager[Self]:
        """Yield an unregistered index for the data that was live on enter; drop it on success."""
        ...