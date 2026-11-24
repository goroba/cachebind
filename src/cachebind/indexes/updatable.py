"""Copy the live index, edit, and publish with replace semantics."""

from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class UpdatableIndex[ClientType](Protocol):
    """Synchronous index that copies live data into staging, then replaces on success."""

    def update(self, client: ClientType) -> AbstractContextManager[Self]:
        """Yield a staging copy of live data; replace live on success or drop staging on failure."""
        ...


@runtime_checkable
class AsyncUpdatableIndex[ClientType](Protocol):
    """Asynchronous index that copies live data into staging, then replaces on success."""

    def update(self, client: ClientType) -> AbstractAsyncContextManager[Self]:
        """Yield a staging copy of live data; replace live on success or drop staging on failure."""
        ...