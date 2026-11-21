"""Tag keeper protocol."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class TagKeeper[ClientType](Protocol):
    """Group cache breadcrumbs in sets keyed by tag."""

    def add(self, client: ClientType, tag: str, breadcrumb: str) -> None:
        """Add ``breadcrumb`` to the set for ``tag``."""
        ...

    def madd(self, client: ClientType, tag: str, breadcrumbs: list[str]) -> None:
        """Add every breadcrumb to the set for ``tag``."""
        ...

    def evict(self, client: ClientType, tag: str) -> None:
        """Evict every entry referenced by breadcrumbs in the set for ``tag``, then drop that set."""
        ...


@runtime_checkable
class AsyncTagKeeper[ClientType](Protocol):
    """Asynchronous tag keeper."""

    async def add(self, client: ClientType, tag: str, breadcrumb: str) -> None:
        """Add ``breadcrumb`` to the set for ``tag``."""
        ...

    async def madd(self, client: ClientType, tag: str, breadcrumbs: list[str]) -> None:
        """Add every breadcrumb to the set for ``tag``."""
        ...

    async def evict(self, client: ClientType, tag: str) -> None:
        """Evict every entry referenced by breadcrumbs in the set for ``tag``, then drop that set."""
        ...