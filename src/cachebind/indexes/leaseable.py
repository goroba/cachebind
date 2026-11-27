"""Key-value index with lease-get."""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable


class LeasableKeyValueIndex[ClientType, IdType, ModelType](ABC):
    """Synchronous key-value index that can load through a fill lease on cache miss."""

    @abstractmethod
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


class AsyncLeasableKeyValueIndex[ClientType, IdType, ModelType](ABC):
    """Asynchronous key-value index that can load through a fill lease on cache miss."""

    @abstractmethod
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