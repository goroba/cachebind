"""Key-value index with lease-get."""

from collections.abc import Awaitable, Callable
from typing import Protocol, runtime_checkable


@runtime_checkable
class LeasableKeyValueIndex[ClientType, IdType, ModelType](Protocol):
    """Synchronous key-value index that can load through a fill lease on cache miss."""

    def lease_get(
        self,
        client: ClientType,
        id: IdType,
        callback: Callable[[], ModelType],
        *,
        lease_ttl: int,
        ttl: int | None = None,
        **kwargs,
    ) -> ModelType | None:
        """Return the cached model, or run ``callback`` under a fill lease when the id is missing."""
        ...


@runtime_checkable
class AsyncLeasableKeyValueIndex[ClientType, IdType, ModelType](Protocol):
    """Asynchronous key-value index that can load through a fill lease on cache miss."""

    async def lease_get(
        self,
        client: ClientType,
        id: IdType,
        callback: Callable[[], Awaitable[ModelType]],
        *,
        lease_ttl: int,
        ttl: int | None = None,
        **kwargs,
    ) -> ModelType | None:
        """Return the cached model, or run ``callback`` under a fill lease when the id is missing."""
        ...