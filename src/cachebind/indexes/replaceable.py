"""Publish a detached staging index onto a registered live name."""

from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class ReplaceableIndex[ClientType](Protocol):
    """Synchronous index that can overwrite its live key from a staging build."""

    def replace(self, client: ClientType) -> AbstractContextManager[Self]:
        """Yield a detached staging index; publish it on success or drop it on failure."""
        ...


@runtime_checkable
class AsyncReplaceableIndex[ClientType](Protocol):
    """Asynchronous index that can overwrite its live key from a staging build."""

    def replace(self, client: ClientType) -> AbstractAsyncContextManager[Self]:
        """Yield a detached staging index; publish it on success or drop it on failure."""
        ...