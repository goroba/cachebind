"""Combine a detached staging index into a registered live name."""

from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import Self


class MergeableIndex[ClientType](ABC):
    """Synchronous index that can merge a staging build into its live key."""

    @abstractmethod
    def merge(self, client: ClientType) -> AbstractContextManager[Self]:
        """Yield a detached staging index; merge it into live on success or drop it on failure."""
        ...


class AsyncMergeableIndex[ClientType](ABC):
    """Asynchronous index that can merge a staging build into its live key."""

    @abstractmethod
    def merge(self, client: ClientType) -> AbstractAsyncContextManager[Self]:
        """Yield a detached staging index; merge it into live on success or drop it on failure."""
        ...