"""Iterate entries stored under one key."""

from collections.abc import AsyncIterator, Iterator
from typing import Protocol, runtime_checkable


@runtime_checkable
class IterableStorage[ClientType, ItemType](Protocol):
    """Synchronous storage that scans every entry under ``name``."""

    def iter(self, client: ClientType, name: str) -> Iterator[ItemType]:
        """Yield each entry stored under ``name``."""
        ...


@runtime_checkable
class AsyncIterableStorage[ClientType, ItemType](Protocol):
    """Asynchronous storage that scans every entry under ``name``."""

    def iter(self, client: ClientType, name: str) -> AsyncIterator[ItemType]:
        """Yield each entry stored under ``name``."""
        ...