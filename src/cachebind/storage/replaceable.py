"""Publish a staging key onto a live storage name."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class ReplaceableStorage[ClientType](Protocol):
    """Synchronous storage that can rename a staging key onto a live key."""

    def replace(self, client: ClientType, source: str, dest: str) -> None:
        """Rename ``source`` onto ``dest``. ``dest`` is overwritten atomically."""
        ...


@runtime_checkable
class AsyncReplaceableStorage[ClientType](Protocol):
    """Asynchronous storage that can rename a staging key onto a live key."""

    async def replace(self, client: ClientType, source: str, dest: str) -> None:
        """Rename ``source`` onto ``dest``. ``dest`` is overwritten atomically."""
        ...