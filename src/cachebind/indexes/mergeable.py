"""Combine a detached staging index into a registered live name."""

from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class MergeableIndex[ClientType](Protocol):
    """Synchronous index that can merge a staging build into its live key."""

    def merge(self, client: ClientType) -> AbstractContextManager[Self]:
        """Yield a detached staging index; merge it into live on success or drop it on failure."""
        ...


@runtime_checkable
class AsyncMergeableIndex[ClientType](Protocol):
    """Asynchronous index that can merge a staging build into its live key."""

    def merge(self, client: ClientType) -> AbstractAsyncContextManager[Self]:
        """Yield a detached staging index; merge it into live on success or drop it on failure."""
        ...