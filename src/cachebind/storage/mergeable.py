"""Combine a staging key into a live storage name."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class MergeableStorage[ClientType](Protocol):
    """Synchronous storage that can merge ``source`` into ``dest``."""

    def merge(self, client: ClientType, source: str, dest: str) -> None:
        """Apply every entry in ``source`` onto ``dest``. Staging values win field conflicts."""
        ...


@runtime_checkable
class AsyncMergeableStorage[ClientType](Protocol):
    """Asynchronous storage that can merge ``source`` into ``dest``."""

    async def merge(self, client: ClientType, source: str, dest: str) -> None:
        """Apply every entry in ``source`` onto ``dest``. Staging values win field conflicts."""
        ...