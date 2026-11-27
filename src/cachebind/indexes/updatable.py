"""Copy the live index, edit, and publish with replace semantics."""

from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import Self


class UpdatableIndex[ClientType](ABC):
    """Synchronous index that copies live data into staging, then replaces on success."""

    @abstractmethod
    def update(self, client: ClientType) -> AbstractContextManager[Self]:
        """Yield a staging copy of live data; replace live on success or drop staging on failure."""
        ...


class AsyncUpdatableIndex[ClientType](ABC):
    """Asynchronous index that copies live data into staging, then replaces on success."""

    @abstractmethod
    def update(self, client: ClientType) -> AbstractAsyncContextManager[Self]:
        """Yield a staging copy of live data; replace live on success or drop staging on failure."""
        ...