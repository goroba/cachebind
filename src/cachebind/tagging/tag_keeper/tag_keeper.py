"""Tag keeper."""

from abc import ABC, abstractmethod


class TagKeeper[ClientType](ABC):
    """Group cache breadcrumbs in sets keyed by tag."""

    @abstractmethod
    def add(self, client: ClientType, tag: str, breadcrumb: str) -> None:
        """Add ``breadcrumb`` to the set for ``tag``."""
        ...

    @abstractmethod
    def madd(self, client: ClientType, tag: str, breadcrumbs: list[str]) -> None:
        """Add every breadcrumb to the set for ``tag``."""
        ...

    @abstractmethod
    def evict(self, client: ClientType, tag: str) -> None:
        """Evict every entry referenced by breadcrumbs in the set for ``tag``, then drop that set."""
        ...


class AsyncTagKeeper[ClientType](ABC):
    """Asynchronous tag keeper."""

    @abstractmethod
    async def add(self, client: ClientType, tag: str, breadcrumb: str) -> None:
        """Add ``breadcrumb`` to the set for ``tag``."""
        ...

    @abstractmethod
    async def madd(self, client: ClientType, tag: str, breadcrumbs: list[str]) -> None:
        """Add every breadcrumb to the set for ``tag``."""
        ...

    @abstractmethod
    async def evict(self, client: ClientType, tag: str) -> None:
        """Evict every entry referenced by breadcrumbs in the set for ``tag``, then drop that set."""
        ...
