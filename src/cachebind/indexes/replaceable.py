"""Publish a detached staging index onto a registered live name."""

from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import Self


class ReplaceableIndex[ClientType](ABC):
    """Synchronous index that can overwrite its live key from a staging build."""

    @abstractmethod
    def replace(self, client: ClientType) -> AbstractContextManager[Self]:
        """Yield a detached staging index; publish it on success or drop it on failure."""
        ...


class AsyncReplaceableIndex[ClientType](ABC):
    """Asynchronous index that can overwrite its live key from a staging build."""

    @abstractmethod
    def replace(self, client: ClientType) -> AbstractAsyncContextManager[Self]:
        """Yield a detached staging index; publish it on success or drop it on failure."""
        ...