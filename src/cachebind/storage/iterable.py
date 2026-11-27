"""Iterate entries stored under one key."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Iterator


class IterableStorage[ClientType, ItemType](ABC):
    """Synchronous storage that scans every entry under ``name``."""

    @abstractmethod
    def iter(self, client: ClientType, name: str) -> Iterator[ItemType]:
        """Yield each entry stored under ``name``."""
        ...


class AsyncIterableStorage[ClientType, ItemType](ABC):
    """Asynchronous storage that scans every entry under ``name``."""

    @abstractmethod
    def iter(self, client: ClientType, name: str) -> AsyncIterator[ItemType]:
        """Yield each entry stored under ``name``."""
        ...