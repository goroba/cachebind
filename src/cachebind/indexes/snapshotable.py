"""Index snapshot for write-back and flush workflows."""

from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import Self


class SnapshotableIndex[ClientType](ABC):
    """Synchronous index that renames storage aside for a flush workflow."""

    @abstractmethod
    def snapshot(self, client: ClientType) -> AbstractContextManager[Self]:
        """Yield an unregistered index for the data that was live on enter; drop it on success."""
        ...


class AsyncSnapshotableIndex[ClientType](ABC):
    """Asynchronous index that renames storage aside for a flush workflow."""

    @abstractmethod
    def snapshot(self, client: ClientType) -> AbstractAsyncContextManager[Self]:
        """Yield an unregistered index for the data that was live on enter; drop it on success."""
        ...